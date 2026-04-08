"""Hand-authored verification plan for streaming_multidevice.

Same as streaming_base + 4 stream-limit ceilings (FreeMember and Subscriber
× Movie and Show) for the new concurrent-stream forbids:
  - FreeMember: activeStreams < 1
  - Subscriber tier=standard: activeStreams < 2
  - Subscriber tier=premium:  activeStreams < 5

All watch floors include the corresponding stream-limit exclusion as the
§8.8 floor-bound consistency excursion. Subscriber non-premium floors use
< 2 (the strictest tier limit, which works for any tier including premium).
The premium-specific floor uses < 5.

Rent and buy are NOT subject to stream limits, so those reuse streaming_base
references unchanged. Oscars window per spec: 2025-02-01 to 2025-03-31.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── streaming_base watch ceilings ────────────────────────────────
        {"name": "freemember_movie_only_free", "description": "FreeMember may watch a Movie only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_movie_only_free.cedar")},
        {"name": "freemember_show_only_free", "description": "FreeMember may watch a Show only when isFree", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "freemember_show_only_free.cedar")},
        {"name": "subscriber_movie_no_rent_buy", "description": "Subscriber may watch a Movie only when !needsRentOrBuy", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_movie_no_rent_buy.cedar")},
        {"name": "subscriber_show_premium_or_not_early", "description": "Subscriber may watch a Show only when !isEarlyAccess OR tier==premium", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "subscriber_show_premium_or_not_early.cedar")},
        {"name": "kid_bedtime_no_watch_movie", "description": "Subscriber may watch a Movie only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_movie.cedar")},
        {"name": "kid_bedtime_no_watch_show", "description": "Subscriber may watch a Show only when NOT (isKid AND localTime in bedtime)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "kid_bedtime_no_watch_show.cedar")},

        # ── stream limit ceilings (new) ──────────────────────────────────
        {"name": "freemember_movie_stream_limit", "description": "FreeMember may watch a Movie only when activeStreams < 1", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "freemember_movie_stream_limit.cedar")},
        {"name": "freemember_show_stream_limit", "description": "FreeMember may watch a Show only when activeStreams < 1", "type": "implies", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "freemember_show_stream_limit.cedar")},
        {"name": "subscriber_movie_stream_limit", "description": "Subscriber may watch a Movie only when tier-stream-limit holds (standard<2, premium<5)", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "reference_path": os.path.join(REFS, "subscriber_movie_stream_limit.cedar")},
        {"name": "subscriber_show_stream_limit", "description": "Subscriber may watch a Show only when tier-stream-limit holds", "type": "implies", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "reference_path": os.path.join(REFS, "subscriber_show_stream_limit.cedar")},

        # ── watch floors (with stream + bedtime exclusions) ──────────────
        {"name": "freemember_must_watch_free_movie_low_streams", "description": "FreeMember MUST watch any free Movie when activeStreams < 1", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "freemember_must_watch_free_movie.cedar")},
        {"name": "freemember_must_watch_free_show_low_streams", "description": "FreeMember MUST watch any free Show when activeStreams < 1", "type": "floor", "principal_type": "FreeMember", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "freemember_must_watch_free_show.cedar")},
        {"name": "subscriber_must_watch_movie_no_rent_no_kid_low_streams", "description": "Non-kid Subscriber MUST watch any !needsRentOrBuy Movie when activeStreams < 2", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Movie", "floor_path": os.path.join(REFS, "subscriber_must_watch_movie_no_rent_no_kid_low_streams.cedar")},
        {"name": "subscriber_must_watch_show_not_early_no_kid_low_streams", "description": "Non-kid Subscriber MUST watch any !isEarlyAccess Show when activeStreams < 2", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "subscriber_must_watch_show_not_early_no_kid_low_streams.cedar")},
        {"name": "premium_must_watch_show_early_no_kid_low_streams", "description": "Non-kid premium Subscriber MUST watch early-access Show in 24h pre-release when activeStreams < 5", "type": "floor", "principal_type": "Subscriber", "action": "Action::\"watch\"", "resource_type": "Show", "floor_path": os.path.join(REFS, "premium_must_watch_show_early_no_kid_low_streams.cedar")},

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
        {"name": "liveness_subscriber_rent_movie", "description": "Subscriber+rent+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"rent\"", "resource_type": "Movie"},
        {"name": "liveness_subscriber_buy_movie", "description": "Subscriber+buy+Movie liveness", "type": "always-denies-liveness", "principal_type": "Subscriber", "action": "Action::\"buy\"", "resource_type": "Movie"},
    ]
