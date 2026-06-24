# REDE to AutoCedar Handoff

This document explains how to run the REDE AccessControlModelStudy experiment
with AutoCedar. It is written for a knowledge worker who needs exact files, exact
stages, and the research reason behind the work.

## 1. What We Are Trying To Show

AutoCedar is a human-in-the-loop system for converting access-control intent
into deployable Cedar policies. Cedar policies can be used in production
authorization systems, but real projects rarely begin with Cedar. They begin
with prose requirements, use cases, and natural-language access-control policy
statements.

REDE gives us exactly that upstream material:

- Full access-control scenario descriptions.
- Natural-language access-control policies (NLACP).
- Subject/action/resource triples for many policy sentences.
- CRUD labels and negation markers such as `NEG-not`, `NEG-prevent`, and
  `ONLY-only`.

REDE does **not** give finished Cedar schemas or Cedar policies. That is the
point of the experiment. We want to show that AutoCedar can bridge the gap:

```text
REDE prose scenario + REDE NLACP policies
  -> AutoCedar schema atoms with human review
  -> AutoCedar policy/property atoms with human review
  -> Cedar schema + verification plan + reference policies
  -> synthesized Cedar candidate
  -> verified, deployable Cedar policy artifact
```

The paper value is that this is not another hand-written toy prompt. It is an
external requirements-engineering dataset being converted into formal,
intent-reviewed Cedar artifacts.

## 2. Where The Data Lives

Clone REDE outside this repo:

```bash
git clone https://github.com/RealsearchGroup/REDE.git /tmp/REDE
```

The root for this experiment is:

```text
/tmp/REDE/data/AccessControlModelStudy
```

In my local audit, the same directory was checked at:

```text
/tmp/autocedar_research/REDE/data/AccessControlModelStudy
```

Use your own clone path, but keep the internal relative paths exactly the same.

## 3. Important Rule: AutoCedar Uses Text, Not File References

Each REDE dataset has multiple source files:

- A scenario/problem-description file.
- A labeled NLACP policy file.
- Usually a JSON export.
- Usually an XLSX export.

AutoCedar does not currently crawl a REDE directory or dereference file paths
listed inside a prompt. It uses the natural-language text you give it.

There are two equivalent ways to give AutoCedar that text:

1. Save the exact authoring context as a `spec.md` file and run the CLI.
2. Paste the exact same authoring context into the AutoCedar TUI draft and say
   `author this`.

The CLI form is:

```bash
uv run autocedar author path/to/spec.md --out path/to/output-dir
```

The TUI form is:

```text
start a policy draft
<paste the authoring context>
author this
```

For every experiment run, give AutoCedar one curated authoring context. For
repeatability, save that exact context as `spec.md`; this is not an external
preprocessing format, just a durable copy of what AutoCedar saw.

This context must contain the actual text AutoCedar should reason over:

1. Dataset name and source file references for audit provenance.
2. The actual relevant scenario/problem description text.
3. The actual selected NLACP policy sentences/triples to formalize.
4. Instructions that AutoCedar must propose Cedar schema atoms first, then
   policy/property atoms, and that every atom must go through HITL review.

Important: file paths inside the authoring context are for provenance only. If
the context only says `ibm use case/IBM Course Registration.txt`, AutoCedar
treats that path as ordinary prose. It does not open the file or load hidden
context from it. The relevant excerpts must be pasted into the authoring
context.

Provenance means that a human auditor can later trace the copied text back to
the original REDE source file. It is for reproducibility, paper review, and
future debugging; it is not operational model context unless the source text is
also pasted.

Do not pass the raw XLSX or JSON directly to AutoCedar as the main spec. Use
them as evidence and labels.

## 4. AutoCedar Inputs And Outputs

### Input Context You Prepare

For each dataset or slice, prepare the exact text that AutoCedar should see.
If using the CLI, save it here:

```text
experiments/rede_autocedar/<dataset_slug>/spec.md
```

If using the TUI, paste the same text into the working draft. Either way,
AutoCedar receives the same content.

### Schema Mode

AutoCedar supports both schema modes:

1. **No schema supplied.** AutoCedar proposes schema atoms from the natural
   language context, pauses for HITL review, and writes
   `stage1/final_schema.cedarschema`.
2. **Existing schema supplied.** AutoCedar uses the provided schema and skips
   Stage 1 schema atomization.

