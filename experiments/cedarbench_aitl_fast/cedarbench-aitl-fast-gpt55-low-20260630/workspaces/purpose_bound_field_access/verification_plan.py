"""Hand-authored verification plan for realworld/purpose_bound_field_access.

Purpose-bound field access enforces data minimization: each access carries
a declared purpose (treatment / billing / research) and a requested field
name, and the policy must check that the field is in the resource's
per-purpose allowlist AND that the requesting workforce member's role
matches the declared purpose.

The natural OOP encoding -- `resource.purposeFields[declaredPurpose]
.contains(requestedField)` -- is exactly what Cedar does NOT support
(no dynamic record key access). The correct encoding stores three
separate `Set<String>` attributes on the resource and uses an explicit
OR-branching permit policy that selects the matching set based on the
declared purpose literal.

Failure modes this scenario hunts:
  - Candidate writes `resource.purposeFields[ctx.declaredPurpose]
    .contains(...)` (Cedar rejects: no record subscript).
  - Candidate forgets to require role-purpose match, letting any
    workforce member access any record by declaring any purpose.
  - Candidate forgets to require `contains(requestedField)` against
    the matching purpose set, granting cross-purpose field leakage
    (clinician-with-treatment-purpose reading billing-only fields).
  - Candidate enumerates only one or two of the three purposes,
    failing one of the floors.
  - Candidate inverts the role-purpose mapping (clinician -> billing).
  - Candidate forgets to deny unsupported declaredPurpose values
    (relies on default-deny instead -- which is fine, but only if the
    permit doesn't accidentally cover them).

5 checks total (1 ceiling + 3 floors + 1 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling -------------------------------------------------
        {
            "name": "access_safety",
            "description": "accessField permitted ONLY when (purpose, role, field-in-matching-set) all align across one of the three supported branches",
            "type": "implies",
            "principal_type": "Workforce",
            "action": 'Action::"accessField"',
            "resource_type": "PatientRecord",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_treatment",
            "description": "Clinician declaring purpose treatment requesting a field in purposeFieldsTreatment MUST be permitted",
            "type": "floor",
            "principal_type": "Workforce",
            "action": 'Action::"accessField"',
            "resource_type": "PatientRecord",
            "floor_path": os.path.join(REFS, "floor_treatment.cedar"),
        },
        {
            "name": "floor_billing",
            "description": "Billing clerk declaring purpose billing requesting a field in purposeFieldsBilling MUST be permitted",
            "type": "floor",
            "principal_type": "Workforce",
            "action": 'Action::"accessField"',
            "resource_type": "PatientRecord",
            "floor_path": os.path.join(REFS, "floor_billing.cedar"),
        },
        {
            "name": "floor_research",
            "description": "Researcher declaring purpose research requesting a field in purposeFieldsResearch MUST be permitted",
            "type": "floor",
            "principal_type": "Workforce",
            "action": 'Action::"accessField"',
            "resource_type": "PatientRecord",
            "floor_path": os.path.join(REFS, "floor_research.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "Workforce+accessField+PatientRecord liveness",
            "type": "always-denies-liveness",
            "principal_type": "Workforce",
            "action": 'Action::"accessField"',
            "resource_type": "PatientRecord",
        },
    ]
