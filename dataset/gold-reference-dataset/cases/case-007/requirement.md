Equipment Calibration Access

These are the only permissions for users to approve an asset’s return to service or calibrate an asset; each permission requires all applicable conditions below. Decisions use current recorded facts and trusted information from the host application. These permissions neither change records nor require either activity to precede the other.

Return-to-service approval

A user with the Quality Inspector or Metrology Manager role may approve an asset’s return to service only if the user is not the asset’s recorded technician. During a declared emergency, a Calibration Technician or Senior Technician who is the asset’s recorded technician may also approve its return to service; this exception waives only the requirement to be someone other than that technician. In all cases, the asset’s out-of-service flag must be false.

Calibration

A user may calibrate an asset only if the user holds the Calibration Technician or Senior Technician role. The user’s certification level and the asset’s equipment class must each be 0, 1, 2, or 3, and the certification level must be at least the equipment class. The asset must have a nonnegative measurement point count and an asset tag beginning with “MET-”. Only when the measurement point count exceeds 200 must the host application also confirm completion of the additional review.
