"""Document Cloud permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

## Requirements

### 1. Owner Permissions
- The **owner** of a document may perform ALL actions on that document:
  ViewDocument, ModifyDocument, DeleteDocument, EditIsPrivate, EditPublicAccess,
  AddToShareACL.

### 2. View ACL Permissions
- A user who is in a document's **viewACL** may **ViewDocument**.

### 3. Modify ACL Permissions
- A user who is in a document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL Permissions
- A user who is in a document's **manageACL** may perform:
  **AddToShareACL**, **DeleteDocument**, **EditIsPrivate**, **EditPublicAccess**.

### 5. Public Access Rules
- If a document's `publicAccess == "view"`, then **Public** principals (or any
  authenticated user) may **ViewDocument**.
- If a document's `publicAccess == "edit"`, then **Public** principals may
  **ViewDocument** and **ModifyDocument**.

### 6. Blocking Rules (Deny Rules -- Bidirectional)
- If the **principal** is in the document owner's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- If the document **owner** is in the principal's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- Blocking is bidirectional: either direction triggers the deny.

### 7. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- The Public entity type is a separate principal type, not a User.
- Cedar denies by default -- no explicit deny-by-default policy is needed.
- Blocking forbid rules use `when` conditions on entity attribute sets.
"""


# -- Helpers -------------------------------------------------------------------

def _doccloud_base_schema() -> str:
    """The base Document Cloud schema."""
    return """\
// Document Cloud Permissions -- Cedar Schema

entity DocumentShare, Drive;
entity Document = {
    "isPrivate": Bool,
    "manageACL": DocumentShare,
    "modifyACL": DocumentShare,
    "owner": User,
    "publicAccess": String,
    "viewACL": DocumentShare,
};
entity Group in [DocumentShare] = {
    "owner": User,
};
entity Public in [DocumentShare];
entity User in [Group] = {
    "blocked": Set<User>,
    "personalGroup": Group,
};

action DeleteGroup, ModifyGroup appliesTo {
    principal: [User],
    resource: [Group],
    context: { "is_authenticated": Bool }
};
action CreateGroup appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
action ViewDocument appliesTo {
    principal: [User, Public],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action ModifyDocument appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action CreateDocument appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
"""


# -- Easy Mutations ------------------------------------------------------------

class DocCloudRemoveBlocking(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_remove_blocking",
            base_scenario="doccloud",
            difficulty="easy",
            description="Remove the blocked attribute from User and all blocking forbid rules",
            operators=["S10", "P3"],
            features_tested=["attribute_removal", "forbid_removal"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_attribute(base_schema, "User", '"blocked"')
        spec = """\
# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

## Requirements

### 1. Owner Permissions
- The **owner** of a document may perform ALL actions on that document:
  ViewDocument, ModifyDocument, DeleteDocument, EditIsPrivate, EditPublicAccess,
  AddToShareACL.

### 2. View ACL Permissions
- A user who is in a document's **viewACL** may **ViewDocument**.

### 3. Modify ACL Permissions
- A user who is in a document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL Permissions
- A user who is in a document's **manageACL** may perform:
  **AddToShareACL**, **DeleteDocument**, **EditIsPrivate**, **EditPublicAccess**.

### 5. Public Access Rules
- If a document's `publicAccess == "view"`, then **Public** principals (or any
  authenticated user) may **ViewDocument**.
- If a document's `publicAccess == "edit"`, then **Public** principals may
  **ViewDocument** and **ModifyDocument**.

### 6. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 7. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- There are NO blocking rules in this variant. Users cannot block each other.
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- The Public entity type is a separate principal type, not a User.
- Cedar denies by default -- no explicit deny-by-default policy is needed.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class DocCloudAddCommentACL(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_add_comment_acl",
            base_scenario="doccloud",
            difficulty="easy",
            description="Add commentACL to Document and CommentOnDocument action; viewers cannot comment",
            operators=["S1", "S7", "P2"],
            features_tested=["new_attribute", "new_action", "acl_pattern"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", '"commentACL"', "DocumentShare")
        schema = schema_ops.add_action(schema, """\
action CommentOnDocument appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool }
};""")
        spec = _BASE_SPEC + """\
### 9. Comment ACL Permissions
- A user who is in a document's **commentACL** may **CommentOnDocument**.
- Users who only have **ViewDocument** access (via viewACL or public access)
  may NOT comment -- commenting requires explicit commentACL membership.
