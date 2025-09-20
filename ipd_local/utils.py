import sys
import os
import re
from typing import get_origin

def clean_json_like(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
    s = re.sub(r"\n?```$", "", s)
    s = s.replace("“", '"').replace("”", '"').replace("„", '"').replace("‟", '"')
    s = s.replace("’", "'").replace("‘", "'")
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1:
        s = s[start:end+1]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s

_re_s5 = re.compile(r'"summary5"\s*:\s*"((?:\\.|[^"\\])*)"')
_re_s40 = re.compile(r'"summary40"\s*:\s*"((?:\\.|[^"\\])*)"')

def recover_summary_fields(s: str):
    s = s.strip()
    m5 = _re_s5.search(s)
    m40 = _re_s40.search(s)
    out = {}
    if m5:
        out["summary5"] = m5.group(1)
    if m40:
        out["summary40"] = m40.group(1)
    return out if out else None

class suppress_output:
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.null = open(os.devnull, "w")
        sys.stdout = self.null
        sys.stderr = self.null  # Redirect stderr as well

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.null.close()


def get_length_no_whitespace(code):
    return sum([
        len("".join(line.split())) for line in code
    ])

def get_length_no_whitespace_no_comments(code):
    length = 0
    for line in code:
        if "#" in line:
            length += get_length_no_whitespace(line.split("#")[0])
        else:
            length += get_length_no_whitespace(line)
    return length


def check_type(obj, expected_type):
    origin = get_origin(expected_type)
    if origin is None:
        # Not a generic type
        return isinstance(obj, expected_type)
    else:
        # Check against the origin type
        return isinstance(obj, origin)