For this REDE experiment, the default path should be no schema supplied. The
point is to show that AutoCedar can derive a Cedar schema from NLACP scenario
material with human review.

### CLI Command To Run

From the AutoCedar repo root:

```bash
uv run autocedar author \
  experiments/rede_autocedar/<dataset_slug>/spec.md \
  --out experiments/rede_autocedar/<dataset_slug>/runs \
  --session-id <dataset_slug>-001 \
  --effort high
```

### TUI Command To Run

If the TUI is preferred:

```bash
uv run autocedar
```

Then use natural language:

```text
start a policy draft
```

Paste the same curated authoring context, then say:

```text
author this
```

### Output AutoCedar Creates

For a session id like `ibm-course-registration-001`, inspect:

```text
experiments/rede_autocedar/ibm_course_registration/runs/ibm-course-registration-001/
```

Important files:

```text
input/<spec filename>                         # exact spec AutoCedar saw
stage1/proposed_atoms.json                    # proposed schema atoms
stage1/decisions.json                         # human schema review decisions
stage1/final_schema.cedarschema               # Cedar schema created by AutoCedar
stage2/proposed_atoms.json                    # proposed policy/property atoms
stage2/decisions.json                         # human property review decisions
stage2/symbolic_verification_logs.json        # symbolic verification notes
stage2/final_plan/verification_plan.py        # formal check plan
stage2/final_plan/references/*.cedar          # reference policies/bounds
stage3/final_candidate.cedar                  # synthesized Cedar policy
stage2_5/traceback.json                       # atom-to-policy trace
stage2_5/final_user_decision.json             # final user approval
transcript.json                               # session event log
```

The schema does not come from REDE. It is produced by AutoCedar in
`stage1/final_schema.cedarschema` after human review.

## 5. Dataset File Map

The AccessControlModelStudy has five labeled datasets. Treat them differently.

### 5.1 IBM Course Management

This is the best first end-to-end experiment.

Use for schema/problem description:

```text
ibm use case/IBM Course Registration.txt
```

Optional structured source:

```text
ibm use case/CourseRegistration 2.json
ibm use case/CourseRegistration_without_glossary_login.json
ibm use case/CourseRegistration.docx
```

Use for NLACP policy candidates:

```text
labelled data sets/IBM Course Management - ac rules.txt
labelled data sets/IBM Course Management.xlsx
```

Audit counts:

```text
401 sentence lines
169 access-control sentence lines
379 NLACP triples
35 empty-subject triples
CRUD counts: R=208, C=83, U=50, D=31, E=23
markers: NEG-not=3, NEG-prevent=1, ONLY-only=2
```

Why this is strong:

- It is a coherent production-like domain.
- It has a glossary with entities: `Course`, `Course Offering`, `Faculty`,
  `Finance System`, `Grade`, `Professor`, `Report Card`, `Roster`, `Student`,
  `Schedule`, `Transcript`.
- It has clear roles: `Student`, `Professor`, `Registrar`.
- It has clear authorization rules:
  - Students can register for courses and view report cards.
  - Professors can select course offerings to teach.
  - Professors can enter grades.
  - Only the Registrar can change student information.
  - Students cannot change schedules other than their own.
  - Professors cannot modify assigned course offerings for other professors.

Recommended first IBM slice:

1. Use the problem statement, glossary, and security section from
   `IBM Course Registration.txt`.
2. Add the NLACP policies around:
   - security block,
   - maintain professor information,
   - maintain student information,
   - register for courses,
   - select courses to teach,
   - submit grades,
   - view report card.
3. Do not try all 379 triples in the first run. Start with 20-40 important
   policies, then expand.

Likely schema atoms:

```text
User / Student / Professor / Registrar
Course
CourseOffering
Schedule
Grade
ReportCard
StudentInformation
ProfessorInformation
Semester
```

Likely relationships/attributes:

```text
Schedule.owner: Student
Schedule.semester: Semester
Schedule.selectedOfferings: Set<CourseOffering>
CourseOffering.course: Course
CourseOffering.instructor: Professor
CourseOffering.enrolledStudents: Set<Student>
CourseOffering.semester: Semester
Grade.student: Student
Grade.offering: CourseOffering
ReportCard.owner: Student
StudentInformation.subject: Student
ProfessorInformation.subject: Professor
Semester.registrationOpen: Bool
Semester.addDropOpen: Bool
```

