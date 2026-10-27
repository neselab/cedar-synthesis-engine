## Verification Results — 2 check(s) FAILED

- floor__submitstep1__slice_p0003 (implies): **PASS**
- ceiling__submitstep1 (implies): **PASS**
- floor__submitfullpaper__slice_p0004 (implies): **PASS**
- ceiling__submitfullpaper (implies): **PASS**
- floor__updatestep1info__slice_p0005 (implies): **PASS**
- ceiling__updatestep1info (implies): **PASS**
- floor__submitcameraready__slice_p0006 (implies): **PASS**
- ceiling__submitcameraready (implies): **PASS**
- floor__downloadpaper__slice_p0007 (implies): **PASS**
- ceiling__downloadpaper (implies): **PASS**
- floor__submitreview__slice_p0008_submit (implies): **PASS**
- ceiling__submitreview (implies): **PASS**
- floor__updatereview__slice_p0008_update (implies): **PASS**
- ceiling__updatereview (implies): **PASS**
- floor__readotherreviews__slice_p0009 (implies): **PASS**
- ceiling__readotherreviews (implies): **PASS**
- floor__declareconflict__slice_p0010 (implies): **PASS**
- ceiling__declareconflict (implies): **PASS**
- floor__volunteerforconflictingpaper__slice_p0011 (implies): **PASS**
- ceiling__volunteerforconflictingpaper (implies): **FAIL**
  **Your policy is MORE permissive than the ceiling.**
  It allows something the ceiling forbids. Tighten conditions.
  Ceiling policy (your policy must not exceed this):
  ```cedar
  permit(
  principal is User,
  action == Action::"volunteerForConflictingPaper",
  resource is Submission
) when {
  (((principal.role) == "Reviewer") && (principal.submittedAllAssignedReviews)) && (!((resource.conflictedReviewers).contains(principal)))
};
  ```

  **Signal-layer diagnosis:**
    - Check identity: `ceiling__volunteerforconflictingpaper`
    - Check direction: `implies`
    - Intent description: Only requests in one of this scope's slices may be allowed.
    - Likely repair class(es):
      - set membership encoding drift: keep entity-set checks in one style, prefer `setAttr.contains(entity)` for attribute sets.
      - ceiling/over-permission failure: candidate allows at least one request outside this reference. Tighten the candidate permit while preserving all required floors. The target is fixed during synthesis; a suspected target conflict must be returned for review, never silently removed.
    - Candidate policy block(s) for same action:
      ```cedar
      permit (principal, action == Action::"submitStep1", resource)
      when {
          principal in resource.authors && resource.step1Open
      };
      
      permit (principal, action == Action::"submitFullPaper", resource)
      when {
          principal in resource.authors && context.hasStep2Credential && resource.step2Open
      };
      
      permit (principal, action == Action::"updateStep1Info", resource)
      when {
          principal in resource.authors && resource.step2Open
      };
      
      permit (principal, action == Action::"submitCameraReady", resource)
      when {
          principal in resource.authors && resource.selected && resource.reviewProcessDone
      };
      
      permit (principal, action == Action::"downloadPaper", resource)
      when {
          principal in resource.assignedReviewers && resource.distributionDone && !(principal in resource.conflictedReviewers)
      };
      
      permit (principal, action == Action::"submitReview", resource)
      when {
          principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      };
      
      permit (principal, action == Action::"updateReview", resource)
      when {
          principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      };
      
      permit (principal, action == Action::"readOtherReviews", resource)
      when {
          principal in resource.reviewersSubmitted
      };
      
      permit (principal, action == Action::"declareConflict", resource)
      when {
          principal in resource.assignedReviewers
      };
      
      permit (principal, action == Action::"volunteerForConflictingPaper", resource)
      when {
          principal.submittedAllAssignedReviews && !(principal in resource.conflictedReviewers)
      };
      ```
    - Candidate/reference diff around this action:
      ```
      --- reference
      +++ candidate
      @@ -1,7 +1,49 @@
      -permit(
      -  principal is User,
      -  action == Action::"volunteerForConflictingPaper",
      -  resource is Submission
      -) when {
      -  (((principal.role) == "Reviewer") && (principal.submittedAllAssignedReviews)) && (!((resource.conflictedReviewers).contains(principal)))
      +permit (principal, action == Action::"submitStep1", resource)
      +when {
      +    principal in resource.authors && resource.step1Open
       };
      +
      +permit (principal, action == Action::"submitFullPaper", resource)
      +when {
      +    principal in resource.authors && context.hasStep2Credential && resource.step2Open
      +};
      +
      +permit (principal, action == Action::"updateStep1Info", resource)
      +when {
      +    principal in resource.authors && resource.step2Open
      +};
      +
      +permit (principal, action == Action::"submitCameraReady", resource)
      +when {
      +    principal in resource.authors && 
      ... (139 chars omitted) ...
      resource.conflictedReviewers)
      +};
      +
      +permit (principal, action == Action::"submitReview", resource)
      +when {
      +    principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      +};
      +
      +permit (principal, action == Action::"updateReview", resource)
      +when {
      +    principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      +};
      +
      +permit (principal, action == Action::"readOtherReviews", resource)
      +when {
      +    principal in resource.reviewersSubmitted
      +};
      +
      +permit (principal, action == Action::"declareConflict", resource)
      +when {
      +    principal in resource.assignedReviewers
      +};
      +
      +permit (principal, action == Action::"volunteerForConflictingPaper", resource)
      +when {
      +    principal.submittedAllAssignedReviews && !(principal in resource.conflictedReviewers)
      +};
      ```
  Counterexample from solver:
  ```
  ✗ Policy set 1 implies policy set 2: DOES NOT HOLD
  Counterexample found:
principal: User::"", action: Action::"volunteerForConflictingPaper", resource: Submission::""
context: {}
entities: [
  User::"A" {
    role: "",
    submittedAllAssignedReviews: true,
  },
  User::"" {
    role: "",
    submittedAllAssignedReviews: true,
  },
  Action::"displayAbstract",
  Action::"readOtherReviews",
  Action::"readReviewFile",
  Action::"accessReviewerDirectory",
  Action::"indicateWillingness",
  Action::"updateReview",
  Action::"askAdditionalReviewer",
  Action::"monitorReviewProcess",
  Action::"declareConflict",
  Action::"submitFullPaper",
  Action::"downloadPaper",
  Action::"volunteerForConflictingPaper",
  Action::"updateStep1Info",
  Action::"submitStep1",
  Action::"submitReview",
  Submission::"" {
    assignedReviewers: [User::""],
    authors: [User::"A"],
    conflictedReviewers: [],
    contactPerson: User::"A",
    distributionDone: true,
    hasConflictingReviews: true,
    onlyNonExpertReviews: true,
    reviewOpen: true,
    reviewProcessDone: true,
    reviewersSubmitted: [User::"", User::"A"],
    selected: true,
    step1Open: true,
    step2Open: true,
  },
  Action::"indicateExpertise",
  Action::"submitCameraReady",
  ReviewerDirectory::"" {
    allowedUsers: [],
    owner: User::"",
  },
]
  ```
