"""Hand-authored verification plan for streaming_remove_bedtime.

Same structure as streaming_base, with two differences from the base:
  1. No bedtime forbid (kid profiles have no time-based limits in this
     variant), so no kid_bedtime_* ceilings and no `!isKid` exclusion in
     the subscriber watch floors.
  2. Different Oscars window per the spec:
     `[2025-02-01T00:00:00Z, 2025-03-31T23:59:59Z]` (entire Feb-Mar 2025).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── watch ceilings ───────────────────────────────────────────────
        {
            "name": "freemember_movie_only_free",
            "description": "FreeMember may watch a Movie only when isFree",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_movie_only_free.cedar"),
        },
        {
            "name": "freemember_show_only_free",
            "description": "FreeMember may watch a Show only when isFree",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "reference_path": os.path.join(REFS, "freemember_show_only_free.cedar"),
        },
        {
            "name": "subscriber_movie_no_rent_buy",
            "description": "Subscriber may watch a Movie only when !needsRentOrBuy",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "subscriber_movie_no_rent_buy.cedar"),
        },
        {
            "name": "subscriber_show_release_or_premium_early",
            "description": "Subscriber may watch a Show only when (!isEarlyAccess) OR (now >= releaseDate) OR (premium AND now >= releaseDate-24h)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "reference_path": os.path.join(REFS, "subscriber_show_release_or_premium_early.cedar"),
        },

        # ── watch floors ─────────────────────────────────────────────────
        {
            "name": "freemember_must_watch_free_movie",
            "description": "FreeMember MUST be permitted to watch any free Movie",
            "type": "floor",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "freemember_must_watch_free_movie.cedar"),
        },
        {
            "name": "freemember_must_watch_free_show",
            "description": "FreeMember MUST be permitted to watch any free Show",
            "type": "floor",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "freemember_must_watch_free_show.cedar"),
        },
        {
            "name": "subscriber_must_watch_movie_no_rent",
            "description": "Subscriber MUST be permitted to watch any !needsRentOrBuy Movie",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent.cedar"),
        },
        {
            "name": "subscriber_must_watch_show_not_early",
            "description": "Subscriber MUST be permitted to watch any !isEarlyAccess Show",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early.cedar"),
        },
        {
            "name": "subscriber_must_watch_show_post_release",
            "description": "Subscriber MUST be permitted to watch a Show that is past its releaseDate (early-access lifts after release)",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_show_post_release.cedar"),
        },
        {
            "name": "premium_must_watch_show_early_in_window",
            "description": "Premium Subscriber MUST be permitted to watch a Show in early access if now is within 24h before releaseDate",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "premium_must_watch_show_early_in_window.cedar"),
        },

        # ── rent ceilings & floor ────────────────────────────────────────
        {
            "name": "freemember_no_rent",
            "description": "FreeMember can NEVER rent a Movie (empty ceiling)",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_no_rent.cedar"),
        },
        {
            "name": "subscriber_rent_oscar_in_window_safety",
            "description": "Subscriber may rent a Movie only when isOscarNominated AND now in [2025-02-01,2025-03-31]",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "subscriber_rent_oscar_in_window_safety.cedar"),
        },
        {
            "name": "subscriber_must_rent_oscar_in_window",
            "description": "Subscriber MUST be permitted to rent any Oscar-nominated Movie in window",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_rent_oscar_in_window.cedar"),
        },

        # ── buy ceilings & floor ─────────────────────────────────────────
        {
            "name": "freemember_no_buy",
            "description": "FreeMember can NEVER buy a Movie (empty ceiling)",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_no_buy.cedar"),
        },
        {
            "name": "subscriber_buy_oscar_in_window_safety",
            "description": "Subscriber may buy a Movie only when isOscarNominated AND now in window",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "subscriber_buy_oscar_in_window_safety.cedar"),
        },
        {
            "name": "subscriber_must_buy_oscar_in_window",
            "description": "Subscriber MUST be permitted to buy any Oscar-nominated Movie in window",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_buy_oscar_in_window.cedar"),
        },

        # ── liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_freemember_watch_movie",
            "description": "FreeMember+watch+Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_freemember_watch_show",
            "description": "FreeMember+watch+Show has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
        },
        {
            "name": "liveness_subscriber_watch_movie",
            "description": "Subscriber+watch+Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_subscriber_watch_show",
            "description": "Subscriber+watch+Show has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
        },
        {
            "name": "liveness_subscriber_rent_movie",
            "description": "Subscriber+rent+Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_subscriber_buy_movie",
            "description": "Subscriber+buy+Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
        },
    ]
