"""Hand-authored verification plan for streaming_add_trial_tier.

Same as streaming_base + 2 TrialMember ceilings, 4 TrialMember floors,
and 2 TrialMember liveness checks. TrialMember has no `profile` attribute,
so the bedtime forbid never fires for it (Cedar would type-error if it
tried). TrialMember is also excluded from the rent/buy actions at the
schema level, so no rent/buy checks are needed for TrialMember.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── streaming_base watch ceilings & floors ───────────────────────
        {"name": "freemember_movie_only_free", "description": "FreeMember may watch a Movie only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_movie_only_free.cedar")},
        {"name": "freemember_show_only_free", "description": "FreeMember may watch a Show only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "freemember_show_only_free.cedar")},
        {"name": "subscriber_movie_no_rent_buy", "description": "Subscriber may watch a Movie only when !needsRentOrBuy", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_movie_no_rent_buy.cedar")},
        {"name": "subscriber_show_premium_or_not_early", "description": "Subscriber may watch a Show only when !isEarlyAccess OR tier==premium", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "subscriber_show_premium_or_not_early.cedar")},
        {"name": "kid_bedtime_no_watch_movie", "description": "Subscriber may watch a Movie only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_movie.cedar")},
        {"name": "kid_bedtime_no_watch_show", "description": "Subscriber may watch a Show only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_show.cedar")},
        {"name": "freemember_must_watch_free_movie", "description": "FreeMember MUST watch any free Movie", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "freemember_must_watch_free_movie.cedar")},
        {"name": "freemember_must_watch_free_show", "description": "FreeMember MUST watch any free Show", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "freemember_must_watch_free_show.cedar")},
        {"name": "subscriber_must_watch_movie_no_rent_no_kid", "description": "Non-kid Subscriber MUST watch any !needsRentOrBuy Movie", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent_no_kid.cedar")},
        {"name": "subscriber_must_watch_show_not_early_no_kid", "description": "Non-kid Subscriber MUST watch any !isEarlyAccess Show", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early_no_kid.cedar")},
        {"name": "premium_must_watch_show_early_no_kid", "description": "Non-kid premium Subscriber MUST watch early-access Show in 24h pre-release", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "premium_must_watch_show_early_no_kid.cedar")},

        # ── TrialMember ceilings & floors ────────────────────────────────
        {"name": "trial_movie_safety", "description": "TrialMember may watch a Movie only when isFree OR (!needsRentOrBuy AND trial active)", "type": "implies", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "trial_movie_safety.cedar")},
        {"name": "trial_show_safety", "description": "TrialMember may watch a Show only when isFree OR (!isEarlyAccess AND trial active)", "type": "implies", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "trial_show_safety.cedar")},
        {"name": "trial_must_watch_free_movie", "description": "TrialMember MUST watch any free Movie", "type": "floor", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "trial_must_watch_free_movie.cedar")},
        {"name": "trial_must_watch_free_show", "description": "TrialMember MUST watch any free Show", "type": "floor", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "trial_must_watch_free_show.cedar")},
        {"name": "trial_active_must_watch_paid_movie", "description": "Active-trial TrialMember MUST watch any !needsRentOrBuy Movie", "type": "floor", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "trial_active_must_watch_paid_movie.cedar")},
        {"name": "trial_active_must_watch_paid_show", "description": "Active-trial TrialMember MUST watch any !isEarlyAccess Show", "type": "floor", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "trial_active_must_watch_paid_show.cedar")},

        # ── rent ─────────────────────────────────────────────────────────
        {"name": "freemember_no_rent", "description": "FreeMember can NEVER rent (empty ceiling)", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"rent\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_no_rent.cedar")},
        {"name": "subscriber_rent_oscar_in_window_safety", "description": "Subscriber may rent only when oscar AND in window", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_rent_oscar_in_window_safety.cedar")},
        {"name": "subscriber_must_rent_oscar_in_window", "description": "Subscriber MUST rent any oscar movie in window", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_rent_oscar_in_window.cedar")},

        # ── buy ──────────────────────────────────────────────────────────
        {"name": "freemember_no_buy", "description": "FreeMember can NEVER buy (empty ceiling)", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"buy\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_no_buy.cedar")},
        {"name": "subscriber_buy_oscar_in_window_safety", "description": "Subscriber may buy only when oscar AND in window", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_buy_oscar_in_window_safety.cedar")},
        {"name": "subscriber_must_buy_oscar_in_window", "description": "Subscriber MUST buy any oscar movie in window", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_buy_oscar_in_window.cedar")},

        # ── liveness ─────────────────────────────────────────────────────
        {"name": "liveness_freemember_watch_movie", "description": "FreeMember+watch+Movie liveness", "type": "always-denies-liveness", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie"},
        {"name": "liveness_freemember_watch_show", "description": "FreeMember+watch+Show liveness", "type": "always-denies-liveness", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show"},
        {"name": "liveness_subscriber_watch_movie", "description": "Subscriber+watch+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_watch_show", "description": "Subscriber+watch+Show liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show"},
        {"name": "liveness_trial_watch_movie", "description": "TrialMember+watch+Movie liveness", "type": "always-denies-liveness", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Movie"},
        {"name": "liveness_trial_watch_show", "description": "TrialMember+watch+Show liveness", "type": "always-denies-liveness", "principal_type": "TrialMember", "action": "Action::\"watch\"", "resource_type": "Show"},
        {"name": "liveness_subscriber_rent_movie", "description": "Subscriber+rent+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_buy_movie", "description": "Subscriber+buy+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie"},
    ]
