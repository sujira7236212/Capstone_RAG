"""One feedback answer from a context and a session payload.

Moved out of test_rag_compare.py (2026-10-25, docs/plans/app_integration_plan.md A1). No
retry or rate-limit policy here: the batch scripts sleep between calls, the service must
not, so each caller wraps generate() in its own.
"""
import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_core.prompt import HUMAN_TEMPLATE, SYSTEM_PROMPT, model_payload

LLM_TEMPERATURE = 0.7

# Marker a batch script writes in place of an answer whose call failed.
GENERATION_ERROR = "Error occurred during generation"


def build_chain(context, model, temperature=LLM_TEMPERATURE, max_retries=1, timeout=None,
                thinking_level=None):
    """`max_retries` is the client's total number of attempts (1 = no retry). `thinking_level`
    ("minimal"/"low"/"medium"/"high", Gemini 3+): None keeps the model's own default, which
    is what every eval run so far used."""
    llm = ChatGoogleGenerativeAI(model=model, temperature=temperature, max_retries=max_retries,
                                 timeout=timeout, thinking_level=thinking_level)
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", HUMAN_TEMPLATE)])
    return (
        {"context": lambda x: context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def render_input(session_data):
    """The human turn's {input}: model_payload() as indented JSON."""
    return json.dumps(model_payload(session_data), indent=2)


def generate(chain, session_data):
    return chain.invoke(render_input(session_data))
