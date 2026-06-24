# iTrust for Text2Policy Access-Control Slice

## Dataset And Source Provenance

Dataset: REDE AccessControlModelStudy, `iTrust for Text2Policy`.

Source files:

- `Xiao Sources/iTrust for Text2Policy.txt`
- `labelled data sets/iTrust for Text2Policy.txt`
- `labelled data sets/iTrust for Text2Policy.xlsx`

Local audit counts for the full labeled export:

- 471 sentence lines
- 418 access-control sentence lines
- 1070 parsed NLACP triples
- 222 empty-subject triples
- 19 negated triples

This experiment uses a coherent first slice: UC1, UC2, UC3, UC6, UC8,
and UC9. The NLACP triples below are provenance/evaluation evidence, not
prewritten Cedar. AutoCedar should derive a Cedar schema from the natural
language, then derive verifier property atoms from the same intent. Do not
create schema entities for file paths or section headings.

## Natural-Language Requirements To Formalize

The system is iTrust, a medical-records application with role-based access
control. Important actors include HCP, LHCP, DLHCP, administrator, patient,
personal representative, UAP, emergency responder, public health agent, and
ordinary authenticated user. Important resources include patients, personnel,
medical records, demographic information, provider designations, access logs,
sessions, credentials, and provider lists.

An HCP can create a patient and enter the patient as a new user of the system.
Only the patient's name and email are initially provided by the HCP. The HCP
can edit patient data according to the data format, but the patient's MID must
not be editable.

The HCP must not enter, edit, or view the patient's security question or
password.

An administrator can create LHCPs, emergency responders, and public health
agents. An administrator can enter LHCPs, emergency responders, and public
health agents as users of the system. The administrator must specify the
specialty for a new LHCP. The administrator can assign an LHCP to multiple
hospitals and choose the hospitals. A LHCP can create UAP users.

Any user can enter their MID and password to gain role-based entry into
iTrust. Any user can request a password change. An authenticated session ends
when the user logs out or closes the application. Electronic sessions must
terminate after the configured inactivity period; after the inactivity limit is
exceeded, all authorization is disabled. The administrator can set the
inactivity period length.

A patient can view all LHCPs the patient has ever had an office visit with and
all LHCPs the patient has designated. A patient can add a LHCP/HCP to their
provider list by searching by name, specialty, and optionally zip code. A
patient can designate any LHCP as a DLHCP for that patient and can
undesignate any LHCP as a DLHCP for that patient.

A patient can view the patient's own access log. The patient can choose a
beginning and end date for the access-log period. The access-log result
contains the accessor name, the accessor role relative to the patient, the
access timestamp, and the transaction type.

A patient or personal representative may view medical records including family
history. A patient or personal representative can see patient personal health
information, immunizations, and office-visit information for their own records
and for records of patients for whom the user is a personal representative.

## Selected NLACP Policy Sentences/Triples

```text
2.0 An HCP creates patients.
  hcp;create;patient - C

5.0 The HCP can edit the patient according to data format.
  hcp;edit;patient - U

7.0 The patient's MID can not be edited.
  ;edit;mid;NEG-not - U

8.0 The HCP does not have the ability to enter the patient's security question and password.
  hcp;enter;security question;NEG-not - C
  hcp;enter;password;NEG-not - C

9.0 The HCP does not have the ability to edit the patient's security question and password.
  hcp;edit;security question;NEG-not - U
  hcp;edit;password;NEG-not - U

10.0 The HCP does not have the ability to view the patient's security question and password.
  hcp;view;security question;NEG-not - R
  hcp;view;password;NEG-not - R

12.0 An admin creates a LHCP, an ER and a public health agent.
  admin;create;lhcp - C
  admin;create;er - C
  admin;create;public health agent - C

13.0 A LHCP creates UAPs.
  lhcp;create;uap - C

19.0 The administrator shall be allowed to assign a LHCP to multiple hospitals.
  administrator;assign;lhcp - R
  administrator;assign;hospital - CRUD

23.0 A user enters their MID and their password to gain role-based entry into iTrust.
  user;enter;mid - R
  user;enter;password - R

24.0 A user can request to change their password.
  user;request change;password - C

26.0 An authenticated session ends when the user logs out or closes the iTrust application.
  user;log out;itrust application - E
  user;close;itrust application - E

28.0 The administrator is allowed to set the length of this period of time.
  administrator;set;length

49.0 The patient views all LHCPs the patient has ever had an office visit with and those whom he or she had designated.
  patient;view;lhcp - R

50.0 The patient can add also a LHCP to their provider list by searching for the name possibly and possibly specialty of a LHCP.
  patient;add;lhcp - R
  patient;add;provider list - CRU

54.0 The patient can designate any LHCP as being a DLHCP for them.
  patient;designate;lhcp - U

55.0 The patient can undesignate any LHCP as being a DLHCP for them.
  patient;undesignate;lhcp - U

60.0 The patient views his access log.
  patient;view;access log - R

66.0 A patient or personal representative may view medical records including family history.
  patient;view;medical record - R
  personal representative;view;medical record - R
  patient;view;family history - R
  personal representative;view;family history - R

67.0 The patient or personal representative can see patient personal health information, immunizations, and office visit information for their own records and the records for whom the user is a personal representative.
  patient;see;personal health information - R
  personal representative;see;personal health information - R
  patient;see;immunization - R
  personal representative;see;immunization - R
  patient;see;office visit information - R
  personal representative;see;office visit information - R
```

## Human Review Focus

During schema review, pay attention to whether DLHCP is modeled as a separate
principal type or as a patient-specific designation relationship. During
property review, ensure that patient-owned records, represented-patient
records, designated-provider access, credential secrecy, and inactivity-session
boundaries are explicit rather than approximated by generic role checks.
