"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # === Ceiling checks (candidate ≤ ceiling) ===
        {
            "name": "ceiling_cancel",
            "description": "cancelReservation only for members or admins (not viewers)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"cancelReservation"',
            "resource_type": "Reservation",
            "reference_path": os.path.join(REFS, "ceiling_cancel.cedar"),
        },
        {
            "name": "ceiling_view_reservation",
            "description": "viewReservation for viewers, members, or admins",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"viewReservation"',
            "resource_type": "Reservation",
            "reference_path": os.path.join(REFS, "ceiling_view_reservation.cedar"),
        },

        # === Floor checks (floor ≤ candidate) ===
        {
            "name": "floor_member_cancel",
            "description": "Members with hotelReservations MUST be able to cancelReservation",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"cancelReservation"',
            "resource_type": "Reservation",
            "floor_path": os.path.join(REFS, "floor_member_cancel.cedar"),
        },

        # === Liveness checks ===
        {
            "name": "liveness_cancel",
            "description": "cancelReservation is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"cancelReservation"',
            "resource_type": "Reservation",
        },
    ]
