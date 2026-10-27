"""One feedback answer from a context and a session payload.

Moved out of test_rag_compare.py (2026-10-25, docs/plans/app_integration_plan.md A1). No
retry or rate-limit policy here: the batch scripts sleep between calls, the service must
not, so each caller wraps generate() in its own.

Two providers (2026-10-27): "gemini", what every eval run and the plan's D5 use, and "groq",
a free model for trying the app integration out while it costs nothing, until the switch
back to Gemini. Groq is called over its OpenAI-compatible HTTP endpoint with the standard
library, as eval/generate_groq.py does, so the service needs no extra package for it.
"""
import json
import os
import re
import urllib.error
import urllib.request

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from rag_core.prompt import HUMAN_TEMPLATE, SYSTEM_PROMPT, model_payload

LLM_TEMPERATURE = 0.7

# Marker a batch script writes in place of an answer whose call failed.
GENERATION_ERROR = "Error occurred during generation"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Qwen writes its reasoning inline before the answer; it is never part of the feedback.
_THINK = re.compile(r"<think>.*?</think>\s*", re.S)
_ROLES = {"system": "system", "human": "user", "ai": "assistant"}


class GroqError(RuntimeError):
    """A failed Groq call. `retry_after` (seconds) is set from the 429 answer's header, so the
    service can wait exactly that long when its budget allows."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


def _groq_complete(prompt_value, model, temperature, timeout):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise GroqError("GROQ_API_KEY is not set")
    body = {"model": model, "temperature": temperature,
            "messages": [{"role": _ROLES[m.type], "content": m.content} for m in prompt_value.to_messages()]}
    req = urllib.request.Request(GROQ_URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}",
                                          "User-Agent": "rag-feedback-service/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        retry_after = e.headers.get("retry-after")
        raise GroqError(f"Groq HTTP {e.code}: {detail}",
                        retry_after=float(retry_after) if retry_after else None) from None
    return _THINK.sub("", data["choices"][0]["message"]["content"] or "").strip()


def build_chain(context, model, temperature=LLM_TEMPERATURE, max_retries=1, timeout=None,
                thinking_level=None, provider="gemini"):
    """`max_retries` is the client's total number of attempts (1 = no retry). `thinking_level`
    ("minimal"/"low"/"medium"/"high", Gemini 3+): None keeps the model's own default, which
    is what every eval run so far used. Groq takes neither: one attempt, the model's own
    reasoning."""
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", HUMAN_TEMPLATE)])
    inputs = {"context": lambda x: context, "input": RunnablePassthrough()}
    if provider == "groq":
        return inputs | prompt | RunnableLambda(lambda pv: _groq_complete(pv, model, temperature, timeout))
    if provider != "gemini":
        raise ValueError(f"unknown LLM provider {provider!r}, want 'gemini' or 'groq'")
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model=model, temperature=temperature, max_retries=max_retries,
                                 timeout=timeout, thinking_level=thinking_level)
    return inputs | prompt | llm | StrOutputParser()


def render_input(session_data):
    """The human turn's {input}: model_payload() as indented JSON."""
    return json.dumps(model_payload(session_data), indent=2)


def generate(chain, session_data):
    return chain.invoke(render_input(session_data))
