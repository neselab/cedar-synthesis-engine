Underwriting Exception Approval and Policy Binding

These are the only permissions: users may approve underwriting exceptions and bind insurance policies on applications only under the applicable conditions below. Decisions use current recorded facts and trusted context supplied by the host application; these permissions neither change records nor require either activity to occur first. Amounts in the supplied records are stored in whole US cents.

Approving an underwriting exception

A user with the senior underwriter, underwriting manager, or chief underwriter role may approve an underwriting exception for an application whose premium is at least $0.00 and whose segments include "high_value". The user must be the application's assigned underwriter unless a staffing emergency has been declared and the user holds the underwriting manager role. This exception waives only the assignment requirement; all other approval requirements still apply.

Binding an insurance policy

A user with the underwriter, senior underwriter, or underwriting manager role may bind an insurance policy for an application whose premium is at least $0.00 and whose product code starts with "EXCESS-", followed by zero or more characters. The user's authority level and the application's risk tier must each be one of 0, 1, 2, or 3. The user's authority level must be at least the application's risk tier unless a catastrophe surge has been declared and the user holds the underwriter role. This exception waives only the authority-to-risk comparison; the permitted authority levels and risk tiers and all other binding requirements still apply.
