"""Hand-authored verification plan for streaming_base.

Phase 1 was performed by the conversation Opus 4.6 instance, not the API
planner. The plan covers six requirements from policy_spec.md:
  1. FreeMember can only watch free content.
  2. Subscribers can watch any non-rent-or-buy Movie.
  3. Subscribers can watch any Show that is past its early-access window.
  4. Premium subscribers can watch Shows in the early-access window.
  5. Subscribers (any tier) can rent or buy Oscar-nominated Movies in the
     28-day window leading up to the 97th Academy Awards (March 2, 2025).
  6. Subscribers with the kid profile cannot watch during local bedtime.

Floor references for Subscriber + watch include `!principal.profile.isKid`
exclusions per the §8.8 floor-bound consistency rule, so the floor's
permitted set is disjoint from the kid-bedtime forbid's denied set.

The Oscars window is pinned to `[2025-02-02T00:00:00Z, 2025-03-02T23:59:59Z]`
(28 days ending at end-of-day on the awards date). Candidates must use
these exact constants for the bound checks to align.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── watch ceilings (implies) ─────────────────────────────────────
        {
            "name": "freemember_movie_only_free",
            "description": "FreeMember may watch a Movie only when the movie is free",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_movie_only_free.cedar"),
        },
        {
            "name": "freemember_show_only_free",
            "description": "FreeMember may watch a Show only when the show is free",
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
            "name": "subscriber_show_premium_or_not_early",
            "description": "Subscriber may watch a Show only when !isEarlyAccess OR tier==premium",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "reference_path": os.path.join(REFS, "subscriber_show_premium_or_not_early.cedar"),
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
            "description": "Subscriber (non-kid) MUST be permitted to watch any !needsRentOrBuy Movie",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent_no_kid.cedar"),
        },
        {
            "name": "subscriber_must_watch_show_not_early_no_kid",
            "description": "Subscriber (non-kid) MUST be permitted to watch any !isEarlyAccess Show",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early_no_kid.cedar"),
        },
        {
            "name": "premium_must_watch_show_early_no_kid",
            "description": "Premium Subscriber (non-kid) MUST be permitted to watch any isEarlyAccess Show",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
            "floor_path": os.path.join(REFS, "premium_must_watch_show_early_no_kid.cedar"),
        },

        # ── rent ceilings & floor ────────────────────────────────────────
        {
            "name": "freemember_no_rent",
            "description": "FreeMember can NEVER rent a Movie (empty ceiling, no permits)",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_no_rent.cedar"),
        },
        {
            "name": "subscriber_rent_only_oscar_in_window",
            "description": "Subscriber may rent a Movie only when isOscarNominated AND now in Oscars window",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "subscriber_rent_only_oscar_in_window.cedar"),
        },
        {
            "name": "subscriber_must_rent_oscar_in_window",
            "description": "Subscriber MUST be permitted to rent any isOscarNominated Movie in window",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_rent_oscar_in_window.cedar"),
        },

        # ── buy ceilings & floor ─────────────────────────────────────────
        {
            "name": "freemember_no_buy",
            "description": "FreeMember can NEVER buy a Movie (empty ceiling, no permits)",
            "type": "implies",
            "principal_type": "FreeMember",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "freemember_no_buy.cedar"),
        },
        {
            "name": "subscriber_buy_only_oscar_in_window",
            "description": "Subscriber may buy a Movie only when isOscarNominated AND now in Oscars window",
            "type": "implies",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "reference_path": os.path.join(REFS, "subscriber_buy_only_oscar_in_window.cedar"),
        },
        {
            "name": "subscriber_must_buy_oscar_in_window",
            "description": "Subscriber MUST be permitted to buy any isOscarNominated Movie in window",
            "type": "floor",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
            "floor_path": os.path.join(REFS, "subscriber_must_buy_oscar_in_window.cedar"),
        },

        # ── liveness checks (must permit at least one request) ──────────
        {
            "name": "liveness_freemember_watch_movie",
            "description": "FreeMember + watch + Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_freemember_watch_show",
            "description": "FreeMember + watch + Show has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "FreeMember",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
        },
        {
            "name": "liveness_subscriber_watch_movie",
            "description": "Subscriber + watch + Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_subscriber_watch_show",
            "description": "Subscriber + watch + Show has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"watch\"",
            "resource_type": "Show",
        },
        {
            "name": "liveness_subscriber_rent_movie",
            "description": "Subscriber + rent + Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"rent\"",
            "resource_type": "Movie",
        },
        {
            "name": "liveness_subscriber_buy_movie",
            "description": "Subscriber + buy + Movie has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Subscriber",
            "action": "Action::\"buy\"",
            "resource_type": "Movie",
        },
    ]
