"""Verification plan for realworld/conference_room_booking.
Time-windowed room booking with capacity + level checks.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        {"name": "book_safety", "description": "book only when level+capacity+future", "type": "implies", "principal_type": "Employee", "action": 'Action::"book"', "resource_type": "Room", "reference_path": os.path.join(REFS, "book_safety.cedar")},
        {"name": "cancel_safety", "description": "any employee can cancel", "type": "implies", "principal_type": "Employee", "action": 'Action::"cancel"', "resource_type": "Room", "reference_path": os.path.join(REFS, "cancel_safety.cedar")},
        {"name": "view_safety", "description": "any employee can view", "type": "implies", "principal_type": "Employee", "action": 'Action::"view"', "resource_type": "Room", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "floor_qualified_book", "description": "qualified employee MUST book", "type": "floor", "principal_type": "Employee", "action": 'Action::"book"', "resource_type": "Room", "floor_path": os.path.join(REFS, "floor_qualified_book.cedar")},
        {"name": "floor_any_view", "description": "any employee MUST view", "type": "floor", "principal_type": "Employee", "action": 'Action::"view"', "resource_type": "Room", "floor_path": os.path.join(REFS, "floor_any_view.cedar")},
        {"name": "floor_any_cancel", "description": "any employee MUST cancel", "type": "floor", "principal_type": "Employee", "action": 'Action::"cancel"', "resource_type": "Room", "floor_path": os.path.join(REFS, "floor_any_cancel.cedar")},
        {"name": "liveness_book", "description": "at least one book permitted", "type": "always-denies-liveness", "principal_type": "Employee", "action": 'Action::"book"', "resource_type": "Room"},
        {"name": "liveness_cancel", "description": "at least one cancel permitted", "type": "always-denies-liveness", "principal_type": "Employee", "action": 'Action::"cancel"', "resource_type": "Room"},
        {"name": "liveness_view", "description": "at least one view permitted", "type": "always-denies-liveness", "principal_type": "Employee", "action": 'Action::"view"', "resource_type": "Room"},
    ]
