# iTrust Access Control Intent

The final product is a site where health care workers can access important patient information, the non-emergency access can be controlled, and all access would be tracked.

HIPAA rules protect patients' information and also allow a patient to dictate who can access this information.

Approved diagnostic information: The set of diagnostic information a patient allows a designated or other licensed health care professional to view.

A patient is only given the choice to restrict viewing on selected diagnostic information, such as those related to mental illness, substance abuse, and cosmetic surgery.

The licensed health care professional making a diagnosis determines if a patient is granted the ability to restrict viewing of the diagnosis.

For the diagnostic information which a patient can restrict viewing, he or she can choose to enable designated licensed health care professionals, possibly and possibly other licensed health care professionals, possibly and possibly no one.

The role of a user determines their viewing and editing capabilities (role-based access control).

Administrator: The administrator assigns medical identification numbers and passwords to LHCPs.

Licensed Health Care Professional (LHCP): A licensed health care professional that is allowed by a particular patient to view all approved medical records.

An unlicensed personnel can enter and edit demographic information, diagnosis, office visit notes and other medical information, and can view records.

When a person logs into iTrust, if he or she is a personal representative, they view their own records or those of the person or people they are representing.

Public Health Agent: A person legally authorized view and respond to reports of adverse events.

The HCP does not have the ability to enter or edit or view the patient's security question or password.

A deactivated patient can not be modified or log into the system, and can only be reactivated by the administrator.

A user enters their MID and their password to gain role-based entry into the iTrust Medical Records system or requests that their password be changed .

A patient or personal health representative may enter or edit their own demographic information including their security question or answer according to data format 6.1.

HCP must enter the MID of a patient and then enter or edit demographic information with the exception of the patient's security question or password according to data format 6.1.

The patients can choose to toggle between designating or undesignating any LHCP as being a DLHCP for themselves.

The patient chooses to view his or her access log or that for a person for whom they are a personal health representative.

The resulting list should include the following for each access: name of non-DLHCP accessor (with a link to contact information if the viewer is an LHCP), role of non-DLHCP accessor relative to the patient, date and time of access, transaction Type (See Data Format 6.3).

A patient or personal health representative chooses to view medical records including family history .

The patient or personal health representative can see patient personal health information (including historical values), immunizations, and office visit information (date, diagnoses, medication, name of attending physician but not notes, laboratory procedures) for (a) their own records and (b) the records for whom the user is a personal representative.

The health care personnel may enter or edit personal health information including editing historical values from Data Format 6.4.1, 6.4.2, 6.4.3, and 6.4.4, immunizations, and office visit information (date, diagnoses, medication, name of attending physician but not notes, laboratory procedures), family history (the MIDs of the patient's mother and father), Body Mass Index (BMI) , and drug allergies .

HCPs can return to an office visit and modify or delete the fields of the office visit .

The HCP can choose to add or remove another registered user as a personal health representative to that patient.

If the LHCP is not one of the patient's DLHCP or the UAP associated with one of their DLHCP, a message is sent to the patient and their personal representative .

A LHCP or ER chooses to view an emergency report and provides an MID .

The LHCP requests a comprehensive patient report for a particular patient .

All diagnoses, including those not normally viewable by the requesting LHCP, see (UC11) and Data Format 6.5.

A patient may view his or her own lab procedure results .

A Lab Technician can view his or her priority queue of lab procedures .

A Lab Technician can record the results of a lab procedure .

An LHCP wants to send a message to a patient possibly and possibly that patient's personal representative or a patient or personal representative wants to send a message to one of their DLHCP or that of a person they are representing .

The patient or representative is presented with a pull down menu of his or her DLHCP.

An LHCP chooses to send a message to a patient or representative (no multiple recipients allowed in a single message).
