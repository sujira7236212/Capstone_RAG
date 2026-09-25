"""Cross-encoder relevance scores for test_rag_compare.py's --rerank gate (ablation R6).

BAAI/bge-reranker-v2-m3 (XLMRobertaForSequenceClassification) through transformers, run locally: free,
deterministic, and independent of eval/build_relevance_pool.py's judge (gemini-3.8-flash) -
a Gemini reranker would be graded by its own family. Runs on CUDA when torch sees a GPU
(needs a CUDA build of torch, e.g. `pip install "torch==2.13.0+cu126" --index-url
https://download.pytorch.org/whl/cu126`), otherwise CPU.

The published weights are fp32 (2.27 GB). On the 6 GB development machine loading them
fails outright - safetensors maps the file copy-on-write, which Windows charges in full
against the commit limit ("paging file is too small", os error 1455). So the first call
writes an fp16 copy (1.1 GB) to .cache/models/, converting tensor by tensor from plain
file reads, and the model is always loaded from that copy in fp16 - also by plain reads
(_read_tensors), since with CUDA's DLLs loaded even the 1.1 GB copy-on-write map does not fit.

Scores are sigmoid(logit) in 0..1; 0.5 is the model's own relevant / not-relevant boundary.
Every (query, chunk) score is cached on disk under .cache/rerank/ keyed by model, query and
chunk text, so re-running the eval or a comparison only scores pairs it has not seen.
"""
import hashlib
import json
import math
import os

MODEL = "BAAI/bge-reranker-v2-m3"
MAX_LENGTH = 512
BATCH_SIZE = 16
_CACHE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
CACHE_PATH = os.path.join(_CACHE_ROOT, "rerank", MODEL.replace("/", "__") + ".json")
FP16_DIR = os.path.join(_CACHE_ROOT, "models", MODEL.replace("/", "__") + "-fp16")
_CHUNK_BYTES = 64 << 20

_model = None
_cache = None


def _key(query, text):
    return hashlib.md5(f"{query}\x00{text}".encode("utf-8")).hexdigest()


def _load_cache():
    global _cache
    if _cache is None:
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_cache, f)
    os.replace(tmp, CACHE_PATH)


def _convert_to_fp16(src, dst):
    """Rewrite a safetensors file with every F32 tensor as F16, streaming through plain
    reads (no mmap) so peak memory is one _CHUNK_BYTES chunk, not the whole model."""
    import numpy as np
    with open(src, "rb") as f:
        n = int.from_bytes(f.read(8), "little")
        header = json.loads(f.read(n))
        data_start = 8 + n
        names = sorted((k for k in header if k != "__metadata__"), key=lambda k: header[k]["data_offsets"][0])
        out_header, offset = {}, 0
        if "__metadata__" in header:
            out_header["__metadata__"] = header["__metadata__"]
        for k in names:
            t = header[k]
            size = t["data_offsets"][1] - t["data_offsets"][0]
            dtype = t["dtype"]
            if dtype == "F32":
                dtype, size = "F16", size // 2
            out_header[k] = {"dtype": dtype, "shape": t["shape"], "data_offsets": [offset, offset + size]}
            offset += size
        blob = json.dumps(out_header, separators=(",", ":")).encode("utf-8")
        blob += b" " * (-len(blob) % 8)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as out:
            out.write(len(blob).to_bytes(8, "little"))
            out.write(blob)
            for k in names:
                start, end = header[k]["data_offsets"]
                f.seek(data_start + start)
                left = end - start
                while left:
                    buf = f.read(min(left, _CHUNK_BYTES))
                    left -= len(buf)
                    if header[k]["dtype"] == "F32":
                        buf = np.frombuffer(buf, dtype="<f4").astype("<f2").tobytes()
                    out.write(buf)
    os.replace(tmp, dst)


