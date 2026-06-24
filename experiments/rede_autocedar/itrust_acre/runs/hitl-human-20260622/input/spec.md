# iTrust for ACRE Access-Control Slice

## Dataset And Source Provenance

Dataset: REDE AccessControlModelStudy, `iTrust for ACRE`.

Source files:

- `iTrust/iTrust_requirements_UTF8.txt`
- `labelled data sets/iTrust for ACRE - ac rules.txt`
- `labelled data sets/iTrust for ACRE.xlsx`

Local audit counts for the full labeled export:

- 1160 sentence lines
- 549 access-control sentence lines
- 2270 parsed NLACP triples
- 553 empty-subject triples
- 24 negated triples

This experiment uses a bounded healthcare slice from the introduction,
glossary, UC1, UC2, UC3, UC4, UC6, UC8, UC9, UC10, UC11, and UC13. The goal is
not to formalize all 2270 triples in one run. The goal is to test whether
AutoCedar can convert a realistic medical-records requirements slice into a
reviewed Cedar schema, reviewed verifier signals, and a converged policy
store.

The NLACP triples below are provenance/evaluation evidence, not prewritten
Cedar. AutoCedar should propose schema atoms first and property atoms second.
Do not create schema entities for file paths or section headings.

## Natural-Language Requirements To Formalize

iTrust is a medical-records application. Doctors and other health-care workers
can obtain and share essential patient information and view aggregate patient
data. Non-emergency access must be controlled, all access must be tracked, and
HIPAA-style privacy allows patients to dictate who can access selected
information.

Important actors include Patient, HCP, LHCP, DLHCP, Administrator, Emergency
Responder, UAP, Personal Representative, Public Health Agent, Lab Technician,
Software Tester, and ordinary authenticated User. Important resources include
patient accounts, credentials, demographic information, medical records,
diagnostic information, office visits, access logs, provider designations,
personal-representative relationships, and authenticated sessions.

Approved diagnostic information is diagnostic information that a patient allows
a designated or other licensed health-care professional to view. For selected
diagnostic information, such as mental-illness, substance-abuse, or cosmetic
surgery diagnoses, the patient can restrict viewing. A licensed health-care
professional determines whether the patient is allowed to restrict viewing of a
diagnosis. A patient can enable designated licensed health-care professionals,
other licensed health-care professionals, or no one to view restricted
diagnostic information.

An HCP can create or disable a selected patient. The HCP can enter a patient as
a new user and can edit the patient according to the patient data format, but
the patient MID cannot be edited. The HCP must not enter, edit, or view the
patient's security question or password. A deactivated patient cannot be
modified or log into the system and can only be reactivated by an
administrator.

An administrator can create LHCPs, emergency responders, lab technicians, and
public health agents. An administrator can assign medical identification
numbers and passwords to LHCPs. A LHCP can create UAP users. An administrator
can assign an LHCP to multiple hospitals, choosing only hospitals from the
hospital list.

A user authenticates with MID and password. The user may request a password
change. Authenticated sessions terminate after inactivity, logout, or closing
the application. After the inactivity limit is exceeded, authorization is
disabled. The administrator can set the inactivity period length.

A patient can view all LHCPs the patient has ever had an office visit with and
all LHCPs the patient has designated. A patient can add a LHCP to the patient
provider list. A patient can designate or undesignate any LHCP as a DLHCP for
that patient.

A patient can view their own access log, or the access log for a person for
whom they are a personal representative. Access logs include accessor name,
accessor role relative to the patient, date/time, and transaction type.

A patient or personal representative can view medical records, family history,
personal health information, immunizations, and office-visit information for
their own records and for patients they represent. If a patient or personal
representative has not taken an office-visit satisfaction survey, they may take
the survey; after the survey has been taken, they cannot take or view the
previously submitted survey through that path.

An HCP can enter and edit a patient's personal health records. An HCP can edit
historical values, immunizations, office-visit information, family history, BMI,
and death status for a selected patient. An HCP can document and edit office
visits for a selected patient, including date, hospital, notes, prescriptions,
lab procedures, diagnoses, procedures, immunizations, and referrals. All
medical-record and office-visit events are logged.

