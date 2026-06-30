// Ceiling for Search: ReadOnly group only. No principal requirement.
// Search may be performed by any user on any document.
permit (
  principal,
  action == Action::"Search",
  resource
);
