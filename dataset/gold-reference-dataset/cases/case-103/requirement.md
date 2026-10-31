Wire Transfer Approval and Release

A user may approve a wire transfer only if they hold the verifier or treasury officer role, their approval tier and the transfer’s amount tier are each 0, 1, or 2, and their approval tier is at least the transfer’s amount tier. The transfer’s amount and fee must each be at least $0.00. The approving user must not be the transfer’s initiator unless an emergency has been declared and the user holds the treasury officer role. This exception waives only the requirement to be different from the initiator; all other approval requirements still apply.

A user may release a wire transfer only if they hold the treasury officer role, the transfer’s amount is at least $0.00, and the request is made on the secure network. The transfer must have verified status unless an emergency has been declared and the user holds the treasury officer role. This exception waives only the verified-status requirement; all other release requirements still apply.

These are the only permissions: approval and release are permitted exactly when their respective requirements above are met, and no other actions are permitted. Decisions use current recorded facts and trusted application context; these permissions neither change records nor require an execution order between approval and release. Amounts in the supplied records are stored in whole US cents.
