# Course Registration Access-Control Requirements

The university is deploying an online course-registration system. Students use the system from personal computers attached to the campus LAN.

At the beginning of each semester, students may request and browse a course catalogue containing course offerings for the current semester. The catalogue includes course information such as professor, department, and prerequisites.

During the add/drop period, students must be able to add, drop, and update course selections for their own schedules. A student may update a current selection by deleting and adding course offerings. Students must not register for course offerings or change course selections after registration for the current semester has closed. Students must not change schedules belonging to other students.

At the end of the semester, each student may view their own electronic report card for the previously completed semester. Student grades are sensitive information and must not be visible to other students.

Professors use the system to indicate which course offerings they will teach. A professor may select course offerings from the catalogue only if the professor is eligible to teach that offering, there is no schedule conflict, and registration has not closed. Professors must not modify assigned course offerings for other professors. Professors cannot change the course offerings they teach after registration for the current semester has closed.

Professors may see which students signed up for course offerings they teach. Professors may enter grades for students in classes they taught after the semester has been completed. Only professors can enter grades.

Only the Registrar is allowed to change student information. The Registrar is also allowed to close the registration process.

The policy should be least-permissive with respect to this description. If the requirements say that a role may perform an action only under a condition, the policy must not permit the same action outside that condition unless another requirement explicitly grants it. In particular:

- student schedule changes are limited to the acting student's own schedule and an open registration period;
- student report-card viewing is limited to the acting student's own completed-semester report card;
- professor course-offering updates are limited to offerings assigned to that professor, when the professor is eligible, there is no conflict, and registration is still open;
- professor roster viewing and grade entry are limited to classes taught by that professor;
- grade entry is professor-only;
- student-information changes and closing registration are registrar-only;
- catalogue browsing is limited to campus-LAN access.
