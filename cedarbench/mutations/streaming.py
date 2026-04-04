"""Streaming Service permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
# Streaming Service — Policy Specification

## Context

This policy governs access control for a streaming video platform with
FreeMember and Subscriber principals, and Movie and Show resources.

Subscribers have a `subscription` with a `tier` (e.g. "standard", "premium")
and a `profile` with an `isKid` boolean.

## Requirements

### 1. Subscriber Watch Permissions
- A **Subscriber** may **watch** any Show, UNLESS the show has `isEarlyAccess == true`
  AND the current time (`context.now.datetime`) is before the show's `releaseDate`.
- A **Subscriber** may **watch** any Movie, UNLESS the movie has `needsRentOrBuy == true`.

### 2. FreeMember Watch Permissions
- A **FreeMember** may **watch** any Movie where `isFree == true`.
- A **FreeMember** may **watch** any Show where `isFree == true`.

### 3. Oscar Promo (Rent/Buy Window)
- A **Subscriber** may **rent** or **buy** a Movie IF the movie has `isOscarNominated == true`
  AND the current time is within the Oscar promo window:
  `datetime("2025-02-01T00:00:00Z")` to `datetime("2025-03-31T23:59:59Z")`.

### 4. Early Access for Premium Subscribers
- A **Subscriber** with `subscription.tier == "premium"` may **watch** a Show
  that has `isEarlyAccess == true` even before the `releaseDate`, as long as
  the current time is within 24 hours before the `releaseDate`
  (i.e. `context.now.datetime >= resource.releaseDate.offset(duration("-24h"))`).

### 5. Kid Bedtime Restriction (Deny Rule)
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  outside of 6:00 AM to 9:00 PM local time.
  Local time is computed using `context.now.datetime.offset(context.now.localTimeOffset)`.
  Specifically, forbid watch when the local time-of-day is before 06:00 or at/after 21:00.

## Notes
- Cedar denies by default — no explicit deny-by-default needed.
- Temporal comparisons use Cedar's `datetime` and `duration` extension types.
- The bedtime rule is a `forbid` that overrides any `permit`.
"""


# -- Helpers -------------------------------------------------------------------

def _streaming_base_schema() -> str:
    """The base Streaming Service schema."""
    return """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
};

// Entities
entity FreeMember;
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
"""


# -- Easy Mutations ------------------------------------------------------------

