# CyberChair Access Control Intent

Manual AITL target built from the human-provided CyberChair prose. This
workspace is a trace artifact for debugging AutoCedar, not an automatically
generated session.

## Authorization Intent Covered

1. Authors can submit abstracts/papers during step 1.
2. Authors with step-2 credentials can upload full papers during step 2.
3. Authors can correct step-1 submission information during step 2.
4. Authors of selected submissions can submit camera-ready papers after review.
5. Assigned reviewers can access/download assigned papers after paper distribution,
   unless they have declared a conflict of interest.
6. Assigned non-conflicted reviewers can submit or update reviews while review is open.
7. Reviewers can read other reviewers' reviews for a paper only after submitting
   their own review for that paper.
8. Reviewers can declare conflicts of interest for assigned papers.
9. Reviewers may volunteer for papers with conflicting reviews only after they
   have submitted all assigned reviews and are not conflicted with the paper.
10. Chairs/PCC can monitor the review process and identify low-expertise papers.
11. PCC can ask an additional reviewer to review a low-expertise paper.
12. Reviewer directories and review files are protected from outsiders by
    per-directory allowed-user lists.

## Deliberately Not Modeled As Access Control

- The system assigning a unique submission id.
- Sending login/password email.
- The mechanics of copying files into reviewer directories.
- The content of generated hyperlinks.

