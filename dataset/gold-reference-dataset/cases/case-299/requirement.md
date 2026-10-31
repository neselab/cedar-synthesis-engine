Contract Lifecycle Access

These are the only permissions for users to execute, review, or sign contract records; all applicable requirements below must be met. For each activity, the contract value must be at least $0.00. Amounts in the supplied records are stored in whole US cents. Decisions use current recorded facts and trusted request information, with all times in UTC. These permissions neither change contract state nor require an order between activities.

Execution requires the contract administrator role, a contract in signed status, an effective date no later than the request’s current date, and a request made on the corporate network.

Review requires the reviewer role and a contract in draft status. The request’s current date must be at or after its scheduled review start and strictly before its scheduled review end. The contract’s counterparty must not be among the user’s recorded conflicted counterparties.

Signing requires the signatory role or the contract administrator role. The user’s signing authority and the contract’s required authority must each be one of the levels 0, 1, or 2. The user’s signing authority must be at least the contract’s required authority unless escalation is approved and the user holds the signatory role. This exception waives only the authority comparison; all other signing requirements remain in force. The contract’s counterparty must not be among the user’s recorded conflicted counterparties.
