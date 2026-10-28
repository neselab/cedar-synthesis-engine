"""Cut Cedar policy text into policies and clauses without Cedar's JSON form.

Cedar's JSON reader stops at 128 levels of nesting, and the JSON form of a
long chain of ``||`` or ``&&`` goes past that, so a policy Cedar parses can
still fail a round trip through JSON. The text can be cut directly instead:
outside strings and comments, a semicolon only ends a policy, and the first
parenthesis after ``permit`` or ``forbid`` opens the policy's scope.
"""

from __future__ import annotations

import re

_EFFECT = re.compile(r"(?<![@\w])(?:permit|forbid)\s*\(")


def _code(text: str) -> str:
    """The text with strings and comments blanked out; indices are unchanged."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
        else:
            i += 1
            continue
        out[i:j] = " " * (j - i)
        i = j
    return "".join(out)


def split_policies(text: str) -> list[str]:
    """The policies in Cedar text, in order, each ending with its semicolon."""
    code = _code(text)
    policies: list[str] = []
    start = 0
    for i, ch in enumerate(code):
        if ch == ";":
            body = code[start:i]
            policies.append(text[start + len(body) - len(body.lstrip()):i + 1])
            start = i + 1
    return policies


def is_template(policy: str) -> bool:
    """Whether the policy has a slot (``?principal`` or ``?resource``)."""
    return "?" in _code(policy)


def policy_conditions(policy: str) -> str:
    """The when and unless clauses of one policy, as written."""
    code = _code(policy)
    match = _EFFECT.search(code)
    if match is None:
        raise ValueError("The policy has no permit or forbid scope.")
    depth = 0
    for i in range(match.end() - 1, len(code)):
        if code[i] == "(":
            depth += 1
        elif code[i] == ")":
            depth -= 1
            if depth == 0:
                end = code.rfind(";")
                return policy[i + 1:end if end > i else len(policy)].strip()
    raise ValueError("The policy's scope is not closed.")