- The document **owner** may also **CommentOnDocument** (owners can do everything).
- Manage ACL members may NOT comment unless they are also in commentACL or are the owner.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class DocCloudRemovePublic(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_remove_public",
            base_scenario="doccloud",
            difficulty="easy",
            description="Remove Public entity and all public access rules; only authenticated Users",
            operators=["S10", "P3", "P8"],
            features_tested=["entity_removal", "principal_narrowing"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Remove the Public entity
        schema = schema_ops.remove_entity(base_schema, "Public")
        # Remove Public from ViewDocument principal list
        schema = schema.replace(
            "principal: [User, Public],",
            "principal: [User],"
        )
        spec = """\
# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

In this variant, the Public entity type has been removed. Only authenticated
User principals can access documents. The publicAccess attribute on Document
is unused / has no effect on authorization.

## Requirements

### 1. Owner Permissions
- The **owner** of a document may perform ALL actions on that document:
  ViewDocument, ModifyDocument, DeleteDocument, EditIsPrivate, EditPublicAccess,
  AddToShareACL.

### 2. View ACL Permissions
- A user who is in a document's **viewACL** may **ViewDocument**.

### 3. Modify ACL Permissions
- A user who is in a document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL Permissions
- A user who is in a document's **manageACL** may perform:
  **AddToShareACL**, **DeleteDocument**, **EditIsPrivate**, **EditPublicAccess**.

### 5. Public Access (Disabled)
- There are NO public access rules. The `publicAccess` attribute has no effect.
- Only Users with explicit ACL membership or ownership can access documents.

### 6. Blocking Rules (Deny Rules -- Bidirectional)
- If the **principal** is in the document owner's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- If the document **owner** is in the principal's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.

### 7. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- There is no Public principal type in this variant.
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- Cedar denies by default -- no explicit deny-by-default policy is needed.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class DocCloudAddExpiry(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_add_expiry",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add expiryDate to Document; forbid all access (except owner DeleteDocument) after expiry",
            operators=["S2", "P1", "P4"],
            features_tested=["datetime_comparison", "forbid_with_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", '"expiryDate"', "Long")
        # Add currentTime to all action contexts that target Document
        # We write out the full schema to ensure clean context additions
        schema = """\
// Document Cloud Permissions -- Cedar Schema

entity DocumentShare, Drive;
entity Document = {
    "isPrivate": Bool,
    "manageACL": DocumentShare,
    "modifyACL": DocumentShare,
    "owner": User,
    "publicAccess": String,
    "viewACL": DocumentShare,
    "expiryDate": Long,
};
entity Group in [DocumentShare] = {
    "owner": User,
};
entity Public in [DocumentShare];
entity User in [Group] = {
    "blocked": Set<User>,
    "personalGroup": Group,
};

action DeleteGroup, ModifyGroup appliesTo {
    principal: [User],
    resource: [Group],
    context: { "is_authenticated": Bool }
};
action CreateGroup appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
action ViewDocument appliesTo {
    principal: [User, Public],
    resource: [Document],
    context: { "is_authenticated": Bool, "currentTime": Long }
};
action AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool, "currentTime": Long }
};
action ModifyDocument appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool, "currentTime": Long }
};
action CreateDocument appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
"""
        spec = _BASE_SPEC + """\
### 9. Document Expiry (Deny Rule with Exception)
- Documents have an `expiryDate` attribute (Long, representing epoch timestamp).
- The context includes `currentTime` (Long, epoch timestamp) for document actions.
- If `context.currentTime > resource.expiryDate`, forbid ALL actions on the document
  EXCEPT: the document **owner** may still **DeleteDocument** on expired documents.
- ViewDocument, ModifyDocument, AddToShareACL, EditIsPrivate, and EditPublicAccess
  are all blocked after expiry for non-owners.
- The owner retains DeleteDocument to allow cleanup of expired documents.

