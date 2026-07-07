# Approved Property Atoms - CyberChair Manual AITL

Status: manually reviewed and approved during agent-in-the-loop simulation.

Canonical Cedar bodies live in `references/*.cedar`. This ledger records the approved property atoms that those references/checks represent. Liveness atoms do not have reference policy files; they are `always-denies-liveness` checks in `verification_plan.py`.

Verification summary: `loss: 0`; all 20 checks passed against `candidate.cedar`.

| # | Atom | Type | Action | Resource | Approved intent | Canonical reference |
|---:|---|---|---|---|---|---|
| 1 | `submit_step1_ceiling` | ceiling | `submitStep1` | `Submission` | Only authors of the submission may submit step-1 material while step 1 is open. | `references/submit_step1_ceiling.cedar` |
| 2 | `submit_full_paper_ceiling` | ceiling | `submitFullPaper` | `Submission` | Only authors with step-2 credentials may upload full papers during step 2. | `references/submit_full_paper_ceiling.cedar` |
| 3 | `update_step1_ceiling` | ceiling | `updateStep1Info` | `Submission` | Only authors with step-2 credentials may correct step-1 information during step 2. | `references/update_step1_ceiling.cedar` |
| 4 | `camera_ready_ceiling` | ceiling | `submitCameraReady` | `Submission` | Only authors of selected submissions may submit camera-ready versions after review. | `references/camera_ready_ceiling.cedar` |
| 5 | `download_assigned_ceiling` | ceiling | `downloadPaper` | `Submission` | Only assigned non-conflicted reviewers may download papers after distribution. | `references/download_assigned_ceiling.cedar` |
| 6 | `display_abstract_ceiling` | ceiling | `displayAbstract` | `Submission` | Only assigned non-conflicted reviewers may display abstracts after distribution. | `references/display_abstract_ceiling.cedar` |
| 7 | `submit_review_ceiling` | ceiling | `submitReview` | `Submission` | Only assigned non-conflicted reviewers may submit reviews while review is open. | `references/submit_review_ceiling.cedar` |
| 8 | `update_review_ceiling` | ceiling | `updateReview` | `Submission` | Only assigned non-conflicted reviewers may update reviews while review is open. | `references/update_review_ceiling.cedar` |
| 9 | `read_other_reviews_ceiling` | ceiling | `readOtherReviews` | `Submission` | Reviewers may read other reviewers' reviews only after submitting their own review for the paper. | `references/read_other_reviews_ceiling.cedar` |
| 10 | `volunteer_conflicting_paper_ceiling` | ceiling | `volunteerForConflictingPaper` | `Submission` | Reviewers may volunteer for conflicting-review papers only after finishing assigned reviews and absent conflict of interest. | `references/volunteer_conflicting_paper_ceiling.cedar` |
| 11 | `monitor_ceiling` | ceiling | `monitorReviewProcess` | `ReviewOverview` | Only chair/PCC roles may monitor review overviews. | `references/monitor_ceiling.cedar` |
| 12 | `ask_additional_reviewer_ceiling` | ceiling | `askAdditionalReviewer` | `ReviewOverview` | Only PCC may ask additional reviewers for low-expertise papers. | `references/ask_additional_reviewer_ceiling.cedar` |
| 13 | `directory_access_ceiling` | ceiling | `accessReviewerDirectory` | `ReviewerDirectory` | Reviewer directories are protected by owner or allowed-user list. | `references/directory_access_ceiling.cedar` |
| 14 | `review_file_access_ceiling` | ceiling | `readReviewFile` | `ReviewFile` | Review files are protected by the file and directory allowed-user lists. | `references/review_file_access_ceiling.cedar` |
| 15 | `author_submit_step1_floor` | floor | `submitStep1` | `Submission` | Authors must be able to submit step-1 material during step 1. | `references/author_submit_step1_floor.cedar` |
| 16 | `reviewer_read_other_reviews_floor` | floor | `readOtherReviews` | `Submission` | A reviewer who has submitted their own review must be able to read other reviews for that paper. | `references/reviewer_read_other_reviews_floor.cedar` |
| 17 | `pcc_ask_additional_reviewer_floor` | floor | `askAdditionalReviewer` | `ReviewOverview` | PCC must be able to ask for additional review on low-expertise papers. | `references/pcc_ask_additional_reviewer_floor.cedar` |
| 18 | `liveness_submit_step1` | liveness | `submitStep1` | `Submission` | At least one author step-1 submission request should be possible. | none |
| 19 | `liveness_submit_review` | liveness | `submitReview` | `Submission` | At least one reviewer submit-review request should be possible. | none |
| 20 | `liveness_monitor` | liveness | `monitorReviewProcess` | `ReviewOverview` | At least one chair/PCC monitoring request should be possible. | none |

