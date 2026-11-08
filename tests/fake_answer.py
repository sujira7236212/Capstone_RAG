"""The fake LLM chains in tests/test_service.py and tests/test_replay_captured.py script plain
strings. Since prompt v17 the service asks for JSON in a schema made per set, so a scripted string
becomes an answer in that schema: the `fault` of every fault the set carries, or the `keep` line
of a clean set. The text the service builds from it then contains the string."""
import json


class Raw(str):
    """A scripted answer sent exactly as written, for answers that break the schema."""


def as_json(text, schema):
    if schema is None or not isinstance(text, str) or isinstance(text, Raw):
        return text
    props = schema["properties"]
    answer = {"keep": "", "progress": "First set on record.", "health": "", "next": ["Same again."]}
    if "faults" in props:
        rules = props["faults"]["items"]["properties"]["rule"]["enum"]
        answer["faults"] = [{"rule": r, "fault": text, "fix": "Fix it.", "what_it_is": "", "likely_cause": "",
                             "setup_change": "", "drill": "", "check": "", "in_this_set": ""} for r in rules]
    else:
        answer["keep"] = text
    return json.dumps(answer)
