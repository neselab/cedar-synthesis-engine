# IBM Course Registration Access Control Intent

Manual AITL target built from the human-provided IBM course registration prose.
This workspace is a trace artifact for debugging AutoCedar, not an automatically
generated session.

## Authorization Intent Covered

1. Students may request the course catalogue at the beginning of the semester
   from the campus LAN.
2. Students may register for current-semester course offerings while registration
   is open.
3. Students may add, update, or delete their own current course selections during
   the add/drop period.
4. Students may not register or alter selections after registration is closed.
5. Students may view only their own report cards for the previously completed
   semester.
6. Professors may select upcoming course offerings they are eligible to teach if
   there is no conflict and registration remains open.
7. Professors may not modify assigned course offerings for other professors.
8. Professors may view rosters for course offerings they teach.
9. Professors may enter grades for students in classes they taught in the
   previous semester.
10. Only the registrar may change student information.
11. The registrar may close the current registration process.
12. Student grades are treated as sensitive: only the owning student can view a
    report card, and only the professor of the completed course can enter grades.

## Deliberately Not Modeled As Access Control

- The informational contents of a course catalogue.
- The mechanics of the system retrieving the roster.
- The actual grade value domain A/B/C/D/F/I, except as part of the grading
  workflow.

