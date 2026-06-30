"""Verification plan for realworld/iot_device_auth.
Capability-based IoT device authorization with non-User principals.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        {"name": "telemetry_safety", "description": "telemetry only when active + read_sensor cap", "type": "implies", "principal_type": "Device", "action": 'Action::"telemetry"', "resource_type": "Endpoint", "reference_path": os.path.join(REFS, "telemetry_safety.cedar")},
        {"name": "control_safety", "description": "control only when active + actuate cap", "type": "implies", "principal_type": "Device", "action": 'Action::"control"', "resource_type": "Endpoint", "reference_path": os.path.join(REFS, "control_safety.cedar")},
        {"name": "stream_safety", "description": "stream only when active + stream cap", "type": "implies", "principal_type": "Device", "action": 'Action::"stream"', "resource_type": "Endpoint", "reference_path": os.path.join(REFS, "stream_safety.cedar")},
        {"name": "manage_safety", "description": "manage only when owner", "type": "implies", "principal_type": "User", "action": 'Action::"manage"', "resource_type": "Endpoint", "reference_path": os.path.join(REFS, "manage_safety.cedar")},
        {"name": "floor_active_telemetry", "description": "active device with read_sensor MUST telemetry", "type": "floor", "principal_type": "Device", "action": 'Action::"telemetry"', "resource_type": "Endpoint", "floor_path": os.path.join(REFS, "floor_active_telemetry.cedar")},
        {"name": "floor_active_control", "description": "active device with actuate MUST control", "type": "floor", "principal_type": "Device", "action": 'Action::"control"', "resource_type": "Endpoint", "floor_path": os.path.join(REFS, "floor_active_control.cedar")},
        {"name": "floor_owner_manage", "description": "owner MUST manage", "type": "floor", "principal_type": "User", "action": 'Action::"manage"', "resource_type": "Endpoint", "floor_path": os.path.join(REFS, "floor_owner_manage.cedar")},
        {"name": "liveness_telemetry", "description": "at least one telemetry permitted", "type": "always-denies-liveness", "principal_type": "Device", "action": 'Action::"telemetry"', "resource_type": "Endpoint"},
        {"name": "liveness_control", "description": "at least one control permitted", "type": "always-denies-liveness", "principal_type": "Device", "action": 'Action::"control"', "resource_type": "Endpoint"},
        {"name": "liveness_manage", "description": "at least one manage permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"manage"', "resource_type": "Endpoint"},
    ]