def _fp16_dir():
    weights = os.path.join(FP16_DIR, "model.safetensors")
    if not os.path.exists(weights):
        import shutil
        from huggingface_hub import snapshot_download
        snap = snapshot_download(MODEL, allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"])
        os.makedirs(FP16_DIR, exist_ok=True)
        for name in os.listdir(snap):
            if name == "config.json":
                with open(os.path.join(snap, name), encoding="utf-8") as f:
                    cfg = json.load(f)
                cfg["torch_dtype"] = "float16"
                with open(os.path.join(FP16_DIR, name), "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
            elif name != "model.safetensors":
                shutil.copyfile(os.path.join(snap, name), os.path.join(FP16_DIR, name))
        _convert_to_fp16(os.path.join(snap, "model.safetensors"), weights)
    return FP16_DIR


def _read_tensors(path, device):
    """{name: tensor on `device`} from a safetensors file via plain reads - no mmap. Each
    tensor is allocated on `device` first and filled through one reused _CHUNK_BYTES host
    buffer, so host memory never holds more than that chunk (the 250k x 1024 embedding
    alone is 512 MB)."""
    import torch
    dtypes = {"F16": torch.float16, "F32": torch.float32, "I64": torch.int64}
    chunk = bytearray(_CHUNK_BYTES)
    out = {}
    with open(path, "rb") as f:
        n = int.from_bytes(f.read(8), "little")
        header = json.loads(f.read(n))
        for name, t in header.items():
            if name == "__metadata__":
                continue
            dtype = dtypes[t["dtype"]]
            item = torch.empty((), dtype=dtype).element_size()
            start, end = t["data_offsets"]
            flat = torch.empty((end - start) // item, dtype=dtype, device=device)
            f.seek(8 + n + start)
            done = 0
            while done < end - start:
                got = f.readinto(memoryview(chunk)[:min(_CHUNK_BYTES, end - start - done)])
                flat[done // item:(done + got) // item].copy_(torch.frombuffer(chunk, dtype=dtype, count=got // item))
                done += got
            out[name] = flat.view(t["shape"])
    return out


def _get_model():
    """(tokenizer, model, device). Built on the meta device and filled straight from the fp16
    file on the target device (see _read_tensors); transformers' own loader maps the file."""
    global _model
    if _model is None:
        import torch
        from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
        path = _fp16_dir()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        with torch.device("meta"):
            model = AutoModelForSequenceClassification.from_config(
                AutoConfig.from_pretrained(path), dtype=torch.float16)
        missing, unexpected = model.load_state_dict(
            _read_tensors(os.path.join(path, "model.safetensors"), device), strict=False, assign=True)
        # Non-persistent buffers are not in the checkpoint and are still on meta: the
        # embeddings' position_ids (arange) and default token_type_ids (zeros).
        for mod in model.modules():
            for bname, buf in list(mod._buffers.items()):
                if buf is None or not buf.is_meta:
                    continue
                if bname == "position_ids":
                    mod._buffers[bname] = torch.arange(buf.shape[-1], device=device).expand(buf.shape).clone()
                elif bname == "token_type_ids":
                    mod._buffers[bname] = torch.zeros(buf.shape, dtype=buf.dtype, device=device)
                else:
                    raise RuntimeError(f"uninitialised buffer {bname} in {type(mod).__name__}")
        still_meta = [n for n, p in model.named_parameters() if p.is_meta]
        if still_meta or unexpected:
            raise RuntimeError(f"checkpoint mismatch: missing {still_meta}, unexpected {unexpected}")
        model.eval()
        _model = (AutoTokenizer.from_pretrained(path), model, device)
    return _model


def _predict(pairs):
    import torch
    tok, model, device = _get_model()
    logits = []
    with torch.inference_mode():
        for i in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[i:i + BATCH_SIZE]
            enc = tok([q for q, _ in batch], [t for _, t in batch], padding=True, truncation=True,
                      max_length=MAX_LENGTH, return_tensors="pt").to(device)
            logits.extend(model(**enc).logits.view(-1).float().tolist())
    return logits


def scores(pairs):
    """[(query, text)] -> [sigmoid(logit)], computing only the pairs missing from the cache."""
    cache = _load_cache()
    todo = sorted({(q, t) for q, t in pairs if _key(q, t) not in cache})
    if todo:
        logits = _predict(todo)
        for (q, t), z in zip(todo, logits):
            cache[_key(q, t)] = float(z)
        _save_cache()
    return [1.0 / (1.0 + math.exp(-cache[_key(q, t)])) for q, t in pairs]


def max_scores(queries, texts):
    """Best score of each text over all queries."""
    flat = scores([(q, t) for t in texts for q in queries])
    n = len(queries)
    return [max(flat[i * n:(i + 1) * n]) for i in range(len(texts))]