## Notes (Expiry)
- The expiry forbid must use an `unless` clause to exempt owner + DeleteDocument.
- `expiryDate` and `currentTime` are Long (epoch) for numeric comparison.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class DocCloudAddVersionLock(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_add_version_lock",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add isLocked boolean to Document; forbid ModifyDocument on locked docs; owner can still delete",
            operators=["S1", "P1"],
            features_tested=["boolean_guard", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", '"isLocked"', "Bool")
        spec = _BASE_SPEC + """\
### 9. Version Lock (Deny Rule)
- Documents have an `isLocked` boolean attribute.
- If `resource.isLocked == true`, forbid **ModifyDocument** for all users
  (including users in modifyACL and the document owner).
- **DeleteDocument** is still allowed on locked documents (the owner can delete).
- **ViewDocument** is still allowed on locked documents.
- **AddToShareACL**, **EditIsPrivate**, and **EditPublicAccess** are still allowed
  on locked documents (these are management actions, not content modification).
"""
        return MutationResult(schema=schema, policy_spec=spec)


class DocCloudAddAdminGroup(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_add_admin_group",
            base_scenario="doccloud",
            difficulty="medium",
            description="manageACL members bypass blocking rules (unless exception on blocking forbid)",
            operators=["P4"],
            features_tested=["unless_exception", "forbid_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        spec = """\
# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

## Requirements

### 1. Owner Permissions
- The **owner** of a document may perform ALL actions on that document:
  ViewDocument, ModifyDocument, DeleteDocument, EditIsPrivate, EditPublicAccess,
  AddToShareACL.

### 2. View ACL Permissions
- A user who is in a document's **viewACL** may **ViewDocument**.

### 3. Modify ACL Permissions
- A user who is in a document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL Permissions
- A user who is in a document's **manageACL** may perform:
  **AddToShareACL**, **DeleteDocument**, **EditIsPrivate**, **EditPublicAccess**.

### 5. Public Access Rules
- If a document's `publicAccess == "view"`, then **Public** principals (or any
  authenticated user) may **ViewDocument**.
- If a document's `publicAccess == "edit"`, then **Public** principals may
  **ViewDocument** and **ModifyDocument**.

### 6. Blocking Rules (Deny Rules -- Bidirectional, with Exception)
- If the **principal** is in the document owner's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- If the document **owner** is in the principal's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- **Exception**: Users who are in the document's **manageACL** bypass the
  blocking rules. They can ViewDocument and ModifyDocument even if blocking
  would otherwise apply.
- The blocking forbid rules must use an `unless` clause:
  `unless { principal in resource.manageACL }`.

### 7. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- The manageACL bypass creates a forbid/unless interaction for blocking rules.
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- The Public entity type is a separate principal type, not a User.
- Cedar denies by default -- no explicit deny-by-default policy is needed.
"""
        # Schema is unchanged -- only the policy interpretation changes
        return MutationResult(schema=base_schema, policy_spec=spec)


class DocCloudGraduatedSharing(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_graduated_sharing",
            base_scenario="doccloud",
            difficulty="medium",
            description='Add "preview" publicAccess option and ViewMetadata action; preview allows metadata only',
            operators=["S7", "P2", "P7"],
            features_tested=["new_action", "string_enum", "fine_grained_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_action(base_schema, """\
action ViewMetadata appliesTo {
    principal: [User, Public],
    resource: [Document],
    context: { "is_authenticated": Bool }
};""")
        spec = _BASE_SPEC + """\
### 9. Graduated Public Sharing
- The `publicAccess` attribute now supports three values: `"view"`, `"edit"`,
  and `"preview"`.
- If `publicAccess == "preview"`, **Public** principals may **ViewMetadata** only.
  They may NOT **ViewDocument** (which grants full content access).
- If `publicAccess == "view"`, **Public** principals may **ViewDocument** and
  **ViewMetadata**.
- If `publicAccess == "edit"`, **Public** principals may **ViewDocument**,
  **ViewMetadata**, and **ModifyDocument**.

### 10. ViewMetadata Action
- **ViewMetadata** is a new action that allows viewing document metadata
  (title, owner, dates) without viewing the full document content.
- Any user who can **ViewDocument** can also **ViewMetadata** (ViewDocument
  implies ViewMetadata).
- The document **owner** may **ViewMetadata** (owners can do everything).
- Users in **viewACL**, **modifyACL**, or **manageACL** may **ViewMetadata**.

## Notes (Graduated Sharing)
- Three levels of public access: preview (metadata only) < view (full) < edit (full + modify).
- ViewMetadata is strictly weaker than ViewDocument.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class DocCloudTemporalSharing(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_temporal_sharing",
            base_scenario="doccloud",
            difficulty="hard",
            description="ACL-based access expires after shareExpiry; owner access persists; plus version lock",
            operators=["S2", "S1", "P1", "P1", "P4"],
            features_tested=["datetime_comparison", "multi_forbid", "owner_exception", "boolean_guard"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Full schema rewrite for clean context fields and new attributes
        schema = """\
// Document Cloud Permissions -- Cedar Schema

entity DocumentShare, Drive;
entity Document = {
    "isPrivate": Bool,
    "manageACL": DocumentShare,
    "modifyACL": DocumentShare,
    "owner": User,
    "publicAccess": String,
    "viewACL": DocumentShare,
    "shareExpiry": Long,
    "isLocked": Bool,
};
entity Group in [DocumentShare] = {
    "owner": User,
};
entity Public in [DocumentShare];
entity User in [Group] = {
    "blocked": Set<User>,
    "personalGroup": Group,
};

action DeleteGroup, ModifyGroup appliesTo {
    principal: [User],
    resource: [Group],
    context: { "is_authenticated": Bool }
};
action CreateGroup appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
action ViewDocument appliesTo {
    principal: [User, Public],
    resource: [Document],
    context: { "is_authenticated": Bool, "requestTime": Long }
};
action AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool, "requestTime": Long }
};
action ModifyDocument appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool, "requestTime": Long }
};
action CreateDocument appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
"""
        spec = _BASE_SPEC + """\
### 9. Temporal Sharing (Deny Rule with Owner Exception)
- Documents have a `shareExpiry` attribute (Long, epoch timestamp).
- The context includes `requestTime` (Long, epoch timestamp) for document actions.
- If `context.requestTime > resource.shareExpiry`, ACL-based access is revoked:
  forbid **ViewDocument**, **ModifyDocument**, **AddToShareACL**,
  **EditIsPrivate**, **EditPublicAccess** for users accessing via ACLs.
- **Exception**: The document **owner** is NOT affected by share expiry.
  The owner retains full access (all actions) regardless of shareExpiry.
- **Exception**: **DeleteDocument** by the owner is always allowed.
- Public access rules are also affected by share expiry -- if shares have
  expired, public access is revoked.

### 10. Version Lock (Deny Rule)
- Documents have an `isLocked` boolean attribute.
- If `resource.isLocked == true`, forbid **ModifyDocument** for ALL users
  (including the owner and users in modifyACL).
- **DeleteDocument** is still allowed on locked documents.
- **ViewDocument** and management actions (AddToShareACL, EditIsPrivate,
  EditPublicAccess) are still allowed on locked documents.

## Notes (Temporal Sharing + Version Lock)
- Two independent forbid rules interact: share expiry and version lock.
- The share expiry forbid must use `unless { principal == resource.owner }`.
- The version lock forbid applies universally with no exceptions.
- A locked, expired document: owner can view/delete but not modify;
  non-owners cannot access at all.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class DocCloudOrgIsolation(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_org_isolation",
            base_scenario="doccloud",
            difficulty="hard",
            description="Add Organization entity; forbid cross-org document access; manageACL can share cross-org",
            operators=["S6", "S1", "P1", "P4"],
            features_tested=["new_entity", "cross_entity_comparison", "forbid_with_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Full schema rewrite for Organization support
        schema = """\
// Document Cloud Permissions -- Cedar Schema

entity DocumentShare, Drive;
entity Organization;
entity Document = {
    "isPrivate": Bool,
    "manageACL": DocumentShare,
    "modifyACL": DocumentShare,
    "owner": User,
    "publicAccess": String,
    "viewACL": DocumentShare,
};
entity Group in [DocumentShare] = {
    "owner": User,
};
entity Public in [DocumentShare];
entity User in [Group] = {
    "blocked": Set<User>,
    "personalGroup": Group,
    "org": Organization,
};

action DeleteGroup, ModifyGroup appliesTo {
    principal: [User],
    resource: [Group],
    context: { "is_authenticated": Bool }
};
action CreateGroup appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
action ViewDocument appliesTo {
    principal: [User, Public],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action ModifyDocument appliesTo {
    principal: [User],
    resource: [Document],
    context: { "is_authenticated": Bool }
};
action CreateDocument appliesTo {
    principal: [User],
    resource: [Drive],
    context: { "is_authenticated": Bool }
};
"""
        spec = _BASE_SPEC + """\
### 9. Organization Isolation (Deny Rule with Exception)
- Users have an `org` attribute referencing an **Organization** entity.
- Document owners also have an `org` attribute (accessed via `resource.owner.org`).
- **Forbid** all document actions (ViewDocument, ModifyDocument, DeleteDocument,
  EditIsPrivate, EditPublicAccess, AddToShareACL) when the principal's org
  does not match the document owner's org:
  `when { principal.org != resource.owner.org }`.
- **Exception**: Users who are in the document's **manageACL** bypass the
  organization isolation rule. They can access documents cross-org.
  The forbid uses: `unless { principal in resource.manageACL }`.
- Public access rules are unaffected by org isolation (Public is not a User
  and has no org attribute).
- The document **owner** always passes the org check (same org as themselves).

## Notes (Organization Isolation)
- Cross-entity comparison: `principal.org != resource.owner.org` requires
  traversing principal -> org and resource -> owner -> org.
- The manageACL exception allows designated cross-org collaborators.
- Org isolation stacks with blocking rules -- both may independently forbid access.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    DocCloudRemoveBlocking(),
    DocCloudAddCommentACL(),
    DocCloudRemovePublic(),
    DocCloudAddExpiry(),
    DocCloudAddVersionLock(),
    DocCloudAddAdminGroup(),
    DocCloudGraduatedSharing(),
    DocCloudTemporalSharing(),
    DocCloudOrgIsolation(),
]

for m in MUTATIONS:
    register(m)