Main human review questions:

- Should `Student`, `Professor`, and `Registrar` be separate entity types, or
  roles on one `User` entity?
- Should `Grade` be a separate resource or part of `ReportCard`?
- Should `registrationOpen` be context or a `Semester` attribute?
- Are `system`, `billing system`, and `course catalog system` authorization
  principals or implementation services to exclude?

### 5.2 iTrust for Text2Policy

This is the best first iTrust experiment because it is shorter and cleaner
than the full ACRE iTrust export.

Use for schema/problem description:

```text
Xiao Sources/iTrust for Text2Policy.txt
```

Optional structured source:

```text
Xiao Sources/iTrustUseCases.json
Xiao Sources/iTrustUseCases.doc
```

Use for NLACP policy candidates:

```text
labelled data sets/iTrust for Text2Policy.txt
labelled data sets/iTrust for Text2Policy.xlsx
```

Audit counts:

```text
471 sentence lines
418 access-control sentence lines
1070 NLACP triples
222 empty-subject triples
CRUD counts: R=742, C=229, U=72, D=27, E=20
markers: NEG-not=15, NEG-have=4
```

Why this is strong:

- It is a medical-records access-control domain.
- It has clear regulated-data motivation.
- It has roles like `HCP`, `LHCP`, `DLHCP`, `Patient`, `Administrator`,
  `Representative`, `UAP`, and `Public Health Agent`.
- It has natural access-control concepts: patient records, demographics,
  provider lists, access logs, appointments, messages, lab procedures.

Recommended first Text2Policy slice:

1. UC1: Create and Disable Patients.
2. UC2: Create, Disable, and Edit Personnel.
3. UC3: Authenticate Users.
4. UC6/UC8-style patient-provider/access-log flows.

Do not start with all 1070 triples. Start with 25-50 meaningful policies.

Likely schema atoms:

```text
User
Patient
HCP
LHCP
DLHCP
Administrator
Representative
UAP
MedicalRecord
DemographicInfo
ProviderDesignation
AccessLog
Appointment
Message
LabProcedure
```

Likely relationships/attributes:

```text
MedicalRecord.patient: Patient
ProviderDesignation.patient: Patient
ProviderDesignation.provider: LHCP
DemographicInfo.patient: Patient
AccessLog.patient: Patient
AccessLog.accessor: User
Message.sender: User
Message.recipient: User
Appointment.patient: Patient
Appointment.provider: HCP
```

Main human review questions:

- Is `DLHCP` a separate entity type, a role, or a relationship between patient
  and LHCP?
- Is `Representative` a role or a relationship to a patient?
- Which "system displays/presents" triples are real authorization policies?
- Which clinical data types deserve separate resources?

### 5.3 iTrust for ACRE

This is the largest and most valuable healthcare scenario, but it is too large
for the first pass.

Use for schema/problem description:

```text
iTrust/iTrust_requirements_UTF8.txt
```

Optional structured source:

```text
iTrust/itrust_full.json
iTrust/iTrust_requirements.docx
```

Use for NLACP policy candidates:

```text
labelled data sets/iTrust for ACRE - ac rules.txt
labelled data sets/iTrust for ACRE.xlsx
```

Audit counts:

```text
1160 sentence lines
549 access-control sentence lines
2270 NLACP triples
553 empty-subject triples
CRUD counts: R=1764, C=373, U=217, D=38, E=24
markers: NEG-not=16, NEG-exception=4, NEG-note=2, NEG-unable=2
```

Why this is strong:

- It has the richest schema material.
- It includes role definitions, medical data definitions, patient/provider
  relationships, and HIPAA-style motivation.
- It is closest to a real production access-control formalization case study.

Why it is hard:

- It is long.
- It has many UI/workflow triples that are not policy.
- It has many empty-subject triples.
- It requires careful modeling of medical roles and patient-specific consent.

Recommended first ACRE slice:

1. Use the introduction and glossary as the schema source.
2. Choose one small policy family:
   - patient record view/edit,
   - provider designation,
   - access log viewing,
   - demographic editing,
   - appointment/message access.
3. Keep the first run under 50 NLACP triples.

Do not attempt the full 2270 triples until we have a successful smaller
Text2Policy or IBM run.

### 5.4 CyberChair

CyberChair is a coherent conference-review domain, but the labels are noisy.
Use it after IBM.

