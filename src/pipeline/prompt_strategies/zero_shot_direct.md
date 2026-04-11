# Cedar Policy Generation
You are given:
- a detailed natural language policy specification (`policy_spec.md`)
- a responding Cedar schema (`schema.cedarschema`)
You must generate a Cedar access control policy.

## Task Input

### Schema
```cedar
{CEDAR_SCHEMA}
```

### Policy Specification
{POLICY_SPEC}

## Output Requirement
Output ONLY Cedar policy code. No markdown explanation. No prose. No bullet points.


# Output Format
Only output the final Cedar policy inside `<cedar_policy>` tags.

<cedar_policy>
Cedar policy here
</cedar_policy>