- floor__monitorreviewprocess__slice_p0012 (implies): **PASS**
- ceiling__monitorreviewprocess (implies): **PASS**
- floor__askadditionalreviewer__slice_p0013 (implies): **PASS**
- ceiling__askadditionalreviewer (implies): **FAIL**
  **Your policy is MORE permissive than the ceiling.**
  It allows something the ceiling forbids. Tighten conditions.
  Ceiling policy (your policy must not exceed this):
  ```cedar
  permit(
  principal is User,
  action == Action::"askAdditionalReviewer",
  resource is ReviewOverview
) when {
  ((principal.role) == "PCC") && (((resource.paper).onlyNonExpertReviews) == true)
};
  ```

  **Signal-layer diagnosis:**
    - Check identity: `ceiling__askadditionalreviewer`
    - Check direction: `implies`
    - Intent description: Only requests in one of this scope's slices may be allowed.
    - Likely repair class(es):
      - ceiling/over-permission failure: candidate allows at least one request outside this reference. Tighten the candidate permit while preserving all required floors. The target is fixed during synthesis; a suspected target conflict must be returned for review, never silently removed.
    - Candidate policy block(s) for same action:
      ```cedar
      permit (principal, action == Action::"submitStep1", resource)
      when {
          principal in resource.authors && resource.step1Open
      };
      
      permit (principal, action == Action::"submitFullPaper", resource)
      when {
          principal in resource.authors && context.hasStep2Credential && resource.step2Open
      };
      
      permit (principal, action == Action::"updateStep1Info", resource)
      when {
          principal in resource.authors && resource.step2Open
      };
      
      permit (principal, action == Action::"submitCameraReady", resource)
      when {
          principal in resource.authors && resource.selected && resource.reviewProcessDone
      };
      
      permit (principal, action == Action::"downloadPaper", resource)
      when {
          principal in resource.assignedReviewers && resource.distributionDone && !(principal in resource.conflictedReviewers)
      };
      
      permit (principal, action == Action::"submitReview", resource)
      when {
          principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      };
      
      permit (principal, action == Action::"updateReview", resource)
      when {
          principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      };
      
      permit (principal, action == Action::"readOtherReviews", resource)
      when {
          principal in resource.reviewersSubmitted
      };
      
      permit (principal, action == Action::"declareConflict", resource)
      when {
          principal in resource.assignedReviewers
      };
      
      permit (principal, action == Action::"volunteerForConflictingPaper", resource)
      when {
          principal.submittedAllAssignedReviews && !(principal in resource.conflictedReviewers)
      };
      
      permit (principal, action == Action::"monitorReviewProcess", resource)
      when {
          principal.role == "Chair" || principal.role == "PCC"
      };
      
      permit (principal, action == Action::"askAdditionalReviewer", resource)
      when {
          principal.role == "PCC"
      };
      ```
    - Candidate/reference diff around this action:
      ```
      --- reference
      +++ candidate
      @@ -1,7 +1,59 @@
      -permit(
      -  principal is User,
      -  action == Action::"askAdditionalReviewer",
      -  resource is ReviewOverview
      -) when {
      -  ((principal.role) == "PCC") && (((resource.paper).onlyNonExpertReviews) == true)
      +permit (principal, action == Action::"submitStep1", resource)
      +when {
      +    principal in resource.authors && resource.step1Open
       };
      +
      +permit (principal, action == Action::"submitFullPaper", resource)
      +when {
      +    principal in resource.authors && context.hasStep2Credential && resource.step2Open
      +};
      +
      +permit (principal, action == Action::"updateStep1Info", resource)
      +when {
      +    principal in resource.authors && resource.step2Open
      +};
      +
      +permit (principal, action == Action::"submitCameraReady", resource)
      +when {
      +    principal in resource.authors && resource.selected && resource.reviewProcessDone
      +};
      +
      +perm
      ... (340 chars omitted) ...
      Action::"updateReview", resource)
      +when {
      +    principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
      +};
      +
      +permit (principal, action == Action::"readOtherReviews", resource)
      +when {
      +    principal in resource.reviewersSubmitted
      +};
      +
      +permit (principal, action == Action::"declareConflict", resource)
      +when {
      +    principal in resource.assignedReviewers
      +};
      +
      +permit (principal, action == Action::"volunteerForConflictingPaper", resource)
      +when {
      +    principal.submittedAllAssignedReviews && !(principal in resource.conflictedReviewers)
      +};
      +
      +permit (principal, action == Action::"monitorReviewProcess", resource)
      +when {
      +    principal.role == "Chair" || principal.role == "PCC"
      +};
      +
      +permit (principal, action == Action::"askAdditionalReviewer", resource)
      +when {
      +    principal.role == "PCC"
      +};
      ```
  Counterexample from solver:
  ```
  ✗ Policy set 1 implies policy set 2: DOES NOT HOLD
  Counterexample found:
principal: User::"", action: Action::"askAdditionalReviewer", resource: ReviewOverview::""
context: {}
entities: [
  Action::"submitCameraReady",
  Action::"volunteerForConflictingPaper",
  Action::"downloadPaper",
  Action::"accessReviewerDirectory",
  Action::"submitFullPaper",
  User::"" {
    role: "PCC",
    submittedAllAssignedReviews: true,
  },
  Action::"askAdditionalReviewer",
  Action::"monitorReviewProcess",
  Action::"updateReview",
  ReviewerDirectory::"" {
    allowedUsers: [],
    owner: User::"",
  },
  Action::"readOtherReviews",
  Action::"updateStep1Info",
  Action::"submitStep1",
  Action::"indicateExpertise",
  Action::"submitReview",
  Action::"displayAbstract",
  Action::"indicateWillingness",
  Action::"readReviewFile",
  Submission::"" {
    assignedReviewers: [],
    authors: [User::""],
    conflictedReviewers: [User::"A"],
    contactPerson: User::"A",
    distributionDone: true,
    hasConflictingReviews: true,
    onlyNonExpertReviews: false,
    reviewOpen: true,
    reviewProcessDone: true,
    reviewersSubmitted: [User::"", User::"A"],
    selected: true,
    step1Open: true,
    step2Open: true,
  },
  ReviewOverview::"" {
    paper: Submission::"",
  },
  Action::"declareConflict",
  User::"A" {
    role: "PCC",
    submittedAllAssignedReviews: true,
  },
]
  ```
