# IBM Course Registration Manual AITL Trace

This trace simulates the intended AutoCedar workflow for the IBM course
registration prose while bypassing the currently broken Stage 1 schema-packet
behavior. Codex acted as the reviewing oracle and manually compared each
modeling decision against the provided requirements.

## Source

Input intent was provided directly in chat under:

- `IBM Course Registration Access Control Intent`

Manual AITL workspace:

- `experiments/rede_autocedar/ibm_course_manual_aitl/`

## Procedure

1. Read the IBM course-registration prose as the human reviewer.
2. Separated authorization intent from informational workflow details.
3. Built a schema with explicit lifecycle, ownership, professor-assignment, and
   campus-LAN hooks.
4. Wrote reviewed floor/ceiling/liveness targets as Cedar references.
5. Wrote a candidate Cedar policy store.
6. Validated the schema, candidate, and every reference with `cedar validate`.
7. Ran AutoCedar verification with `uv run autocedar verify`.

## Stage 1: Reviewed Schema Decisions

Approved principal model:

- `User.role: String`
  - Compact roles: `student`, `professor`, `registrar`.
  - This is acceptable for this trace because the prose does not require role
    intersection behavior.

Approved resources:

- `CourseCatalogue`
  - Contains `semesterIsBeginning` for the catalogue-request window.
- `CourseOffering`
  - Contains current/upcoming semester flags, registration/add-drop lifecycle,
    eligible professors, optional instructor, and conflict flag.
- `CourseSelection`
  - Represents a student's selected course offering.
  - Contains `student`, `offering`, and `isCurrentSelection`.
- `ReportCard`
  - Represents a student's report card for a completed semester.
- `GradeRecord`
  - Represents a grade a professor enters for a student in a completed class.
- `StudentInfo`
  - Represents registrar-editable student information.
- `RegistrationProcess`
  - Represents the current registration process that the registrar can close.

Approved context hooks:

- `context.onCampusLan`
  - Applied to student-facing catalogue, registration, add/drop, and report-card
    actions because the prose says students use personal computers attached to
    the campus LAN.

Rejected / not modeled as schema intent:

- Course catalogue informational fields such as professor, department, and
  prerequisites.
- Mechanics of retrieving a class roster.
- Grade value domain `A/B/C/D/F/I`.

Reason: these facts are important application data, but they are not needed to
express the authorization boundaries selected for this trace.

## Stage 2: Reviewed Property Target

The approved target uses ceilings for every important excess-access boundary and
floors for the primary required workflows.

Ceilings:

1. `catalogue_ceiling`
   - Students may request catalogues only from the campus LAN at semester start.
2. `register_course_ceiling`
   - Students may register only for their own current-semester selections while
     registration is open.
3. `add_course_ceiling`
   - Students may add only their own current selections during add/drop while
     registration is open.
4. `update_course_ceiling`
   - Same boundary as add, for updates.
5. `delete_course_ceiling`
   - Same boundary as add, for deletes.
6. `report_card_ceiling`
   - Students may view only their own previous-semester report cards from the
     campus LAN.
7. `select_teaching_ceiling`
   - Professors may select only eligible upcoming offerings, before registration
     closes, when there is no conflict.
8. `modify_assigned_offering_ceiling`
   - Professors may modify only their own assigned offerings while registration
     is open.
9. `view_roster_ceiling`
   - Professors may view rosters only for offerings they teach.
10. `enter_grade_ceiling`
    - Only the professor for a completed previous-semester class may enter
      grades.
11. `student_info_ceiling`
    - Only the registrar may change student information.
12. `close_registration_ceiling`
    - Only the registrar may close current registration.

Floors:

1. `register_course_floor`
   - Students must be able to register for their own current-semester offering
     while registration is open.
2. `add_course_floor`
   - Students must be able to add their own current selections during add/drop.
3. `report_card_floor`
   - Students must be able to view their own previous-semester report cards.
4. `select_teaching_floor`
   - Eligible professors must be able to select conflict-free upcoming offerings
     before registration closes.
5. `enter_grade_floor`
   - Professors must be able to enter grades for their completed classes.
6. `registrar_close_floor`
   - Registrar must be able to close current registration.

Liveness:

1. `liveness_register`
2. `liveness_enter_grade`
3. `liveness_close_registration`

Note: AutoCedar's current liveness check is broad `not always-denies` for an
action/resource/principal type. The floors above are the stronger targeted
existential checks for the important workflows. AutoCedar should upgrade
liveness to explicit probe-overlap checks.

## Stage 3: Candidate Policy

Candidate:

- `candidate.cedar`

The policy contains one compact permit branch per workflow family. It avoids
broad role grants and encodes the post-registration denial behavior by requiring
`registrationOpen` / `addDropOpen` in student and professor modification paths.

## Verification Commands

Schema/candidate validation:

```bash
cedar validate \
  --schema experiments/rede_autocedar/ibm_course_manual_aitl/schema.cedarschema \
  --policies experiments/rede_autocedar/ibm_course_manual_aitl/candidate.cedar
```

Reference validation:

```bash
for f in experiments/rede_autocedar/ibm_course_manual_aitl/references/*.cedar; do
  cedar validate \
    --schema experiments/rede_autocedar/ibm_course_manual_aitl/schema.cedarschema \
    --policies "$f"
done
```

Full target verification:

```bash
uv run autocedar verify experiments/rede_autocedar/ibm_course_manual_aitl
```

Result:

```text
loss: 0
```

All 21 checks passed:

- 12 ceilings
- 6 floors
- 3 liveness checks

## Issues Encountered

1. LAN boundary is a semantic choice that must be surfaced.
   - The prose explicitly mentions students using personal computers attached to
     the campus LAN.
   - I applied `context.onCampusLan` to student-facing actions.
   - I did not apply it to professor/registrar actions because the provided text
     does not state that same condition for them.
   - AutoCedar should ask or surface this as an intent decision instead of
     silently applying LAN globally.

2. "Current semester", "upcoming semester", "previous semester", and
   "registration closed" require schema hooks.
   - The correct schema needs lifecycle/status fields before the policy can be
     expressed.
   - This is exactly the class of schema support AutoCedar should detect during
     property proposal.

3. The professor-selection rule combines three boundaries.
   - Eligibility.
   - No conflict.
   - Registration not closed.
   - AutoCedar should not split these into a floor that omits one boundary and a
     ceiling that later contradicts it.

4. Student schedule ownership is central.
   - The policy must require `resource.student == principal` for registration
     and add/drop actions.
   - This is the main anti-scope-creep boundary for student actions.

5. Professor ownership is central.
   - The policy must require `resource.instructor == principal` for modifying
     assigned offerings and viewing rosters.
   - This directly captures "professors from modifying assigned course offerings
     for other professors."

6. Grade sensitivity has two different aspects.
   - Students view their own report cards.
   - Professors enter grades only for their completed classes.
   - AutoCedar should keep these separate instead of modeling "grades" as a
     generic readable/writable resource.

7. Current liveness machinery is weaker than the target.
   - The broad `always-denies` liveness checks passed.
   - For paper-quality claims, liveness should be compiled as probe overlap:
     `candidate ∩ liveness_probe != empty`.

