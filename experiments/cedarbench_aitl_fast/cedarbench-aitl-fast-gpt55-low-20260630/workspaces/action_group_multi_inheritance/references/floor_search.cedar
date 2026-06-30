// Floor for Search: any user may Search any document.
permit (
  principal,
  action == Action::"Search",
  resource
);
