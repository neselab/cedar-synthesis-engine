"""Clinical trial platform mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor). Documents
belong to Projects. Project attributes (status, managingDepartment)
are denormalized onto Document for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher** or **PrincipalInvestigator**
  role may View or Edit documents. All other users are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- This forbid overrides all permit rules.

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block
  (via an `unless` clause on the forbid rule). GlobalAuditors may access
  documents outside their department, provided they otherwise qualify
  under the permit rules.

## Notes
- Roles are checked via entity group membership: `principal in Role::"ClinicalResearcher"`.
- Cedar denies by default; no explicit deny-all policy is needed.
- The forbid/unless pattern is the key complexity driver in this scenario.
"""


# -- Helpers -------------------------------------------------------------------

def _clinical_base_schema() -> str:
    """The base Clinical Trial schema."""
    return """\
// Clinical Trial Data Platform -- Cedar Schema
//
// Design note: Cedar cannot traverse entity hierarchies to access
// parent attributes (e.g., no resource.parent.status). To reference
// Project attributes in policies, projectStatus and projectManagingDepartment
// are denormalized onto Document. The application ensures these stay in sync.

entity Role;

entity User in [Role] {
    department: String,
    clearanceLevel: Long,
};

entity Project {
    status: String,
    managingDepartment: String,
};

entity Document in [Project] {
    classification: String,
    projectStatus: String,
    projectManagingDepartment: String,
};

action "View" appliesTo {
    principal: [User],
    resource: [Document],
    context: {
        networkRiskScore: Long,
        isCompliantDevice: Bool,
    },
};

action "Edit" appliesTo {
    principal: [User],
    resource: [Document],
    context: {
        networkRiskScore: Long,
        isCompliantDevice: Bool,
    },
};
"""


# -- Easy Mutations ------------------------------------------------------------

