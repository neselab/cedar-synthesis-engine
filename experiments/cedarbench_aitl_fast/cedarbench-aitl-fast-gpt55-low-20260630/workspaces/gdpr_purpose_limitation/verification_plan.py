"""Hand-authored verification plan for realworld/gdpr_purpose_limitation.

GDPR Article 5.1.b purpose-limitation pattern. Personal data carries the
set of purposes the data subject consented to; each request declares a
purpose; the policy must enforce purpose-match (or compatible-use approval
under Art. 6.4) AND per-action role gating (controller, processor, dpo).
Tests:
  - Set membership for purpose tags via .contains()
  - Optional context attribute (compatibleUseApproval) with positive
    has-guard — avoids the §8.3 negated-has trap
  - Per-action role gating: read open to all, process limited to
    controller/processor, disclose limited to dpo
  - Consent as a hard gate: no access without subjectConsent, including
    when compatibleUseApproval is present
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read permitted only when subjectConsent AND (purpose-match OR compatible-use approval)", "type": "implies", "principal_type": "Processor", "action": "Action::\"read\"", "resource_type": "PersonalData", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "process_safety", "description": "process permitted only when read conditions hold AND principal is controller or processor", "type": "implies", "principal_type": "Processor", "action": "Action::\"process\"", "resource_type": "PersonalData", "reference_path": os.path.join(REFS, "process_safety.cedar")},
        {"name": "disclose_safety", "description": "disclose permitted only when read conditions hold AND principal is dpo", "type": "implies", "principal_type": "Processor", "action": "Action::\"disclose\"", "resource_type": "PersonalData", "reference_path": os.path.join(REFS, "disclose_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "controller_purpose_match_must_read", "description": "controller with consent and declaredPurpose in allowedPurposes MUST read", "type": "floor", "principal_type": "Processor", "action": "Action::\"read\"", "resource_type": "PersonalData", "floor_path": os.path.join(REFS, "controller_purpose_match_must_read.cedar")},
        {"name": "dpo_compatible_use_must_read", "description": "dpo with consent and compatibleUseApproval MUST read (Art. 6.4 escape hatch)", "type": "floor", "principal_type": "Processor", "action": "Action::\"read\"", "resource_type": "PersonalData", "floor_path": os.path.join(REFS, "dpo_compatible_use_must_read.cedar")},
        {"name": "controller_purpose_match_must_process", "description": "controller with consent and declaredPurpose in allowedPurposes MUST process", "type": "floor", "principal_type": "Processor", "action": "Action::\"process\"", "resource_type": "PersonalData", "floor_path": os.path.join(REFS, "controller_purpose_match_must_process.cedar")},
        {"name": "processor_purpose_match_must_process", "description": "processor with consent and declaredPurpose in allowedPurposes MUST process", "type": "floor", "principal_type": "Processor", "action": "Action::\"process\"", "resource_type": "PersonalData", "floor_path": os.path.join(REFS, "processor_purpose_match_must_process.cedar")},
        {"name": "dpo_purpose_match_must_disclose", "description": "dpo with consent and declaredPurpose in allowedPurposes MUST disclose", "type": "floor", "principal_type": "Processor", "action": "Action::\"disclose\"", "resource_type": "PersonalData", "floor_path": os.path.join(REFS, "dpo_purpose_match_must_disclose.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "Processor+read+PersonalData liveness", "type": "always-denies-liveness", "principal_type": "Processor", "action": "Action::\"read\"", "resource_type": "PersonalData"},
        {"name": "liveness_process", "description": "Processor+process+PersonalData liveness", "type": "always-denies-liveness", "principal_type": "Processor", "action": "Action::\"process\"", "resource_type": "PersonalData"},
        {"name": "liveness_disclose", "description": "Processor+disclose+PersonalData liveness", "type": "always-denies-liveness", "principal_type": "Processor", "action": "Action::\"disclose\"", "resource_type": "PersonalData"},
    ]
