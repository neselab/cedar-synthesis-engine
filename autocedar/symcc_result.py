"""Recognize SymCC's formal verdict lines, independent of witness contents."""


def formal_verdict(output: str) -> bool | None:
    """Return True/False for a formal verdict, None for no unambiguous verdict.

    A witness can itself contain strings such as ``VERIFIED``. Those strings,
    a diagnostic mentioning a counterexample, and solver ``unknown`` are not
    verdicts. Both supported CLI wrappers use this same interpretation.
    """
    verdicts = set()
    for line in output.splitlines():
        verdict = line.strip().rsplit(":", 1)[-1].strip()
        if verdict == "VERIFIED":
            verdicts.add(True)
        elif verdict == "DOES NOT HOLD":
            verdicts.add(False)
    return next(iter(verdicts)) if len(verdicts) == 1 else None
