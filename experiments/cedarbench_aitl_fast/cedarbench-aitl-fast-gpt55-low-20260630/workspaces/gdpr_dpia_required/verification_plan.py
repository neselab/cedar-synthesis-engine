"""Hand-authored verification plan for realworld/gdpr_dpia_required.

GDPR Art. 35 — high-risk processing activities require a valid Data
Protection Impact Assessment (DPIA): completed, approved, and not
older than 365 days. Tests:
  * optional datetime attribute (dpiaCompletedDate?) with has-guard
  * duration arithmetic via durationSince + < duration("365d")
  * per-action policy splits with shared validity predicate
  * DPO override on terminateProcessing
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "initiate_safety", "description": "initiateProcessing only when controller AND (low/medium risk OR valid fresh approved DPIA)", "type": "implies", "principal_type": "Processor", "action": 'Action::"initiateProcessing"', "resource_type": "ProcessingActivity", "reference_path": os.path.join(REFS, "initiate_safety.cedar")},
        {"name": "modify_safety", "description": "modifyProcessing only when controller AND (low/medium risk OR valid fresh approved DPIA)", "type": "implies", "principal_type": "Processor", "action": 'Action::"modifyProcessing"', "resource_type": "ProcessingActivity", "reference_path": os.path.join(REFS, "modify_safety.cedar")},
        {"name": "terminate_safety", "description": "terminateProcessing only when controller or DPO", "type": "implies", "principal_type": "Processor", "action": 'Action::"terminateProcessing"', "resource_type": "ProcessingActivity", "reference_path": os.path.join(REFS, "terminate_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_controller_initiate_low", "description": "controller MUST initiate low-risk activity (no DPIA required)", "type": "floor", "principal_type": "Processor", "action": 'Action::"initiateProcessing"', "resource_type": "ProcessingActivity", "floor_path": os.path.join(REFS, "floor_controller_initiate_low.cedar")},
        {"name": "floor_controller_initiate_high_valid_dpia", "description": "controller MUST initiate high-risk activity when valid fresh approved DPIA exists", "type": "floor", "principal_type": "Processor", "action": 'Action::"initiateProcessing"', "resource_type": "ProcessingActivity", "floor_path": os.path.join(REFS, "floor_controller_initiate_high_valid_dpia.cedar")},
        {"name": "floor_controller_modify_medium", "description": "controller MUST modify medium-risk activity (no DPIA required)", "type": "floor", "principal_type": "Processor", "action": 'Action::"modifyProcessing"', "resource_type": "ProcessingActivity", "floor_path": os.path.join(REFS, "floor_controller_modify_medium.cedar")},
        {"name": "floor_dpo_terminate", "description": "DPO MUST terminate any processing activity (compliance wind-down)", "type": "floor", "principal_type": "Processor", "action": 'Action::"terminateProcessing"', "resource_type": "ProcessingActivity", "floor_path": os.path.join(REFS, "floor_dpo_terminate.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_initiate", "description": "at least one initiateProcessing permitted", "type": "always-denies-liveness", "principal_type": "Processor", "action": 'Action::"initiateProcessing"', "resource_type": "ProcessingActivity"},
        {"name": "liveness_modify", "description": "at least one modifyProcessing permitted", "type": "always-denies-liveness", "principal_type": "Processor", "action": 'Action::"modifyProcessing"', "resource_type": "ProcessingActivity"},
        {"name": "liveness_terminate", "description": "at least one terminateProcessing permitted", "type": "always-denies-liveness", "principal_type": "Processor", "action": 'Action::"terminateProcessing"', "resource_type": "ProcessingActivity"},
    ]
