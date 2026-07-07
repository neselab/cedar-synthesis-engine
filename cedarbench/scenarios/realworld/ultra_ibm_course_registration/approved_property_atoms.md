# Approved Property Atoms - IBM Course Registration Manual AITL

Status: manually reviewed and approved during agent-in-the-loop simulation.

Canonical Cedar bodies live in `references/*.cedar`. This ledger records the approved property atoms that those references/checks represent. Liveness atoms do not have reference policy files; they are `always-denies-liveness` checks in `verification_plan.py`.

Verification summary: `loss: 0`; all 21 checks passed against `candidate.cedar`.

| # | Atom | Type | Action | Resource | Approved intent | Canonical reference |
|---:|---|---|---|---|---|---|
| 1 | `catalogue_ceiling` | ceiling | `requestCatalogue` | `CourseCatalogue` | Students may request catalogues from the campus LAN at the beginning of semester. | `references/catalogue_ceiling.cedar` |
| 2 | `register_course_ceiling` | ceiling | `registerCourse` | `CourseSelection` | Students may register only for their own current-semester selections while registration is open. | `references/register_course_ceiling.cedar` |
| 3 | `add_course_ceiling` | ceiling | `addCourseSelection` | `CourseSelection` | Students may add only their own current selections during add/drop while registration is open. | `references/add_course_ceiling.cedar` |
| 4 | `update_course_ceiling` | ceiling | `updateCourseSelection` | `CourseSelection` | Students may update only their own current selections during add/drop while registration is open. | `references/update_course_ceiling.cedar` |
| 5 | `delete_course_ceiling` | ceiling | `deleteCourseSelection` | `CourseSelection` | Students may delete only their own current selections during add/drop while registration is open. | `references/delete_course_ceiling.cedar` |
| 6 | `report_card_ceiling` | ceiling | `viewReportCard` | `ReportCard` | Students may view only their own previous-semester report cards from the campus LAN. | `references/report_card_ceiling.cedar` |
| 7 | `select_teaching_ceiling` | ceiling | `selectTeachingOffering` | `CourseOffering` | Professors may select eligible upcoming offerings only while registration is open and conflict-free. | `references/select_teaching_ceiling.cedar` |
| 8 | `modify_assigned_offering_ceiling` | ceiling | `modifyAssignedOffering` | `CourseOffering` | Professors may modify only their own assigned offerings while registration is open. | `references/modify_assigned_offering_ceiling.cedar` |
| 9 | `view_roster_ceiling` | ceiling | `viewRoster` | `CourseOffering` | Professors may view rosters only for offerings they teach. | `references/view_roster_ceiling.cedar` |
| 10 | `enter_grade_ceiling` | ceiling | `enterGrade` | `GradeRecord` | Only the professor for a completed previous-semester class may enter grades. | `references/enter_grade_ceiling.cedar` |
| 11 | `student_info_ceiling` | ceiling | `changeStudentInfo` | `StudentInfo` | Only the registrar may change student information. | `references/student_info_ceiling.cedar` |
| 12 | `close_registration_ceiling` | ceiling | `closeRegistration` | `RegistrationProcess` | Only the registrar may close current registration. | `references/close_registration_ceiling.cedar` |
| 13 | `register_course_floor` | floor | `registerCourse` | `CourseSelection` | Students must be able to register for their own current-semester offering while registration is open. | `references/register_course_floor.cedar` |
| 14 | `add_course_floor` | floor | `addCourseSelection` | `CourseSelection` | Students must be able to add their own current selections during add/drop. | `references/add_course_floor.cedar` |
| 15 | `report_card_floor` | floor | `viewReportCard` | `ReportCard` | Students must be able to view their own previous-semester report cards. | `references/report_card_floor.cedar` |
| 16 | `select_teaching_floor` | floor | `selectTeachingOffering` | `CourseOffering` | Eligible professors must be able to select conflict-free upcoming offerings before registration closes. | `references/select_teaching_floor.cedar` |
| 17 | `enter_grade_floor` | floor | `enterGrade` | `GradeRecord` | Professors must be able to enter grades for their completed classes. | `references/enter_grade_floor.cedar` |
| 18 | `registrar_close_floor` | floor | `closeRegistration` | `RegistrationProcess` | Registrar must be able to close current registration. | `references/registrar_close_floor.cedar` |
| 19 | `liveness_register` | liveness | `registerCourse` | `CourseSelection` | At least one student registration request should be possible. | none |
| 20 | `liveness_enter_grade` | liveness | `enterGrade` | `GradeRecord` | At least one professor grade-entry request should be possible. | none |
| 21 | `liveness_close_registration` | liveness | `closeRegistration` | `RegistrationProcess` | At least one registrar close-registration request should be possible. | none |

