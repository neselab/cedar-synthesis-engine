"""Hand-authored verification plan for streaming_remove_oscars.

This variant removes the Oscars promo (no rent/buy actions, no
isOscarNominated attribute) but KEEPS the kid-bedtime forbid. So
all Subscriber+watch floors include a `!principal.profile.isKid`
exclusion per the §8.8 floor-bound consistency rule.
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
        {
            "name": "kid_bedtime_no_watch_movie",
            "description": "Subscriber may watch a Movie only when NOT (isKid AND localTime in bedtime)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_movie.cedar"),
        },
        {
            "name": "kid_bedtime_no_watch_show",
            "description": "Subscriber may watch a Show only when NOT (isKid AND localTime in bedtime)",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_show.cedar"),
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
            "name": "subscriber_must_watch_movie_no_rent_no_kid",
            "description": "Non-kid Subscriber MUST be permitted to watch any !needsRentOrBuy Movie",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent_no_kid.cedar"),
        },
        {
            "name": "subscriber_must_watch_show_not_early_no_kid",
            "description": "Non-kid Subscriber MUST be permitted to watch any !isEarlyAccess Show",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early_no_kid.cedar"),
        },
        {
            "name": "subscriber_must_watch_show_post_release_no_kid",
            "description": "Non-kid Subscriber MUST be permitted to watch a Show post-release",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_show_post_release_no_kid.cedar"),
        },
        {
            "name": "premium_must_watch_show_early_no_kid",
            "description": "Non-kid premium Subscriber MUST be permitted to watch early-access Show in 24h pre-release window",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "premium_must_watch_show_early_no_kid.cedar"),
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
    ]