class ClinicalRemoveAuditor(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_remove_auditor",
            base_scenario="clinical",
            difficulty="easy",
            description="Remove GlobalAuditor loophole; strict department matching with no exceptions",
            operators=["P3", "P8"],
            features_tested=["remove_unless", "strict_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        spec = """\
# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator). Documents belong to Projects.
Project attributes (status, managingDepartment) are denormalized onto
Document for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher** or **PrincipalInvestigator**
  role may View or Edit documents. All other users are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- This forbid overrides all permit rules.
- There are NO exceptions to this rule. Even GlobalAuditors are blocked
  by department mismatch.

## Notes
- Roles are checked via entity group membership: `principal in Role::"ClinicalResearcher"`.
- Cedar denies by default; no explicit deny-all policy is needed.
- The GlobalAuditor loophole has been removed. The forbid rule has no `unless` clause.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalAddExport(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_add_export",
            base_scenario="clinical",
            difficulty="easy",
            description="Add Export action; same as View but additionally requires isCompliantDevice for all roles",
            operators=["S7", "P2", "P5"],
            features_tested=["new_action", "universal_constraint"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        schema = schema_ops.add_action(schema, """\
action "Export" appliesTo {
    principal: [User],
    resource: [Document],
    context: {
        networkRiskScore: Long,
        isCompliantDevice: Bool,
    },
};""")
        spec = _BASE_SPEC + """\
### 7. Export Action
- A new **Export** action is available on Documents.
- Export follows the same constraints as View (active project gate,
  role gate, clinical researcher constraints, PI constraints, and
  cross-departmental block with auditor loophole).
- **Additionally**, Export requires `context.isCompliantDevice == true`
  for ALL roles (not just PrincipalInvestigator). A ClinicalResearcher
  who would normally only need clearanceLevel > 3 and non-HighlyRestricted
  classification must ALSO be on a compliant device to Export.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalRelaxClearance(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_relax_clearance",
            base_scenario="clinical",
            difficulty="easy",
            description="Change clearanceLevel > 3 to >= 3; tests numeric boundary precision",
            operators=["P7"],
            features_tested=["numeric_boundary", "operator_change"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        spec = _BASE_SPEC.replace(
            "  - `principal.clearanceLevel > 3`, AND",
            "  - `principal.clearanceLevel >= 3`, AND",
        )
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class ClinicalAddDataManager(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_add_datamanager",
            base_scenario="clinical",
            difficulty="medium",
            description="Add DataManager role; can Edit HighlyRestricted docs if clearanceLevel > 5",
            operators=["S9", "P2", "P5"],
            features_tested=["new_role", "classification_access", "third_path"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        spec = _BASE_SPEC.replace(
            """\
### 2. Role Gate
- Only users in the **ClinicalResearcher** or **PrincipalInvestigator**
  role may View or Edit documents. All other users are denied by default.""",
            """\
### 2. Role Gate
- Only users in the **ClinicalResearcher**, **PrincipalInvestigator**,
  or **DataManager** role may View or Edit documents. All other users
  are denied by default.""",
        )
        spec += """\
### 7. DataManager Constraints
- A **DataManager** is a new role (checked via `principal in Role::"DataManager"`).
- A DataManager may **Edit** documents (including `"HighlyRestricted"` classification)
  only if `principal.clearanceLevel > 5`.
- A DataManager may also **View** documents under the same clearance constraint.
- DataManagers are still subject to the active project gate (requirement 1)
  and the cross-departmental block with auditor loophole (requirements 5 and 6).
- Unlike ClinicalResearchers, DataManagers CAN access HighlyRestricted documents
  (provided their clearanceLevel > 5).
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalAddStudyPhase(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_add_study_phase",
            base_scenario="clinical",
            difficulty="medium",
            description="Add studyPhase to Document; Phase-3 docs restricted to PrincipalInvestigator only",
            operators=["S1", "P1", "P5"],
            features_tested=["string_guard", "role_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        schema = schema_ops.add_attribute(schema, "Document", "studyPhase", "String")
        spec = _BASE_SPEC + """\
### 7. Study Phase Restriction
- Documents now have a `studyPhase` attribute (e.g., `"Phase-1"`, `"Phase-2"`, `"Phase-3"`).
- Documents with `studyPhase == "Phase-3"` may ONLY be accessed (View or Edit)
  by users in the **PrincipalInvestigator** role.
- ClinicalResearchers are blocked from Phase-3 documents even if they
  otherwise satisfy all other constraints.
- Phase-1 and Phase-2 documents remain accessible to both ClinicalResearchers
  and PrincipalInvestigators under their normal constraints.
- The cross-departmental block and auditor loophole still apply to Phase-3
  documents.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalAddConsent(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_add_consent",
            base_scenario="clinical",
            difficulty="medium",
            description="Add hasPatientConsent to context; forbid Edit without consent, View still allowed",
            operators=["S5", "P1"],
            features_tested=["context_guard", "action_specific_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        # Add hasPatientConsent to both View and Edit context blocks
        schema = schema_ops.add_context_field(schema, "View", "hasPatientConsent", "Bool")
        schema = schema_ops.add_context_field(schema, "Edit", "hasPatientConsent", "Bool")
        spec = _BASE_SPEC + """\
### 7. Patient Consent Requirement
- A new context field `hasPatientConsent: Bool` is added to both View
  and Edit actions.
- **Forbid** the **Edit** action if `context.hasPatientConsent == false`.
  Editing patient data without recorded consent is always denied.
- The **View** action is NOT affected by consent status. Users may
  view documents regardless of consent.
- This forbid has no exceptions -- it applies to all roles, including
  PrincipalInvestigators and GlobalAuditors.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalDualForbid(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_dual_forbid",
            base_scenario="clinical",
            difficulty="medium",
            description="Add second forbid: HighlyRestricted on non-compliant devices forbidden; auditor exempt from dept block but NOT device check",
            operators=["P1", "P1", "P4"],
            features_tested=["multi_forbid", "selective_exemption"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        spec = """\
# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor). Documents
belong to Projects. Project attributes (status, managingDepartment)
are denormalized onto Document for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher** or **PrincipalInvestigator**
  role may View or Edit documents. All other users are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- This forbid overrides all permit rules.
- **Exception**: GlobalAuditors (`principal in Role::"GlobalAuditor"`) are
  exempt from this block via an `unless` clause.

### 6. Device Compliance Block for Highly Restricted Documents (Forbid)
- **Forbid** any View or Edit of documents with
  `resource.classification == "HighlyRestricted"` if
  `context.isCompliantDevice != true` (i.e., the device is non-compliant).
- This forbid has NO exceptions. Even GlobalAuditors must use a
  compliant device to access HighlyRestricted documents.

## Notes
- There are TWO independent forbid rules in this scenario.
- The GlobalAuditor is exempt from the cross-departmental block (requirement 5)
  but is NOT exempt from the device compliance block (requirement 6).
- This tests correct handling of multiple forbid rules with different exemption scopes.
- Cedar denies by default; no explicit deny-all policy is needed.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class ClinicalAddSponsor(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_add_sponsor",
            base_scenario="clinical",
            difficulty="hard",
            description="Add SponsorRepresentative role; can View (not Edit) cross-department but only Active Phase-3",
            operators=["S1", "S9", "P2", "P4", "P5"],
            features_tested=["new_role", "action_restriction", "cross_dept_exception", "multi_condition"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        schema = schema_ops.add_attribute(schema, "Document", "studyPhase", "String")
        spec = """\
# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor,
SponsorRepresentative). Documents belong to Projects. Project attributes
(status, managingDepartment) are denormalized onto Document for policy
evaluation. Documents also have a `studyPhase` attribute.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher**, **PrincipalInvestigator**,
  or **SponsorRepresentative** role may access documents. All other
  users are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- This forbid overrides all permit rules.
- **Exception**: GlobalAuditors (`principal in Role::"GlobalAuditor"`) are
  exempt from this block via an `unless` clause.
- **Exception**: SponsorRepresentatives are also exempt from this block,
  but ONLY for the **View** action (see requirement 7).

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block
  for both View and Edit actions.

### 7. SponsorRepresentative Constraints
- A **SponsorRepresentative** is a new role
  (checked via `principal in Role::"SponsorRepresentative"`).
- A SponsorRepresentative may **View** documents only. They may NOT **Edit**.
- SponsorRepresentatives are exempt from the cross-departmental block
  for View only. They can view documents from any department.
- SponsorRepresentatives may ONLY view documents where
  `resource.studyPhase == "Phase-3"`. Phase-1 and Phase-2 documents
  are not accessible to them.
- SponsorRepresentatives are still subject to the active project gate.

## Notes
- Three roles now provide View access via different paths: ClinicalResearcher
  (clearance + classification), PrincipalInvestigator (network + device),
  and SponsorRepresentative (Phase-3 only, View only, cross-dept exempt).
- The cross-departmental forbid now has TWO exception paths: GlobalAuditor
  (all actions) and SponsorRepresentative (View only).
- Cedar denies by default; no explicit deny-all policy is needed.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalTemporalEmbargo(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_temporal_embargo",
            base_scenario="clinical",
            difficulty="hard",
            description="Add embargoUntil datetime to Document, requestTime datetime to context; forbid access before embargo except PI",
            operators=["S2", "S5", "P1", "P4", "P10"],
            features_tested=["datetime", "temporal_constraint", "forbid_with_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Build schema with datetime fields added
        schema = _clinical_base_schema()
        schema = schema_ops.add_attribute(schema, "Document", "embargoUntil", "Long")
        schema = schema_ops.add_context_field(schema, "View", "requestTime", "Long")
        schema = schema_ops.add_context_field(schema, "Edit", "requestTime", "Long")
        spec = _BASE_SPEC + """\
### 7. Temporal Embargo (Forbid with Exception)
- Documents now have an `embargoUntil` attribute (Long, representing a
  Unix epoch timestamp).
- A new context field `requestTime` (Long, Unix epoch timestamp) is added
  to both View and Edit actions.
- **Forbid** any View or Edit if `context.requestTime < resource.embargoUntil`
  (i.e., the request is made before the embargo lifts).
- **Exception**: PrincipalInvestigators (`principal in Role::"PrincipalInvestigator"`)
  are exempt from this embargo via an `unless` clause. PIs can access
  embargoed documents early.
- This forbid is independent of the cross-departmental block. Both may
  apply simultaneously.

## Notes (Temporal Embargo)
- The embargo uses Long (integer) timestamps rather than a dedicated datetime
  type for Cedar compatibility.
- The embargo forbid uses a numeric less-than comparison on context vs resource.
- Two forbid rules now exist, each with different `unless` exceptions:
  cross-dept block (unless GlobalAuditor) and embargo (unless PI).
"""
        return MutationResult(schema=schema, policy_spec=spec)


class ClinicalFullExpansion(Mutation):
    def meta(self):
        return MutationMeta(
            id="clinical_full_expansion",
            base_scenario="clinical",
            difficulty="hard",
            description="DataManager + study phase + consent + device forbid for HighlyRestricted; four simultaneous constraints",
            operators=["S1", "S5", "S9", "P1", "P1", "P2", "P5"],
            features_tested=["multi_mutation", "complexity", "multi_forbid", "new_role"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _clinical_base_schema()
        # Add studyPhase to Document
        schema = schema_ops.add_attribute(schema, "Document", "studyPhase", "String")
        # Add hasPatientConsent to both action contexts
        schema = schema_ops.add_context_field(schema, "View", "hasPatientConsent", "Bool")
        schema = schema_ops.add_context_field(schema, "Edit", "hasPatientConsent", "Bool")
        spec = """\
# Clinical Trial Data Platform -- Policy Specification (Full Expansion)

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor, DataManager).
Documents belong to Projects and have a `studyPhase` attribute. Project
attributes (status, managingDepartment) are denormalized onto Document
for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher**, **PrincipalInvestigator**,
  or **DataManager** role may View or Edit documents. All other users
  are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- **Exception**: GlobalAuditors are exempt via an `unless` clause.

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block.

### 7. DataManager Role
- A **DataManager** (checked via `principal in Role::"DataManager"`)
  may View and Edit documents (including `"HighlyRestricted"` classification)
  only if `principal.clearanceLevel > 5`.
- DataManagers are subject to the active project gate and the
  cross-departmental block with auditor loophole.

### 8. Study Phase Restriction
- Documents with `studyPhase == "Phase-3"` may ONLY be accessed by
  **PrincipalInvestigator** or **DataManager** roles.
- ClinicalResearchers are blocked from Phase-3 documents even if they
  otherwise satisfy all other constraints.

### 9. Patient Consent Requirement (Forbid)
- **Forbid** the **Edit** action if `context.hasPatientConsent == false`.
- View is NOT affected by consent status.
- This forbid has NO exceptions -- it applies to all roles.

### 10. Device Compliance Block for Highly Restricted Documents (Forbid)
- **Forbid** any View or Edit of documents with
  `resource.classification == "HighlyRestricted"` if
  `context.isCompliantDevice != true`.
- This forbid has NO exceptions. Even GlobalAuditors must use a
  compliant device to access HighlyRestricted documents.

## Notes
- This is the most complex variant with THREE forbid rules:
  1. Cross-departmental block (unless GlobalAuditor)
  2. Consent block on Edit (no exceptions)
  3. Device compliance block on HighlyRestricted (no exceptions)
- Three roles provide access via different paths: ClinicalResearcher
  (clearance + classification), PrincipalInvestigator (network + device),
  DataManager (high clearance, can access HighlyRestricted).
- Phase-3 restriction further limits ClinicalResearcher access.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    ClinicalRemoveAuditor(),
    ClinicalAddExport(),
    ClinicalRelaxClearance(),
    ClinicalAddDataManager(),
    ClinicalAddStudyPhase(),
    ClinicalAddConsent(),
    ClinicalDualForbid(),
    ClinicalAddSponsor(),
    ClinicalTemporalEmbargo(),
    ClinicalFullExpansion(),
]

for m in MUTATIONS:
    register(m)
