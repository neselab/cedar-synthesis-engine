# TB-Science Airtable Field Map

## Required Personal Fields

These must come from the submitting person:

- Name:
- Email:
- Affiliation:
- Role:
- GitHub:

Optional:

- Discord Name:
- Professional Profile:

## Task Fields

### Proposal Title

Cedar Policy Synthesis from Course-Registration Authorization Intent

### Scientific Domain

Other Sciences

### Field

Engineering Sciences

### Subfield

Autoformalization / Security Policy Verification

### Scientific Problem

Access-control policy authoring is a formalization problem: informal organizational requirements must be translated into executable authorization policies without introducing over-permission, under-permission, or broken lifecycle behavior. This task studies a realistic security-policy engineering workflow in which a university course-registration access-control specification must be converted into a deployable Cedar policy store.

The problem matters because security policies often compile and appear plausible while still violating organizational intent. In practice, policy engineers and formal-methods researchers must validate that policy code preserves ownership boundaries, lifecycle state, role/action constraints, and sensitive-data restrictions. This task captures that workflow in a compact, objectively verifiable terminal setting.

### Workflow Details

The agent receives `/app/requirements.md`, a natural-language course-registration access-control scenario, and `/app/schema.cedarschema`, a Cedar authorization schema for the application. The agent must synthesize `/app/policy.cedar`, a Cedar policy store satisfying the requirements.

The workflow is:

1. Inspect the requirements and schema.
2. Write a Cedar policy store.
3. Run Cedar validation and repair syntax/type errors.
4. Iterate until the policy satisfies the hidden semantic checks.

Expected output: a valid `/app/policy.cedar` file.

### Requirements

Software dependencies:

- Cedar Policy CLI with symbolic-analysis support.
- CVC5 solver.
- Python 3 for the verifier harness.

Recommended hardware:

- CPU only.
- 2 CPUs.
- 4 GB memory.
- 10 GB storage.

Estimated runtime:

- Build time depends on installing Cedar CLI and CVC5.
- Verification should run in a few minutes.
- Expert human solution time is approximately one hour.

### Dataset

The task uses a small synthetic/curated authorization scenario derived from course-registration access-control requirements. It consists of a natural-language requirements file and a Cedar schema. No large external dataset is required. The task data is included directly in the task package and is small enough to inspect manually.

### Evaluation Strategy

The task is objectively and programmatically verifiable. The verifier checks the final `/app/policy.cedar` artifact.

Verification consists of:

1. `cedar validate` for Cedar syntax and type correctness.
2. `cedar symcc implies` ceiling checks to ensure the candidate policy is not more permissive than hidden reference boundaries.
3. `cedar symcc implies` floor checks in the opposite direction to ensure required access is included.
4. `cedar symcc always-denies` liveness checks to ensure important workflows are not empty.

The verifier accepts any policy denotation satisfying the intended behavior; it does not require syntactic similarity to the oracle solution. Broad permit policies fail ceiling checks, and overly narrow policies fail floor or liveness checks.

### Complexity

Conceptually, the task is difficult because it requires preserving several interacting authorization boundaries at once: lifecycle state, ownership/self-access, role/action separation, professor eligibility, schedule-conflict constraints, sensitive grade visibility, and required access/liveness. A policy can be syntactically valid and still wrong.

A Cedar/security-policy expert could solve the task in roughly one hour. For a frontier AI terminal agent, the challenge is semantic composition and verifier-guided repair: agents commonly produce plausible but overbroad role policies, omit lifecycle constraints, or satisfy one requirement while violating another.

### References & Resources

- Cedar documentation: https://docs.cedarpolicy.com/
- Cedar Policy CLI: https://github.com/cedar-policy/cedar
- CVC5 SMT solver: https://cvc5.github.io/
- AutoCedar / CedarBench repository: https://github.com/neselab/cedar-synthesis-engine

### Reviewer Recommendation

Potential reviewers could include researchers with expertise in formal methods, access-control policy languages, Cedar, security policy verification, or automated program repair.

### Additional Information

A draft task package has been prepared locally under:

`experiments/terminal_bench_science/cedar-policy-synthesis-course-registration`

It includes the task instructions, requirements, schema, oracle solution, Dockerfile, and hidden symbolic verifier. The oracle solution passes locally with Cedar CLI 4.10.0 and CVC5 installed. A deliberately overbroad `permit (principal, action, resource);` policy fails the hidden ceiling checks.