An HCP can add or remove another registered user as a personal health
representative for a selected patient. Human review should decide whether this
should be narrowed to a patient-specific DLHCP boundary if the surrounding
requirements imply that stronger constraint.

## Selected NLACP Policy Sentences/Triples

```text
12.0 Doctors can obtain and share essential patient information and view aggregate patient data.
  doctor;obtain;essential patient information - R
  doctor;share;essential patient information - C
  doctor;view;aggregate patient datum - R

16.0 Health care workers can access important patient information; non-emergency access can be controlled and tracked.
  health care worker;access;important patient information - R

18.0 HIPAA rules allow a patient to dictate who can access this information.
  patient;dictate;access who can information - CRUD

20.0 Approved diagnostic information is information a patient allows designated or other LHCPs to view.
  patient;allow;designate view diagnostic information - C
  professional;view;diagnostic information - R

21.0 A patient can restrict viewing on selected diagnostic information.
  patient;restrict;view diagnostic information - C

29.0 The administrator assigns medical identification numbers and passwords to LHCPs.
  administrator;assign;medical identification number - CR
  administrator;assign;password - CR

30.0 A LHCP is allowed by a particular patient to view approved medical records.
  patient;allow;licensed health care professional view all - C
  licensed health care professional;view;all - R

37.0 UAP can enter and edit demographic information, diagnosis, office visit notes, and other medical information, and can view records.
  unlicensed personnel;enter;demographic information - C
  unlicensed personnel;edit;demographic information - U
  unlicensed personnel;view;record - R

68.0 An HCP is able to create a patient or disable a selected patient.
  hcp;create;patient - C
  hcp;disable;patient - U

75.0 Patient MID cannot be edited.
  ;edit;patient;NEG-not - U

76.0 The HCP does not have the ability to enter, edit, or view the patient's security question or password.
  hcp;enter;security question;NEG-not - C
  hcp;edit;security question;NEG-not - U
  hcp;view;security question;NEG-not - R
  hcp;enter;password;NEG-not - C
  hcp;edit;password;NEG-not - U
  hcp;view;password;NEG-not - R

79.0 A deactivated patient cannot be modified or log into the system, and can only be reactivated by the administrator.
  administrator;reactivate;patient - RU

103.0 An admin creates LHCP, ER, lab technician, and public health agent users.
  admin;create;lhcp - C
  admin;create;er - C
  admin;create;laboratory technician - C
  admin;create;public health agent - C

104.0 A LHCP creates a UAP.
  lhcp;create;uap - C

178.0 The patient can view all LHCPs ever visited and those designated.
  patient;view;lhcp - R

183.0 The patient can designate or undesignate any LHCP as a DLHCP.
  patient;designate;lhcp - U
  patient;undesignate;lhcp - U

197.0 The patient views their access log for themself or a represented person.
  patient;view;access log - R

211.0 A patient or personal representative can view medical records and family history.
  patient;view;medical record - R
  personal representative;view;medical record - R

213.0 A patient or personal representative can see personal health information, immunizations, and office-visit information for their own or represented records.
  patient;see;personal health information - R
  personal health representative;see;personal health information - R
  patient;see;immunization - R
  personal health representative;see;immunization - R
  patient;see;office visit information - R
  personal health representative;see;office visit information - R

214.0 A patient or personal health representative may take an office-visit satisfaction survey only before one has already been taken.
  patient;take;survey - C
  patient;choose take;office visit satisfaction survey - R
  personal health representative;choose take;office visit satisfaction survey - R

231.0 An HCP can enter or edit personal health information for a selected patient.
  hcp;enter;personal health information - C
  hcp;edit;personal health information - RU

256.0 An HCP can document or edit an office visit.
  hcp;document;office visit - C
  hcp;edit;office visit - U

296.0 An HCP can add or remove a personal representative for a selected patient.
  hcp;add;personal health representative - C
  hcp;remove;personal health representative - D
```

## Human Review Focus

The key semantic question is whether patient-specific relationships are modeled
directly rather than flattened into role types. DLHCP is not just a global
principal type; it is a licensed professional designated by a particular
patient. Personal representative status is also patient-specific. During
property review, ensure that emergency, designated-provider,
personal-representative, credential-secrecy, deactivated-patient, and logging
boundaries are explicit.
