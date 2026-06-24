# Collected ACP Gradebook Access-Control Slice

## Dataset and Provenance

Dataset: REDE / ACRE corpus, Collected ACP Documents.

Source files:

- `Xiao Sources/Collected_ACP_Sentences.txt`
- `labelled data sets/Collected ACP Sentences - ac rules.txt`
- `labelled data sets/Collected ACP Sentences.xlsx`

This curated slice uses the gradebook/RBAC statements around labelled sentence
IDs 43-52. The full Collected ACP corpus is a mixed collection of unrelated
access-control examples, so this experiment intentionally isolates one coherent
mini-domain rather than pretending all collected statements belong to one
deployable application.

## Natural-Language Scenario

The system manages grade-related actions for students, teaching assistants,
faculty, and related faculty-family roles.

Students receive external grades but must not assign external grades.

Faculty members can assign internal grades and external grades.

Faculty members can view internal grades and external grades.

No user should be able to both receive and assign external grades through any
combination of roles.

Teaching assistants can view and assign internal grades, but teaching
assistants must not view or assign external grades.

Faculty members take final responsibility for external grades.

Members of the Faculty Family role can receive external grades.

If a subject is a faculty member, that subject may assign grades.

If a subject is a student, that subject must not assign grades.

If a subject is not a faculty member, that subject may enroll in courses.

## Selected NLACP Labels

The selected NLACP triples from the labelled file are:

```text
43.0:There do not exist members of Student who can Assign ExternalGrades.
          member;assign;externalgrade;NEG-not - C
          student;assign;externalgrade;NEG-not - C
44.0:All members of Faculty can Assign both InternalGrades and ExternalGrades.
          member;assign;internalgrades - C
          member;assign;externalgrades - C
45.0:No combination of roles exists such that a user with those roles can both Receive and Assign the resource ExternalGrades.
          user;receive assign;resource externalgrade;NEG-no - CRUD
46.0:Requests for students to Receive ExternalGrades, and for faculty to Assign and View both InternalGrades and ExternalGrades, will succeed.
          student;receive;externalgrade - R
          faculty;assign;internalgrades - C
          faculty;view;internalgrades - C
          faculty;assign;externalgrades - C
          faculty;view;externalgrades - C
47.0:The sole counter-example shows that a student with the freedom to assign external grades is also a ta but not a faculty member.
          ta;assign;external grade - C
48.0:TA can view and assign InternalGrades but not ExternalGrades (since faculty must take final responsibility for all external grades), combined with Pol3.
          ta;view;internalgrade - R
          ta;view;externalgrade - R
          ta;assign;internalgrade - C
          ta;assign;externalgrade - C
          faculty;take;final responsibility - C
          faculty;take;external grade - C
49.0:All members of role Faculty Family can receive External-Grades.
          member;receive;external-grade - R
50.0:If the subject is a faculty member, then permit that subject to assign grades.
          member;assign;grade -
51.0:If the subject is a student, then do not permit that subject to assign grades.
          student;assign;grade;NEG-not - C
52.0:If the subject is not a faculty member, then permit that subject to enroll in courses.
          subject;enroll;course - C
          faculty;enroll;course;NEG-not - C
```

## AutoCedar Instructions

Propose Cedar schema atoms first. The schema should represent the relevant
principal roles, grade resources, course resources, and any relationship or
role-membership state needed to express the requirements above.

Then propose policy/property atoms. Every proposed schema atom and every
proposed property atom must be reviewed before it is used. Properties should
include floors for required successful requests, ceilings/disjointness for
forbidden role/resource combinations, and liveness where the requirement says a
request should succeed.

Do not infer permissions for unrelated Collected ACP domains. Only formalize the
gradebook/RBAC slice above.
