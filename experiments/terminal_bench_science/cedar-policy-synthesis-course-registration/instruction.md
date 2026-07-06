# Cedar Policy Synthesis: Course Registration

You are working in `/app`.

The file `requirements.md` describes access-control requirements for a university course-registration system. The file `schema.cedarschema` defines the Cedar entities, actions, resources, and context fields that the application exposes to the policy layer.

Your task is to write a Cedar policy store in:

```text
/app/policy.cedar
```

The final policy must satisfy the natural-language requirements and pass the verifier.

## What To Do

1. Read `requirements.md`.
2. Inspect `schema.cedarschema`.
3. Write `policy.cedar`.
4. Run `cedar validate --schema schema.cedarschema --policies policy.cedar` and fix any syntax or type errors.

## Important Intent Boundaries

The policy should preserve all of these requirements:

- Students may browse course offerings from computers on the campus LAN.
- Students may add, drop, and update only their own course selections, and only while registration is open.
- Students may not register or modify course selections after registration closes.
- Students may view only their own report cards.
- Professors may select only course offerings they are eligible to teach, only when there is no schedule conflict, and only while registration is open.
- Professors may view rosters only for offerings they teach.
- Professors may enter grades only for course offerings they teach and only for a completed semester.
- Only the Registrar may change student information.
- Only the Registrar may close registration.

Do not grant broad role permissions that ignore ownership, registration status, lifecycle state, eligibility, conflict, or grade privacy.

## Output Contract

Create or replace `/app/policy.cedar`. Do not rely on external services or network access. The verifier will run hidden semantic checks over your final policy.
