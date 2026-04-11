// Ceiling: a FreeMember can NEVER rent a Movie. This file is intentionally
// empty (no permit rules) — it represents the empty permitted set, so the
// implies check `candidate ⇒ ceiling` reduces to `candidate permits nothing
// for FreeMember + rent + Movie`.
