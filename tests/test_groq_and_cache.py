"""rag_core.generate's Groq path against a local stand-in server, and rag_core.query_cache.
No network, no API key, no paid call.

    python tests/test_groq_and_cache.py
"""
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rag_core import generate  # noqa: E402
from rag_core.query_cache import CachedEmbeddings  # noqa: E402

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


# --- the query cache ----------------------------------------------------------------

class Inner:
    model = "models/fake-embedding"

    def __init__(self):
        self.calls = []

    def embed_query(self, text):
        self.calls.append(text)
        return [float(len(text)), 1.0]


with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "q.json")
    inner = Inner()
    cache = CachedEmbeddings(inner, path=path)
    check("cache: miss calls the model", (cache.embed_query("knees in"), inner.calls), ([8.0, 1.0], ["knees in"]))
    check("cache: hit does not", (cache.embed_query("knees in"), len(inner.calls)), ([8.0, 1.0], 1))
    check("cache: written to disk", json.load(open(path, encoding="utf-8")), {"knees in": [8.0, 1.0]})
    again = CachedEmbeddings(Inner(), path=path)
    check("cache: read back on start", ("knees in" in again, again.embed_query("knees in"), again.inner.calls),
          (True, [8.0, 1.0], []))
    check("cache: default path is per model", CachedEmbeddings(Inner()).path.endswith("models__fake-embedding.json"), True)


# --- Groq ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    replies = []
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        Handler.seen.append({"body": body, "auth": self.headers.get("authorization")})
        status, headers, payload = Handler.replies.pop(0)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
generate.GROQ_URL = f"http://127.0.0.1:{server.server_port}/chat/completions"
os.environ["GROQ_API_KEY"] = "test-groq-key"

chain = generate.build_chain("CONTEXT-TEXT", "qwen/test", timeout=5, provider="groq")
Handler.replies.append((200, {}, {"choices": [{"message": {"content": "<think>plan the answer</think>\n\nPush your knees out."}}]}))
check("groq: answer without the reasoning", chain.invoke('{"summary": {}}'), "Push your knees out.")
sent = Handler.seen[-1]
check("groq: bearer key", sent["auth"], "Bearer test-groq-key")
check("groq: model and temperature", (sent["body"]["model"], sent["body"]["temperature"]), ("qwen/test", generate.LLM_TEMPERATURE))
check("groq: system then user", [m["role"] for m in sent["body"]["messages"]], ["system", "user"])
check("groq: context in the system prompt", "CONTEXT-TEXT" in sent["body"]["messages"][0]["content"], True)
check("groq: session in the user turn", '{"summary": {}}' in sent["body"]["messages"][1]["content"], True)

Handler.replies.append((429, {"retry-after": "7"}, {"error": {"message": "Rate limit reached"}}))
try:
    chain.invoke("{}")
    check("groq 429: raises", False, True)
except generate.GroqError as e:
    check("groq 429: retry_after and the status in the text", (e.retry_after, "429" in str(e)), (7.0, True))

del os.environ["GROQ_API_KEY"]
try:
    chain.invoke("{}")
    check("groq without a key: raises", False, True)
except generate.GroqError as e:
    check("groq without a key: says so", str(e), "GROQ_API_KEY is not set")

try:
    generate.build_chain("c", "m", provider="other")
    check("unknown provider: raises", False, True)
except ValueError:
    pass

server.shutdown()
print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