Use for schema/problem description:

```text
CyberChair/CyberChair_source_document.txt
```

Shorter overview source:

```text
CyberChair/source_documents/overview.txt
```

Optional structured source:

```text
CyberChair/CyberChair_source_document.json
CyberChair/source_documents/overview.html
CyberChair/source_documents/CyberChair - wbgafprp .txt
CyberChair/source_documents/CyberChair - wbgafprp .pdf
```

Use for NLACP policy candidates:

```text
labelled data sets/CyberChair - ac rules.txt
labelled data sets/CyberChair.xlsx
```

Audit counts:

```text
303 sentence lines
139 access-control sentence lines
386 NLACP triples
187 empty-subject triples
CRUD counts: R=229, C=130, U=7, E=11
markers: none in text export
```

Why this is useful:

- It gives a non-healthcare/non-course-registration domain.
- It has clear actors: author, reviewer, chair/PCC, maintainer.
- It has clear resources: paper, abstract, review, assignment, preference,
  comment, proceedings.

Why this is noisy:

- Almost half the triples have empty subjects.
- Many triples are about system behavior rather than authorization.
- Some subjects are pronouns like `you` or `he`.

Recommended CyberChair slice:

1. Use `CyberChair/source_documents/overview.txt` for the first schema pass.
2. Focus on author/reviewer/chair policies:
   - authors submit abstracts/papers,
   - reviewers download assigned papers,
   - reviewers submit reviews,
   - reviewers read other reviews after submitting,
   - chair monitors review process,
   - anonymous comments are sent to authors.
3. Ignore low-value system-generation triples in the first pass.

Likely schema atoms:

```text
User
Author
Reviewer
Chair
Paper
Submission
Review
ReviewAssignment
Preference
Comment
Conference
```

Likely relationships/attributes:

```text
Paper.authors: Set<Author>
ReviewAssignment.paper: Paper
ReviewAssignment.reviewer: Reviewer
Review.paper: Paper
Review.reviewer: Reviewer
Review.submitted: Bool
Conference.phase: String or enum
Comment.anonymous: Bool
```

### 5.5 Collected ACP Sentences

This is not one coherent scenario. Treat it as a sentence-bank benchmark, not
an end-to-end schema case study.

Use for source sentences:

```text
Xiao Sources/Collected_ACP_Sentences.txt
```

Optional structured source:

```text
Xiao Sources/Collected_ACP_Sentences.json
Xiao Sources/Collected_ACP_Sentences.doc
```

Use for NLACP policy labels:

```text
labelled data sets/Collected ACP Sentences - ac rules.txt
labelled data sets/Collected ACP Sentences.xlsx
```

Audit counts:

```text
142 sentence lines
112 access-control sentence lines
258 NLACP triples
5 empty-subject triples
CRUD counts: R=118, C=86, U=30, D=11, E=2
markers: many NEG-* markers
```

Why this is useful:

- It is compact.
- It has relatively clean triples.
- It is good for evaluating atom extraction, negation handling, and CRUD/action
  mapping.

Why it is not the same experiment:

- It mixes multiple domains.
- There is no single coherent schema for all sentences.

How to use it:

1. Do not run it as one full schema-generation task.
2. Cluster sentences by domain first:
   - healthcare/privacy,
   - education/grades,
   - conference review,
   - ecommerce/customer data,
   - project/role management.
3. For each cluster, create a small `spec.md` with only those sentences and
   their matching triples.
4. Use it to measure whether AutoCedar can extract/normalize policy atoms,
   not to claim a full production schema for the whole file.

## 6. How To Prepare The Authoring Context

Use this template for every dataset slice. Save it as `spec.md` for CLI runs,
or paste the same content into the TUI draft.