class StreamingRemoveBedtime(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_remove_bedtime",
            base_scenario="streaming",
            difficulty="easy",
            description="Remove kid bedtime restriction; simpler temporal rules",
            operators=["P3"],
            features_tested=["rule_removal", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Remove localTimeOffset from watch context since bedtime is gone
        schema = _streaming_base_schema().replace(
            """\
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
    },""",
            """\
    context: {
        now: {
            datetime: datetime,
        },
    },""",
        )
        spec = """\
# Streaming Service — Policy Specification

## Context

This policy governs access control for a streaming video platform with
FreeMember and Subscriber principals, and Movie and Show resources.

Subscribers have a `subscription` with a `tier` (e.g. "standard", "premium")
and a `profile` with an `isKid` boolean.

## Requirements

### 1. Subscriber Watch Permissions
- A **Subscriber** may **watch** any Show, UNLESS the show has `isEarlyAccess == true`
  AND the current time (`context.now.datetime`) is before the show's `releaseDate`.
- A **Subscriber** may **watch** any Movie, UNLESS the movie has `needsRentOrBuy == true`.

### 2. FreeMember Watch Permissions
- A **FreeMember** may **watch** any Movie where `isFree == true`.
- A **FreeMember** may **watch** any Show where `isFree == true`.

### 3. Oscar Promo (Rent/Buy Window)
- A **Subscriber** may **rent** or **buy** a Movie IF the movie has `isOscarNominated == true`
  AND the current time is within the Oscar promo window:
  `datetime("2025-02-01T00:00:00Z")` to `datetime("2025-03-31T23:59:59Z")`.

### 4. Early Access for Premium Subscribers
- A **Subscriber** with `subscription.tier == "premium"` may **watch** a Show
  that has `isEarlyAccess == true` even before the `releaseDate`, as long as
  the current time is within 24 hours before the `releaseDate`
  (i.e. `context.now.datetime >= resource.releaseDate.offset(duration("-24h"))`).

## Notes
- Cedar denies by default — no explicit deny-by-default needed.
- Temporal comparisons use Cedar's `datetime` and `duration` extension types.
- There is no bedtime restriction in this variant — kid profiles have no time-based limits.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingAddDownload(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_add_download",
            base_scenario="streaming",
            difficulty="easy",
            description="Add download action; Subscriber only, free content excluded",
            operators=["S7", "P2", "P1"],
            features_tested=["new_action", "principal_restriction", "boolean_guard"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _streaming_base_schema()
        schema = schema_ops.add_action(schema, """\
// Download action — subscribers only
action download appliesTo {
    principal: [Subscriber],
    resource: [Movie, Show],
};""")
        spec = _BASE_SPEC + """\
### 6. Download Permissions
- A **Subscriber** may **download** any Movie or Show, UNLESS the content has `isFree == true`.
  (Free content is streaming-only and cannot be downloaded.)
- A **FreeMember** may NOT download any content (they are not a valid principal for download).

## Notes (Download)
- The download action only applies to Subscriber principals — FreeMember is excluded at the schema level.
- The free-content restriction is a `forbid` rule: `forbid(principal, action == Action::"download", resource) when { resource.isFree }`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingRemoveOscars(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_remove_oscars",
            base_scenario="streaming",
            difficulty="easy",
            description="Remove Oscar promo window; focus on early access + bedtime only",
            operators=["P3", "S10"],
            features_tested=["rule_removal", "attribute_cleanup"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _streaming_base_schema()
        schema = schema_ops.remove_attribute(schema, "Movie", "isOscarNominated")
        # Remove rent/buy actions entirely since they were only for Oscar promo
        schema = schema.replace(
            """\

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
""",
            "\n",
        )
        spec = """\
# Streaming Service — Policy Specification

## Context

This policy governs access control for a streaming video platform with
FreeMember and Subscriber principals, and Movie and Show resources.

Subscribers have a `subscription` with a `tier` (e.g. "standard", "premium")
and a `profile` with an `isKid` boolean.

## Requirements

### 1. Subscriber Watch Permissions
- A **Subscriber** may **watch** any Show, UNLESS the show has `isEarlyAccess == true`
  AND the current time (`context.now.datetime`) is before the show's `releaseDate`.
- A **Subscriber** may **watch** any Movie, UNLESS the movie has `needsRentOrBuy == true`.

### 2. FreeMember Watch Permissions
- A **FreeMember** may **watch** any Movie where `isFree == true`.
- A **FreeMember** may **watch** any Show where `isFree == true`.

### 3. Early Access for Premium Subscribers
- A **Subscriber** with `subscription.tier == "premium"` may **watch** a Show
  that has `isEarlyAccess == true` even before the `releaseDate`, as long as
  the current time is within 24 hours before the `releaseDate`
  (i.e. `context.now.datetime >= resource.releaseDate.offset(duration("-24h"))`).

### 4. Kid Bedtime Restriction (Deny Rule)
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  outside of 6:00 AM to 9:00 PM local time.
  Local time is computed using `context.now.datetime.offset(context.now.localTimeOffset)`.
  Specifically, forbid watch when the local time-of-day is before 06:00 or at/after 21:00.

## Notes
- Cedar denies by default — no explicit deny-by-default needed.
- There are no rent/buy actions or Oscar promo rules in this variant.
- The only temporal rules are early access and bedtime.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class StreamingAddGeoRestriction(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_add_geo_restriction",
            base_scenario="streaming",
            difficulty="medium",
            description="Add region to context, allowedRegions to content; forbid watch outside allowed regions",
            operators=["S1", "S4", "P1"],
            features_tested=["set_contains", "context_field", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Need to inline the full schema since we're adding context fields
        # and set attributes to multiple entities
        schema = """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
};

// Entities
entity FreeMember;
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
    allowedRegions: Set<String>,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
    allowedRegions: Set<String>,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
        region: String,
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
"""
        spec = _BASE_SPEC + """\
### 6. Geo-Restriction (Deny Rule)
- Each Movie and Show has an `allowedRegions` attribute (a `Set<String>` of region codes, e.g. `"US"`, `"EU"`, `"JP"`).
- The **watch** action's context includes a `region: String` field identifying the viewer's current region.
- If `!resource.allowedRegions.contains(context.region)`, the **watch** action is forbidden.
- This geo-restriction applies to all principals (FreeMember and Subscriber alike).
- The rent and buy actions are NOT geo-restricted.

## Notes (Geo-Restriction)
- The forbid rule uses `resource.allowedRegions.contains(context.region)` with a negation.
- This interacts with existing forbid rules (bedtime) — both may apply simultaneously.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingAddTrialTier(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_add_trial_tier",
            base_scenario="streaming",
            difficulty="medium",
            description="Add TrialMember entity with trialExpiry; can watch free + limited non-free until trial expires",
            operators=["S6", "P2", "P5"],
            features_tested=["new_entity", "temporal_expiry", "conditional_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Inline the full schema to add TrialMember entity and update action principal lists
        schema = """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
};

// Entities
entity FreeMember;
entity TrialMember = {
    trialExpiry: datetime,
};
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, TrialMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
"""
        spec = _BASE_SPEC + """\
### 6. TrialMember Permissions
- A **TrialMember** has a `trialExpiry: datetime` attribute.
- A TrialMember may **watch** any Movie or Show where `isFree == true` (same as FreeMember).
- A TrialMember may ALSO **watch** non-free Movies (where `isFree == false` and `needsRentOrBuy == false`)
  as long as the trial has not expired: `context.now.datetime < principal.trialExpiry`.
- A TrialMember may ALSO **watch** non-free Shows (where `isFree == false` and `isEarlyAccess == false`)
  as long as the trial has not expired: `context.now.datetime < principal.trialExpiry`.
- Once the trial expires, a TrialMember can only watch free content (same as FreeMember).
- A TrialMember may NOT **rent** or **buy** movies (they are not a valid principal for those actions).

## Notes (Trial Tier)
- The TrialMember is a new entity type distinct from FreeMember and Subscriber.
- Temporal expiry check compares `context.now.datetime` against `principal.trialExpiry`.
- TrialMembers do NOT get early access or Oscar promo benefits.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingAddAgeRating(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_add_age_rating",
            base_scenario="streaming",
            difficulty="medium",
            description="Add rating to Movie and Show; kid profiles restricted to G/PG only",
            operators=["S3", "P1"],
            features_tested=["string_enum", "multi_value_guard", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _streaming_base_schema()
        schema = schema_ops.add_attribute(schema, "Movie", "rating", "String")
        schema = schema_ops.add_attribute(schema, "Show", "rating", "String")
        spec = _BASE_SPEC + """\
### 6. Age Rating Restriction (Deny Rule)
- Each Movie and Show has a `rating: String` attribute with values: `"G"`, `"PG"`, `"PG13"`, or `"R"`.
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  on content where `rating` is NOT `"G"` and NOT `"PG"`.
  (Kid profiles can only watch G or PG rated content.)
- Non-kid Subscribers and FreeMember principals are NOT restricted by rating.

## Notes (Age Rating)
- This interacts with the bedtime rule — kid profiles have both time-based and rating-based restrictions.
- The rating check uses string equality: `resource.rating != "G" && resource.rating != "PG"`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class StreamingParentalControls(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_parental_controls",
            base_scenario="streaming",
            difficulty="hard",
            description="Add age rating + maxRating on profile; forbid content above profile max rating, plus bedtime",
            operators=["S3", "S1", "P1", "P1", "P10"],
            features_tested=["rating_hierarchy", "cross_attribute_comparison", "multi_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Need inline schema to modify the Profile type and add rating to entities
        schema = """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
    maxRating: String,
};

// Entities
entity FreeMember;
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
    rating: String,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
    rating: String,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
"""
        spec = _BASE_SPEC + """\
### 6. Parental Controls — Rating Restriction (Deny Rule)
- Each Movie and Show has a `rating: String` attribute with values: `"G"`, `"PG"`, `"PG13"`, or `"R"`.
- Each Subscriber profile has a `maxRating: String` attribute (same possible values).
- The rating hierarchy is: G < PG < PG13 < R.
- If a content's rating exceeds the profile's `maxRating`, the **watch** action is forbidden.
  Specifically:
  - If `maxRating == "G"`: only `"G"` content is allowed.
  - If `maxRating == "PG"`: `"G"` and `"PG"` content are allowed.
  - If `maxRating == "PG13"`: `"G"`, `"PG"`, and `"PG13"` content are allowed.
  - If `maxRating == "R"`: all content is allowed.
- This applies to all Subscriber profiles (both kid and non-kid).

### 7. Kid Bedtime + Parental Controls Interaction
- Kid profiles (`profile.isKid == true`) are subject to BOTH:
  (a) The bedtime restriction (no watching outside 6AM-9PM local time), AND
  (b) The parental rating restriction based on `profile.maxRating`.
- Both forbid rules operate independently — either one can block access.

## Notes (Parental Controls)
- Since Cedar has no built-in rating comparison, the rating hierarchy must be encoded
  as explicit string comparisons in forbid conditions.
- A kid profile with `maxRating == "PG"` is restricted both by time (bedtime) and by content rating.
- FreeMember principals have no profile and are NOT subject to parental controls.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingMultidevice(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_multidevice",
            base_scenario="streaming",
            difficulty="hard",
            description="Add activeStreams to context; standard limited to 2, premium to 5 concurrent streams",
            operators=["S2", "P1", "P10"],
            features_tested=["numeric_comparison", "tier_based_limits", "context_field"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Inline schema to add activeStreams to watch context
        schema = """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
};

// Entities
entity FreeMember;
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
        activeStreams: Long,
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};
"""
        spec = _BASE_SPEC + """\
### 6. Concurrent Stream Limits (Deny Rules)
- The **watch** action's context includes `activeStreams: Long`, the number of streams
  currently active on the account (not counting the one being requested).
- **FreeMember**: limited to 1 concurrent stream. Forbid watch if `context.activeStreams >= 1`.
- **Subscriber** with `subscription.tier == "standard"`: limited to 2 concurrent streams.
  Forbid watch if `context.activeStreams >= 2`.
- **Subscriber** with `subscription.tier == "premium"`: limited to 5 concurrent streams.
  Forbid watch if `context.activeStreams >= 5`.

## Notes (Multi-Device)
- The stream limit forbids are principal-type-specific and tier-specific.
- For Subscribers, the forbid conditions must check both `principal is Subscriber` and
  `principal.subscription.tier` to determine the correct limit.
- The FreeMember stream limit is a separate forbid rule.
- These forbid rules interact with the bedtime restriction — both may apply.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class StreamingFullExpansion(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_full_expansion",
            base_scenario="streaming",
            difficulty="hard",
            description="Add download + geo-restriction + age rating; three new constraints simultaneously",
            operators=["S7", "S1", "S3", "S4", "P2", "P1", "P1", "P1"],
            features_tested=["multi_mutation", "new_action", "set_contains", "string_enum", "multi_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Inline full schema with all three expansions
        schema = """\
// Streaming Service — Cedar Schema

// Types
type Subscription = {
    tier: String,
};
type Profile = {
    isKid: Bool,
};

// Entities
entity FreeMember;
entity Subscriber = {
    subscription: Subscription,
    profile: Profile,
};
entity Movie = {
    isFree: Bool,
    needsRentOrBuy: Bool,
    isOscarNominated: Bool,
    rating: String,
    allowedRegions: Set<String>,
};
entity Show = {
    isFree: Bool,
    releaseDate: datetime,
    isEarlyAccess: Bool,
    rating: String,
    allowedRegions: Set<String>,
};

// Actions for content in general
action watch appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie, Show],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration,
        },
        region: String,
    },
};

// Actions for movies only
action rent, buy appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Movie],
    context: {
        now: {
            datetime: datetime,
        },
    },
};

// Download action — subscribers only
action download appliesTo {
    principal: [Subscriber],
    resource: [Movie, Show],
};
"""
        spec = _BASE_SPEC + """\
### 6. Download Permissions
- A **Subscriber** may **download** any Movie or Show, UNLESS the content has `isFree == true`.
  (Free content is streaming-only and cannot be downloaded.)
- A **FreeMember** may NOT download any content (not a valid principal for download).

### 7. Geo-Restriction (Deny Rule)
- Each Movie and Show has an `allowedRegions` attribute (`Set<String>` of region codes).
- The **watch** action's context includes `region: String`.
- If `!resource.allowedRegions.contains(context.region)`, the **watch** action is forbidden.
- Geo-restriction applies to all principals (FreeMember and Subscriber).
- The rent, buy, and download actions are NOT geo-restricted.

### 8. Age Rating Restriction (Deny Rule)
- Each Movie and Show has a `rating: String` attribute with values: `"G"`, `"PG"`, `"PG13"`, or `"R"`.
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  on content where `rating` is NOT `"G"` and NOT `"PG"`.
  (Kid profiles can only watch G or PG rated content.)
- Non-kid Subscribers and FreeMember principals are NOT restricted by rating.

## Notes (Full Expansion)
- This scenario combines THREE new constraints on top of the base rules:
  (a) download action with free-content restriction,
  (b) geo-restriction via set membership,
  (c) age rating restriction for kid profiles.
- Four independent forbid rules may apply: bedtime, geo-restriction, age rating, and free-download block.
- The download action has no context (no temporal or geographic constraints).
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    StreamingRemoveBedtime(),
    StreamingAddDownload(),
    StreamingRemoveOscars(),
    StreamingAddGeoRestriction(),
    StreamingAddTrialTier(),
    StreamingAddAgeRating(),
    StreamingParentalControls(),
    StreamingMultidevice(),
    StreamingFullExpansion(),
]

for m in MUTATIONS:
    register(m)
