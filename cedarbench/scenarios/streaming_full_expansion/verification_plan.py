"""Hand-authored verification plan for streaming_full_expansion.

Stacks three mutations on top of streaming_base:
  - download action (Subscriber-only, forbid free content)
  - geo restriction (forbid !allowedRegions.contains(context.region) on watch)
  - age rating (forbid isKid + rating not G/PG on watch)

Four independent forbids on watch: bedtime, geo, age rating, free-download.
Watch floors include `!principal.profile.isKid` (sidesteps bedtime AND age
rating, both fire only for kids) and `resource.allowedRegions.contains(context.region)`
(sidesteps geo). FreeMember floors only need the geo exclusion (no profile
→ bedtime and rating forbids cannot apply).

Oscars window per spec: 2025-02-01 to 2025-03-31.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── base watch ceilings ──────────────────────────────────────────
        {"name": "freemember_movie_only_free", "description": "FreeMember may watch a Movie only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_movie_only_free.cedar")},
        {"name": "freemember_show_only_free", "description": "FreeMember may watch a Show only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "freemember_show_only_free.cedar")},
        {"name": "subscriber_movie_no_rent_buy", "description": "Subscriber may watch a Movie only when !needsRentOrBuy", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_movie_no_rent_buy.cedar")},
        {"name": "subscriber_show_premium_or_not_early", "description": "Subscriber may watch a Show only when !isEarlyAccess OR tier==premium", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "subscriber_show_premium_or_not_early.cedar")},
        {"name": "kid_bedtime_no_watch_movie", "description": "Subscriber may watch a Movie only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_movie.cedar")},
        {"name": "kid_bedtime_no_watch_show", "description": "Subscriber may watch a Show only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_show.cedar")},

        # ── age rating ceilings ──────────────────────────────────────────
        {"name": "kid_age_rating_no_watch_movie", "description": "Subscriber may watch a Movie only when NOT (isKid AND rating not G and not PG)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "kid_age_rating_no_watch_movie.cedar")},
        {"name": "kid_age_rating_no_watch_show", "description": "Subscriber may watch a Show only when NOT (isKid AND rating not G and not PG)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "kid_age_rating_no_watch_show.cedar")},

        # ── geo ceilings (one per principal x resource) ──────────────────
        {"name": "geo_freemember_movie_in_region", "description": "FreeMember may watch a Movie only when allowedRegions contains context.region", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "geo_freemember_movie_in_region.cedar")},
        {"name": "geo_freemember_show_in_region", "description": "FreeMember may watch a Show only when allowedRegions contains context.region", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "geo_freemember_show_in_region.cedar")},
        {"name": "geo_subscriber_movie_in_region", "description": "Subscriber may watch a Movie only when allowedRegions contains context.region", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "geo_subscriber_movie_in_region.cedar")},
        {"name": "geo_subscriber_show_in_region", "description": "Subscriber may watch a Show only when allowedRegions contains context.region", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "geo_subscriber_show_in_region.cedar")},

        # ── watch floors (with all exclusions baked in) ──────────────────
        {"name": "freemember_must_watch_free_movie_in_region", "description": "FreeMember in-region MUST watch any free Movie", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "freemember_must_watch_free_movie_in_region.cedar")},
        {"name": "freemember_must_watch_free_show_in_region", "description": "FreeMember in-region MUST watch any free Show", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "freemember_must_watch_free_show_in_region.cedar")},
        {"name": "subscriber_must_watch_movie_no_rent_no_kid_in_region", "description": "Non-kid in-region Subscriber MUST watch any !needsRentOrBuy Movie", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent_no_kid_in_region.cedar")},
        {"name": "subscriber_must_watch_show_not_early_no_kid_in_region", "description": "Non-kid in-region Subscriber MUST watch any !isEarlyAccess Show", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early_no_kid_in_region.cedar")},
        {"name": "premium_must_watch_show_early_no_kid_in_region", "description": "Non-kid in-region premium Subscriber MUST watch early-access Show in 24h pre-release", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "premium_must_watch_show_early_no_kid_in_region.cedar")},

        # ── rent ─────────────────────────────────────────────────────────
        {"name": "freemember_no_rent", "description": "FreeMember can NEVER rent (empty ceiling)", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"rent\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_no_rent.cedar")},
        {"name": "subscriber_rent_oscar_in_window_safety", "description": "Subscriber may rent only when oscar AND in window", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_rent_oscar_in_window_safety.cedar")},
        {"name": "subscriber_must_rent_oscar_in_window", "description": "Subscriber MUST rent any oscar movie in window", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_rent_oscar_in_window.cedar")},

        # ── buy ──────────────────────────────────────────────────────────
        {"name": "freemember_no_buy", "description": "FreeMember can NEVER buy (empty ceiling)", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"buy\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_no_buy.cedar")},
        {"name": "subscriber_buy_oscar_in_window_safety", "description": "Subscriber may buy only when oscar AND in window", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_buy_oscar_in_window_safety.cedar")},
        {"name": "subscriber_must_buy_oscar_in_window", "description": "Subscriber MUST buy any oscar movie in window", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_buy_oscar_in_window.cedar")},

        # ── download ─────────────────────────────────────────────────────
        {"name": "subscriber_download_movie_safety", "description": "Subscriber may download a Movie only when !isFree", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_download_movie_safety.cedar")},
        {"name": "subscriber_download_show_safety", "description": "Subscriber may download a Show only when !isFree", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "subscriber_download_show_safety.cedar")},
        {"name": "subscriber_must_download_movie_paid", "description": "Subscriber MUST download any non-free Movie", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_download_movie_paid.cedar")},
        {"name": "subscriber_must_download_show_paid", "description": "Subscriber MUST download any non-free Show", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "subscriber_must_download_show_paid.cedar")},

        # ── liveness ─────────────────────────────────────────────────────
        {"name": "liveness_freemember_watch_movie", "description": "FreeMember+watch+Movie liveness", "type": "always-denies-liveness", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie"},
        {"name": "liveness_freemember_watch_show", "description": "FreeMember+watch+Show liveness", "type": "always-denies-liveness", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show"},
        {"name": "liveness_subscriber_watch_movie", "description": "Subscriber+watch+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_watch_show", "description": "Subscriber+watch+Show liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show"},
        {"name": "liveness_subscriber_rent_movie", "description": "Subscriber+rent+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_buy_movie", "description": "Subscriber+buy+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_download_movie", "description": "Subscriber+download+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_download_show", "description": "Subscriber+download+Show liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"download\"", "resource_type": "Show"},
    ]
