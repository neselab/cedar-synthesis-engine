Prescription Refill and Verification Access

A user may authorize a prescription refill only if the user holds the pharmacist in charge role, the prescription has between 1 and 12 refills remaining, inclusive, its status is dispensed, and its prescriber DEA identifier begins with “BC”.

A user may verify a prescription only if the user holds the pharmacist in charge role, the prescription has between 0 and 12 refills remaining, inclusive, and the user is not the prescription’s entry author. Holding the staff pharmacist role alone is insufficient; holding it in addition to pharmacist in charge does not change these requirements. When the prescription has more than zero refills remaining, the host application must also confirm completion of the additional prescription-verification review. When no refills remain, that review confirmation is not required, but all other requirements still apply.

These are the only permissions granted for these activities; no other actions are permitted under this requirement.
