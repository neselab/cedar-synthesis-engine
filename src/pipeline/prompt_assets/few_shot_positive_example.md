# Positive Example

Task:

- Policy requirement:
  Readers can pull a repository.
  Writers can push a repository if the repository is not archived.
- Relevant schema facts:
  `Repository` has attributes `readers`, `writers`, and `isArchived`.
  `pull` and `push` are repository actions.

Correct Cedar output:

```cedar
permit (
    principal is User,
    action == Action::"pull",
    resource is Repository
) when {
    principal in resource.readers
};

permit (
    principal is User,
    action == Action::"push",
    resource is Repository
) when {
    principal in resource.writers &&
    !resource.isArchived
};
```

Why this is good:

- It uses exact schema names.
- It handles both role-based access and the archive constraint.
- It outputs only Cedar statements.