```markdown
# <Dataset Name> AutoCedar Formalization Spec

## Provenance / Source Files

- REDE source description: `<relative path>`
- REDE NLACP labels: `<relative path>`
- REDE structured source, if used: `<relative path>`

These paths are provenance only. AutoCedar will not open them automatically.
Paste the actual source excerpts below.

## Research Task

Convert this natural-language access-control scenario and its NLACP policy
statements into reviewed Cedar artifacts:

1. Propose Cedar schema atoms.
2. Ask the human reviewer to approve, reject, edit, or question each schema
   atom.
3. Propose policy/property atoms from the NLACP policies.
4. Ask the human reviewer to approve, reject, edit, or question each
   property atom.
5. Compile approved atoms into a Cedar schema, verification plan, reference
   policies, and final Cedar candidate.

## Domain Description Given To AutoCedar

Paste the relevant problem description here.

## NLACP Policies Given To AutoCedar

Paste selected numbered policy sentences and triples here.
Keep sentence ids. Example:

86.0:Security
87.0:The system must prevent students from changing any schedules other than their own...
          student;change;other schedule;NEG-prevent - CUD

88.0:Only Professors can enter grades for students.
          professors;enter;grade;ONLY-only - C

## Human Review Guidance

- Treat REDE triples as weak labels, not as final truth.
- Normalize plural/singular subjects.
- Ignore UI-only behavior unless it is access-control relevant.
- Turn `ONLY-only` into both a positive allowance and a ceiling excluding
  everyone else.
- Turn `NEG-not` and `NEG-prevent` into safety/deny constraints.
- Convert ownership language such as "their own" into resource attributes.
- Decide whether service actors like `system` are principals or out of scope.
```

## 7. How To Review Atoms

During AutoCedar review:

- Approve atoms that correctly capture the intended domain.
- Edit atoms when names/types are wrong but the idea is right.
- Reject noisy atoms from the NLACP export, especially UI-only actions like
  `display message` unless they represent real authorization.
- Ask questions when the prose is ambiguous.

Examples:

```text
student;change;other schedule;NEG-prevent - CUD
```

Should become a property like:

```text
Students may update only schedules they own.
```

It needs schema support:

```text
Schedule.owner: Student
```

Another example:

```text
professors;enter;grade;ONLY-only - C
```

Should become two properties:

```text
Professors can enter grades for students in their course offerings.
Non-professors cannot enter grades.
```

It needs schema support:

```text
Grade.offering: CourseOffering
CourseOffering.instructor: Professor
```

## 8. What To Measure

For each dataset/slice, record:

```text
dataset name
source files used
sentence id range used
number of NLACP policy sentences
number of NLACP triples
number of schema atoms proposed
schema atoms approved / edited / rejected / questioned
number of property atoms proposed
property atoms approved / edited / rejected / questioned
whether final schema validated
number of reference policies generated
whether Stage 3 synthesis converged
final verifier loss
human review time
main ambiguity types
```

These measurements become paper evidence.

## 9. What This Adds To The Paper

This experiment adds a new section/case study:

> External NLACP-to-Cedar formalization with human-verifiable intent.

It supports these claims:

1. AutoCedar is not only solving handcrafted CedarBench scenarios.
2. AutoCedar can consume existing access-control requirements datasets.
3. HITL schema atomization is necessary because NLACP gives policy intent but
   not a deployable Cedar schema.
4. HITL policy atomization is necessary because NLACP triples are noisy and
   underspecified.
5. The final artifact is stronger than an NLACP extraction: it is a Cedar
   schema plus Cedar policy plus symbolic verification plan.
6. This bridges the deployment gap from requirements-engineering datasets to
   production authorization artifacts.

Do not overclaim. The REDE labels are not formal ground truth. The human
review is the trust anchor. The strong claim is:

> Given real NLACP scenario material, AutoCedar can help a human convert access
> control intent into reviewed, symbolically checked Cedar artifacts suitable
> for production-style authorization.

## 10. Recommended Work Order

1. IBM Course Management, first slice.
2. iTrust for Text2Policy, first slice.
3. CyberChair, author/reviewer/chair slice.
4. iTrust for ACRE, small healthcare slice.
5. Collected ACP Sentences, clustered sentence-level extraction.

Do not start with full iTrust ACRE or all Collected ACP sentences. The goal is
not volume first; the goal is a clean, explainable conversion path.

## 11. Final Deliverable For Each Dataset

For each dataset or slice, produce a short report with:

```text
1. Source files used.
2. Exact `spec.md` path.
3. AutoCedar command used.
4. Output session directory.
5. Final schema path.
6. Final candidate Cedar path.
7. Verification status.
8. Atom review counts.
9. Main human decisions.
10. Whether this slice is paper-ready.
```

Paper-ready means:

- The schema is coherent.
- The final Cedar validates.
- The verification plan/reference policies are human-reviewed.
- The final candidate satisfies the checks or the failure is explainable.
- The report clearly traces NLACP policies to Cedar atoms and final policy
  clauses.