- floor__accessreviewerdirectory__slice_p0014_dir (implies): **PASS**
- ceiling__accessreviewerdirectory (implies): **PASS**
- floor__readreviewfile__slice_p0014_file (implies): **PASS**
- ceiling__readreviewfile (implies): **PASS**
- no_runtime_errors__submitStep1__User__Submission (never-errors): **PASS**
- no_runtime_errors__submitFullPaper__User__Submission (never-errors): **PASS**
- no_runtime_errors__updateStep1Info__User__Submission (never-errors): **PASS**
- no_runtime_errors__submitCameraReady__User__Submission (never-errors): **PASS**
- no_runtime_errors__downloadPaper__User__Submission (never-errors): **PASS**
- no_runtime_errors__submitReview__User__Submission (never-errors): **PASS**
- no_runtime_errors__updateReview__User__Submission (never-errors): **PASS**
- no_runtime_errors__readOtherReviews__User__Submission (never-errors): **PASS**
- no_runtime_errors__declareConflict__User__Submission (never-errors): **PASS**
- no_runtime_errors__volunteerForConflictingPaper__User__Submission (never-errors): **PASS**
- no_runtime_errors__monitorReviewProcess__User__ReviewOverview (never-errors): **PASS**
- no_runtime_errors__askAdditionalReviewer__User__ReviewOverview (never-errors): **PASS**
- no_runtime_errors__accessReviewerDirectory__User__ReviewerDirectory (never-errors): **PASS**
- no_runtime_errors__readReviewFile__User__ReviewFile (never-errors): **PASS**

Fix the policy to address EVERY failure without breaking passing checks. Output the COMPLETE updated policy.