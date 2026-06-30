// Floor: a member of the channel MUST be permitted to read.
permit (principal is Member, action == Action::"read", resource is Channel)
when { resource.members.contains(principal) };
