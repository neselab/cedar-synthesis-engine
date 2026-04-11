# Cedar Policy Syntax Cheat Sheet

## Policy Structure

```
permit | forbid (
    principal [== | is | in] ...,
    action    [== | in]      ...,
    resource  [== | is | in] ...
)
[when   { <condition> }]
[unless { <condition> }];
```

- `permit` → allow; `forbid` → deny (forbid overrides permit)
- `when { C }` → rule fires only if C is true
- `unless { C }` → rule fires only if C is false
- `when` and `unless` may both appear on the same policy
- Condition body **must** be wrapped in `{ }` — `unless principal in ...` is invalid
- Every policy statement ends with `;`

---

## Scope Patterns

```cedar
// exact match
principal == User::"alice"
action    == Action::"read"
resource  == File::"doc1"

// type constraint
principal is User
resource  is Document

// group / hierarchy membership
principal in Group::"engineering"
resource  in Folder::"docs"

// action set
action in [Action::"read", Action::"write"]
```

---

## Condition Operators

### Comparison
```cedar
principal.age >= 18
resource.classification != "HighlyRestricted"
context.networkRiskScore < 20
```
Operators: `==`  `!=`  `<`  `<=`  `>`  `>=`

### Logical
```cedar
principal.department == "eng" && !resource.isArchived
principal in Role::"Admin" || principal in Role::"Owner"
```
Operators: `&&`  `||`  `!`

### Membership (`in`)
```cedar
principal in Role::"ClinicalResearcher"   // entity group membership
principal in resource.readers             // membership in attribute set
```

### Attribute existence (`has`) — use before accessing optional attributes
```cedar
resource has expiryDate && resource.expiryDate > context.now
```

### Collection contains
```cedar
resource.tags.contains("public")
```

---

## Attribute Access

```cedar
principal.department
resource.owner
resource.project.status      // nested
context.isCompliantDevice
```

---

## Common Patterns

### Allow a group, block an exception
```cedar
permit (
    principal is User,
    action == Action::"view",
    resource is Document
) when {
    principal in Role::"Researcher"
} unless {
    resource.classification == "HighlyRestricted"
};
```

### Forbid everyone except a role
```cedar
forbid (
    principal is User,
    action == Action::"delete",
    resource is Document
) unless {
    principal in Role::"Admin"
};
```

### Conditional access with context
```cedar
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
) when {
    principal in resource.writers &&
    context.isCompliantDevice &&
    !resource.isLocked
};
```

---

## Key Rules

1. Use only entity types, actions, and attributes that exist in the schema — do not invent names
2. `unless { C }` requires braces — never write `unless <expr>` without `{ }`
3. Check optional attributes with `has` before accessing them
4. `in` checks group/hierarchy membership — use `.contains()` for set membership
5. `forbid` always overrides `permit` — Cedar denies by default
