## Department of Veterans Affairs Chapter 33 Long Term Solution (LTS) Web Service (WS) VA/DoD Identity Repository (VADIR)

## Demographics

Interface Control Document

<!-- image -->

## Version 2.1.1 March 2022

## Revision History

| Date          | Version   | Description                                                                                                                                                                                    | Author                       |
|---------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|
| March 2022    | 2.1.1     | Renamed MGAB table to MGIB to match output. Explicitly stated SSN required for findPersonByCriteria method. Added notes describing missing code value behavior to lookup table entry sections. | Patrick Lewis                |
| November 2021 | 2.1       | Revisions for 2.1                                                                                                                                                                              | Patrick Lewis                |
| June 2021     | 2.0.4     | Revisions for 2.0.4                                                                                                                                                                            | Patrick Lewis (Halfaker)     |
| March 2021    | 2.0.3     | Revisions reflect 2.0.3 rewritten service and changes from previous.                                                                                                                           | Patrick Lewis (Halfaker)     |
| October 2019  | 2.0       | Revised ICD. Updated POC in table1                                                                                                                                                             | Bruce Makinney, Sandeep Kaur |
| 3/2/2018      | 1.3       | Updated for new endpoints, security fixes.                                                                                                                                                     | CSRA                         |
| 12/2/2016     | 1.0       | Added data element tables for Service Period and getKicker Info operations                                                                                                                     | SRA International, Inc.      |
| 09/12/2016    | 0.1       | Added additional fields to ActiveService & TrainingPeriod, and additional fields CallStatus, CallStatusNote to SearchResults.                                                                  | SRA International, Inc.      |

## 1. Introduction

Chapter 33 of the Montgomery GI Bill (MGIB) is an education benefits program created by Congress in July 2008. Formally titled the Post/911 Montgomery GI Bill, Chapter 33 provides education benefits for service members and Veterans who have served on Active Duty for 90 or more days since September 10, 2001. Veterans who qualify for Chapter 33 benefits are eligible to receive up to 100% payment of tuition and fees for education and training programs taken through accredited colleges or universities; a monthly housing stipend; up to $1,000 a year for books and supplies; a relocation allowance; and reimbursement for certification, licensing, work-study programs, or tutorial assistance. After meeting specific eligibility requirements, Veterans can also transfer their unused benefits to their spouses and dependents.

The Chapter 33 Long Term Solution (LTS) is a web service that automates the processing of the complex eligibility calculations and completion of forms for Chapter 33 claims.  Chapter 33 LTS is used to establish eligibility, determine payment, or disallow a claim should eligibility requirements or some other validating factor not be met. Automation of Chapter 33 claims benefits the Department of Veterans Affairs (VA) and Veterans by providing efficient and streamlined determination of eligibility, accurate calculation of payments, and timely distribution of benefits to the Veterans and to the institutions that serve Veteran education needs.

## 1.1. Purpose

This Interface Control Document (ICD) describes the software interface between the VA/Department of Defense (DoD) Identity Repository (VADIR) and Chapter33 LTS through the VADIR Chapter 33 Web Service. The purpose of the ICD is to specify interface requirements to be met by the participating systems. It describes the concept of operations for the interface, defines the message structure and protocols which govern the interchange of data, and identifies the communication paths along which the data is expected to flow.

## 1.2. Scope

This ICD specifies the interface(s) between VADIR and Chapter 33 LTS. Upon formal approval by each participating system, this ICD shall be incorporated into the requirements baseline for each system. This document provides details on the functional, performance, operational, and design requirements for the interface between VADIR and Chapter 33 LTS. This document describes the web service parameters and record layouts for the data that VADIR exposes for consumption by Chapter 33 LTS. It is intended for use by all parties requiring such information, including software developers, system designers, and testers responsible for implementing the interface.

## 1.3. System Identification

This ICD describes the interface between VADIR and Digital GI Bill.

## VADIR

Table 1: VADIR System Information

| System                | Details                    |
|-----------------------|----------------------------|
| Identification number | 1682                       |
| Title                 | VA/DoD Identity Repository |
| Abbreviation          | VADIR                      |
| Version number        | 1.0                        |
| Release number        | 1.0                        |
| Point of Contact      | Alexander V. Torres        |

## Digital GI Bill

Table 2: Digital GI Bill System Information

| System                | Details         |
|-----------------------|-----------------|
| Identification number | 2745            |
| Title                 | Digital GI Bill |
| Abbreviation          | DGIB            |
| Version number        | N/A             |
| Release number        | 1.0             |
| Point of Contact      | Riley Ross      |

## 1.4. Operational Agreement

This ICD provides the specification for an interface between Chapter 33 LTS and VADIR regarding demographics data requirements. The Chapter 33 LTS Project Manager is responsible for notifying the vendor and the VADIR Project Manager of any potential or planned changes to data feeds, once these changes are known, to minimize adverse impacts on Chapter 33 LTS and VADIR.

Chapter 33 LTS developers and users are expected to protect VADIR data in accordance with the Privacy Act and Trade Secrets Act guidelines. The following considerations will be made when conducting interfacing operations with VADIR:

Chapter 33 LTS agrees not to misuse or disclose Personally Identifiable Information (PII) other than as permitted or required by this Agreement or as Required by Law;

Chapter 33 LTS agrees to use appropriate safeguards to prevent use or unauthorized disclosure of the personal information other than as defined in this Agreement;

Chapter 33 LTS agrees to mitigate, to the extent practicable, any harmful effect that is known to VADIR of misuse or unauthorized disclosure or breach of PII by any Business Partner in violation of the requirements of this Agreement;

Chapter 33 LTS agrees to immediately report to the Intellectual Property Enforcement Officer (IPEO), and the Austin Information Technology Center (AITC) Information Security Officer (ISO), or VADIR ISO any misuse or disclosure of the PII not provided for by this Agreement of which it becomes aware, thereby triggering AITC to trigger their incident response procedures, which includes notifying all stakeholders; and,

Chapter 33 LTS agrees to ensure that any agent, including a subcontractor, to whom it provides protected information received from VADIR, agrees to the same restrictions and conditions that apply through this Agreement to Chapter 33 LTS with respect to such information.  Chapter 33 LTS further accepts responsibility to ensure that these agents comply with VA regulations regarding privacy training and rules of behavior.

## 2. Interface Definition

This software interface provides the necessary data exchange between VADIR and Chapter 33 LTS to facilitate the population and display the agreed upon data feed to support data required from VADIR to Chapter 33 LTS.

VADIR uses the Simple Object Access Protocol (SOAP) protected by Transport Layer Security (TLS) between the Chapter 33 LTS and VADIR servers after mutual authentication has been established. Data transferred under this agreement includes Service Members 'military service information as well as information concerning their eligibility for, participation in, and utilization of several Education benefits which existed prior to implementation of the Post-9/11 MGIB program.  These included Chapter 30 (Active Component), Chapter 1606 (Selected Reserve), and Chapter 1607 (REAP) as well as utilization and payment information from the VBA Benefits Delivery Network (BDN).

Details of data transferred and of the Extensible Markup Language (XML) schema file are included in this ICD and defined in section 5.

## 2.1. System Overview

VADIR was established to support the OneVA/DoD data-sharing initiative to consolidate data transfers between the DoD and VA.  DoD's Defense Manpower Data Center (DMDC) stages shared data in a VAspecific satellite database, as defined in a Joint DoD/VA Memorandum of Understanding (MOU), and replicates it to a VA data repository called VADIR. This data is then available to VA organizations to assist in determining Veterans' eligibility for benefits as well as to analyze the total Veteran population for other strategic needs.

VADIR contains Service Member Demographics data, including biographical, military history and contact information. This information is utilized by various applications hosted within the VA.

## 2.2. Interface Overview

The interface utilizes a SOAP message over HTTPS with bi-directional certificate validation based on VA-issued and commercial certificates; this allows the interface to identify and authorize the server-toserver communications to a specific endpoint identified by a Uniform Resource Locator (URL). TLS provides the message's confidentiality and integrity between the endpoints.

The Ch33 Person Service consists of the following operations:

-  getPerson - Returns DoD biographical information.
-  getContactInfo - Returns DoD-provided mailing address and phone number.
-  findPeopleByCriteria - Returns a maximum of fifty results that meet the supplied search criteria.
-  getServicePeriods - Returns DoD military service including service periods, exclusion periods, training periods, Guard/Reserve activation periods, Career Intermission Plan (CIP) participation, Ch30 eligibility information, Ch1606 eligibility information, Military affiliation and duty status, Military Academy periods, payments and used eligibility for multiple education programs, and Purple Heart information.
-  getKickerInfo - Returns Ch30/Ch1606 kicker amounts previously awarded.

## 2.3. Data Transfer

The data transfer between Chapter 33 LTS and VADIR is accomplished via a Java web service. Queries are performed against the VADIR database using appropriate uniquely identifying input, generally the individual's DoD Electronic Data Exchange Person Identifier (EDIPI).  VADIR fetches the different data sets and provides the data using the structures and field names specified in Section 5 of this document.

Occasionally DMDC adds new codes and send them to VADIR. These new codes will be transferred to DGIB. However, the codes will transfer and display in the payload but the descriptions won't until the look up table is updated.

## 2.4. Transaction Types

This interface does not require any transaction types.

## 2.5. Data Exchanges

Chapter 33 LTS provides the initial data exchange through a WSDL:

VSCH33Service?wsdl has several operations where:

- a. Chapter 33 LTS provides identity traits (SN) to fetch the Veteran information from the VADIR findPeopleByCriteria operation. VADIR returns one or more records with Demographic Information.
- b. Chapter 33 LTS provides EDIPI to the VADIR getContactInfo operation to fetch complete Demographic Information.
- c. Chapter 33 LTS provides EDIPI to the VADIR getPerson operation to fetch complete Person Information.
- d. Chapter 33 LTS provides EDIPI to the VADIR getServicePeriods operation to fetch ServicePeriod and education-specific Information.
- e. Chapter 33 LTS provides EDIPI to the VADIR getKickerInfo operation to fetch KickerInfo Response Information.

Two new fields, callStatus &amp; callStatusNote, have been added to all Response objects:

- a. callStatus field contains either 'Success' or 'Error' with a numerical error code.
- b. callStatusNote field provides a text description of the error.

Please refer to Section 6.1.1 for additional details on callStatus and callStatusNote.

## 2.6. Precedence and Criticality

Accurate client data is necessary to make informed decisions. As such, accuracy is assigned the highest priority and takes precedence over all conflicting interface requirements.

## 2.7. Communications Methods

The communication between VADIR and the service providers' systems is based on the SOAP over HTTPS protocol after a bi-directional TLS certificate validation.

## 2.8. Performance Requirements

Payload shall be returned in no more than 2 seconds.

## 2.9. Security

This data transmission interface complies with Federal Information Processing Standards (FIPS) Publication 199. The following confidentiality, integrity and availability categorizations have been laid out regarding the transfer and handling of data germane to Chapter 33 LTS:

Confidentiality of Data:

High

Integrity of Data:

High

Availability of Data:

Moderate

These categories also mirror similar National Institute of Standards and Technology (NIST) Special Publication 800-60 standards to which VADIR adheres.

## 3. Interface Requirements

## 3.1. Chapter 33 LTS Interface Requirements

## Interface Processing Time Requirements

Payload shall be returned in no more than 2 seconds.

## Message/File Requirements

The data is exchanged using an XML format. Details for the format of the message containing the data can be found in Section 4 - Interface Verification.

## Constraints

Not Applicable.

## Interface Initiation

Chapter 33 LTS initiates by invoking operations on the VSCH33Service?WSDL

Table 3:  WSDL Names and Operation Names

| WSDL Name          | Operation Name       |
|--------------------|----------------------|
| VSCH33Service?WSDL | getPerson            |
| VSCH33Service?WSDL | getContactInfo       |
| VSCH33Service?WSDL | findPeopleByCriteria |
| VSCH33Service?WSDL | getServicePeriods    |
| VSCH33Service?WSDL | getKickerInfo        |

## Flow Control

This interface, although initialized from Chapter 33 LTS, is controlled via the implemented control methods utilized in the VADIR web service.

## Security Requirements

The interface is designed to utilize HTTPS with bi-directional certificate validation.

Mutual TLS Authentication is used with VA issued certificates to identify and authorize server-to-server communications to a specific endpoint identified by a URL where your services reside. TLS encrypts the request and return messages, providing confidentiality and integrity between the endpoints.

Current security requirements include a minimum of TLSv1.1 for network transport and SHA2 encryption inside the certificates. Additional restrictions and ongoing mitigation are in place as part of the CRISP process which maintains this application at a state acceptable with VA security standards.

## 4. Interface Verification

The following qualification methods will be used to verify that requirements have been met:

-  Demonstration: Ensuring that the VSCH33Service?WSDL is accessible at end points as listed in Section 5, demonstrating that the service is properly deployed and accessible from requesting entities.
-  Test: Once the accessibility of endpoints is established, run through the SOAP UI test to validate that the request is processed successfully, and a corresponding response is generated.
-  Analysis: Verify that the SOAP response has all the fields/data elements as described in Section 5.
-  Inspection: Cross check SOAP response against the VADIR DB, ensuring that the data conforms to what is present in the VADIR DB.

## 5. Web Service

## 5.1. End Points

The following URLs identify the service in each environment:

| Environment   | Endpoint URL                                                    |
|---------------|-----------------------------------------------------------------|
| Dev/Test/PIT  | https://vaausvdrapppit.aac.va.gov/vdrCH33/v2/VSCH33Service?WSDL |
| PreProd       | https://vaausvdrapppp.aac.va.gov/vdrCH33/v2/VSCH33Service?WSDL  |
| Production    | https://vavdrappprd.va.gov/vdrCH33/v2/VSCH33Service?WSDL        |

Table 4: VADIR's Person PortType from VSCH33Service?WSDL

| Operation            | Input                | Output                       |
|----------------------|----------------------|------------------------------|
| getPerson            | getPerson            | getPersonResponse            |
| getContactInfo       | getContactInfo       | getContactInfoResponse       |
| findPeopleByCriteria | findPeopleByCriteria | findPeopleByCriteriaResponse |
| getServicePeriods    | getServicePeriods    | getServicePeriodsResponse    |
| getKickerInfo        | getKickerInfo        | getKickerInfoResponse        |

Note: All input parameters are required unless optional is indicated.

## getPerson Request

Table 5: VADIR's getPerson  Request

| Field    | Type   | Format          | Field Description                      |
|----------|--------|-----------------|----------------------------------------|
| personId | String | 10-digit number | EDIPI of the Veteran or Service Member |

## getPerson Response

The following tables contain the getPerson response elements and structure.

Table 6: VADIR's getPerson Response

| Field          | Field Type   | Format                       | Description                                  |
|----------------|--------------|------------------------------|----------------------------------------------|
| Results        | Person       | Refer to Person Data Element | zero or more Persons as retrieved from VADIR |
| callStatus     | String       | Refer to section 6.1.1       | Refer to section 6.1.1                       |
| callStatusNote | String       | Refer to section 6.1.1       | Refer to section 6.1.1                       |

## findPeopleByCriteria Request

The following illustrates the findPeopleByCriteria request elements and structure.

Note: SSN is a required field.

Table 7: VADIR's findPeopleByCriteria Request

| Field             | Type   | Format                                       | Field Description                                                  |
|-------------------|--------|----------------------------------------------|--------------------------------------------------------------------|
| ssn (Required)    | String | 9-digit string value; may have leading zeros | Social Security Number                                             |
| ssnMatchType      | String | 'EQUALS' (Default) or 'STARTS WITH'          | Sets the search mode for ssn from an equals to a ' %; search       |
| firstName         | String | String                                       | First Name                                                         |
| firstResult       | String | 1,0 Default 0                                | 1 indicates 'best guess' for exact match (Deprecated)              |
| lastName          | String | String                                       | Last Name                                                          |
| lastNameMatchType | String | 'EQUALS' (Default) or 'STARTS WITH'          | Sets the search mode for last name from an equals to a ' %; search |
| maxResults        | String | Numeric - defaults to 50 - 200 cut off.      | Number of people allowed to be returned.                           |
| dateOfBirth       | String | YYYY-MM-DD                                   | Date of Birth                                                      |

## findPeopleByCriteria Response

The following tables contain the findPeopleByCriteria response elements and structure.

## Table 8: VADIR's findPeopleByCriteria Response

| Field                      | Field Type    | Format                         | Description                                      |
|----------------------------|---------------|--------------------------------|--------------------------------------------------|
| findPeopleByCriteriaReturn | SearchResults | See SearchResults Data Element | Search results from findPeopleByCriteria Request |

## Table 9: VADIR's SearchResults Data Element:

| Field          | Field Type    | Format                              | Description                                  |
|----------------|---------------|-------------------------------------|----------------------------------------------|
| Results        | ArrayOfPerson | Refer to ArrayOfPerson Data Element | zero or more Persons as retrieved from VADIR |
| availableCount | String        | Integer                             | Number of persons retrieved                  |
| callStatus     | String        | Refer to section 6.1.1              | Refer to section 6.1.1                       |
| callStatusNote | String        | Refer to section 6.1.1              | Refer to section 6.1.1                       |

## Table 10: VADIR's ArrayOfPerson Data Element

| Field   | Field Type   | Format                       | Description                         |
|---------|--------------|------------------------------|-------------------------------------|
| Person  | Person       | Refer to Person Data Element | Person element retrieved from VADIR |

## Table 11: VADIR's Person Data Element

| Field                | Field Type   | Format                      | Description                                                        |
|----------------------|--------------|-----------------------------|--------------------------------------------------------------------|
| callStatus           | String       | Refer to section 6.1.1      | Refer to section 6.1.1                                             |
| callStatusNote       | String       | Refer to section 6.1.1      | Refer to section 6.1.1                                             |
| socialSecurityNumber | String       | 9-digit number              | Social Security Number                                             |
| vaId                 | String       | 10-digit number             | EDIPI of the identified person                                     |
| firstName            | String       | String                      | First Name                                                         |
| middleName           | String       | String                      | Middle Name                                                        |
| lastName             | String       | String                      | Last Name                                                          |
| cadency              | String       | String                      | Addition to name (Jr., Sr., III, etc.); known as 'Suffix'          |
| dateOfBirth          | String       | YYYY-MM-DD                  | Date of Birth                                                      |
| dateOfDeath          | String       | YYYY-MM-DD                  | Date of Death                                                      |
| deathInd             | String       | Single character value      | Y indicates person is deceased even if a date of death is unknown. |
| gender               | String       | 'Male' or 'Female'          | Indicates Gender                                                   |
| Alias                | Alias        | Refer to Alias Data Element | Aliases used by the person                                         |

Table 12: VADIR's Alias Data Element

<!-- image -->

| Field         | Field Type   | Format     | Description    |
|---------------|--------------|------------|----------------|
| firstName     | String       | String     | First Name     |
| lastName      | String       | String     | Last Name      |
| effectiveDate | String       | YYYY-MM-DD | Effective Date |

12

## getContactInfo Request

Table 13: VADIR's getContactInfo Request

| Field    | Field Type   | Format          | Description                                    |
|----------|--------------|-----------------|------------------------------------------------|
| personId | String       | 10-digit number | EDIPI of the request Veteran or Service Member |

## getContactInfoResponse

The following contains getContactInfo response elements and structure.

Table 14: VADIR's getContactInfo Response

| Field                | Field Type         | Format                              | Description                                |
|----------------------|--------------------|-------------------------------------|--------------------------------------------|
| getContactInfoReturn | contactInfoResults | See contactInfoResults Data Element | Search results from getContactInfo Request |

## Table 15: VADIR's ContactInfoResults Data Element

| Field          | Field Type   | Format                            | Description                    |
|----------------|--------------|-----------------------------------|--------------------------------|
| Results        | ContactInfos | Refer to ContactInfo Data Element | ContactInfo results from VADIR |
| callStatus     | String       | Refer to section 6.1.1            | Refer to section 6.1.1         |
| callStatusNote | String       | Refer to section 6.1.1            | Refer to section 6.1.1         |

## Table 16: VADIR's ContactInfos Data Element

| Field       | Field Type   | Format                            | Description                       |
|-------------|--------------|-----------------------------------|-----------------------------------|
| contactInfo | ContactInfo  | Refer to ContactInfo Data Element | Results of ContactInfo from VADIR |

## Table 17: VADIR's ContactInfo Data Element

| Field   | Field Type   | Format                            | Description                         |
|---------|--------------|-----------------------------------|-------------------------------------|
| vaId    | String       | 10-digit number                   | EDIPI of the Veteran                |
| address | AddressType  | Refer to AddressType Data Element | Address of the Veteran              |
| Phone   | Phone        | Refer to phone Data Element       | Phone Number details of the Veteran |

## Table 18: VADIR's AddressType Data Element

| Field         | Field Type   | Format     | Description            |
|---------------|--------------|------------|------------------------|
| effectiveDate | String       | YYYY-MM-DD | Effective Date         |
| addressLine1  | String       | String     | Address of the Veteran |
| addressLine2  | String       | String     | Address of the Veteran |

| Field            | Field Type   | Format                    | Description                        |
|------------------|--------------|---------------------------|------------------------------------|
| city             | String       | String                    | Name of the city                   |
| state            | String       | two-character state code  | USPS two-letter code for the State |
| zipcode          | String       | 5-digit zipcode           | Zipcode                            |
| zipcodeExtension | String       | 4-digit zipcode extension | Zipcode extension                  |
| countryCode      | String       | 2-character country code  | FIPS Country code                  |

Table 19: VADIR's Phone Data Element

| Field       | Field Type   | Format                                             | Description                         |
|-------------|--------------|----------------------------------------------------|-------------------------------------|
| phoneNumber | String       | 10-digit phone number                              | Phone Number                        |
| phoneType   | String       | F FAX H Home M Mobile or Cell phone R Relay W Work | Single character code for PhoneType |

## getServicePeriods Request

Table 20: VADIR's getServicePeriods Request

| Field    | Field Type   | Format          | Description                  |
|----------|--------------|-----------------|------------------------------|
| personId | String       | 10-digit number | EDIPI of the request Veteran |

## getServicePeriodsResponse

The following tables contain the getServicePeriods response elements and structure.

Table 21: VADIR's getServicePeriods Response

| Field                    | Field Type            | Format                                 | Description                                    |
|--------------------------|-----------------------|----------------------------------------|------------------------------------------------|
| GetServicePeriodsRetur n | servicePeriodResult s | See servicePeriodResult s Data Element | Search results from getServicePeriod s Request |

Table 22: VADIR's servicePeriodResults Response Data Element

| Field   | Field Type                    | Format                              | Description                            |
|---------|-------------------------------|-------------------------------------|----------------------------------------|
| results | ServicePeriods (Zero to many) | Refer to ServicePeriod Data Element | Service Period results from VADIR      |
| cipEnt  | Cip                           | Refer to cipEnt Data Element        | CIP Program participation information. |

| Field                   | Field Type              | Format                                                                                                                  | Description                                                                                                                                           |
|-------------------------|-------------------------|-------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| callStatus              | String                  | Refer to section 6.1.1                                                                                                  | Refer to section 6.1.1                                                                                                                                |
| callStatusNote          | String                  | Refer to section 6.1.1                                                                                                  | Refer to section 6.1.1                                                                                                                                |
| activeServiceIndicator  | String                  | 'Y' or 'N'                                                                                                              | Indicator of current active Federal service based upon the Military Status which is calculated from the Service Periods                               |
| awards                  | purpleHearts            | Refer to Awards Data Element                                                                                            | Collection of Purple Heart information from VADIR sources.                                                                                            |
| bdnEnts                 | bdnEnts                 | Refer to bdnEnts Data Element                                                                                           | Collection of BDN Entries                                                                                                                             |
| ch1606Ents              | ch1606Ents              | Refer to ch1606Ents Data Element                                                                                        | Collection of Ch1606 Entries                                                                                                                          |
| ch30Ent                 | ch30Ent                 | Refer to ch30Ent Data Element                                                                                           | A single Ch30 Entry describing the requested information from VADIR                                                                                   |
| militaryAcademy Periods | militaryAcademyPerio ds | Refer to militaryAcademy Periods Data Element                                                                           | Collection of Military Academy periods                                                                                                                |
| militaryStatus          | String                  | Two numeric digits from 01 to 16                                                                                        | Codes denoting the military status of the individual based upon examination of their service records. Sometimes called 'Duty Status Code              |
| militaryStatusDesc      | String                  | Free text string                                                                                                        | Description of the Military Status Code                                                                                                               |
| resultsHash             | String                  | Formatted string comprising sha 256 hash of legacy values and sha 256 hash of new values with a '-' char in the middle. | A digital fingerprint for the information retrieved at this time for this person - used for comparisons to previous retrievals to detect data changes |

Table 23: VADIR's ServicePeriod Data Element

| Field                          | Field Type                             | Format                                | Description                                      |
|--------------------------------|----------------------------------------|---------------------------------------|--------------------------------------------------|
| vaId                           | String                                 | 10-digit number                       | EDIPI of the requested Veteran or Service Member |
| eod                            | String                                 | YYYY-MM-DD                            | Enter on Duty (EOD) Date                         |
| rad                            | String                                 | YYYY-MM-DD                            | Release from Active Duty (RAD) Date              |
| basd                           | String                                 | YYYY-MM-DD                            | Basic Active Service Date                        |
| charSvcCd                      | String                                 | See 6.1.2                             | Code value for characterOfService                |
| characterOfService             | String                                 | See 6.1.2                             | CharacterOfService                               |
| pnlCatCd                       | String                                 | See 6.1.6                             | Code corresponding to personnelCagegory          |
| personnelCategory              | String                                 | See 6.1.6                             | Component of Military                            |
| svcCd                          | String                                 | See 6.1.4                             | Code corresponding to Branch of Service          |
| branchOfService                | String                                 | See 6.1.4                             | Military Service                                 |
| mgibCd                         | String                                 | String                                | String value for mgibSeparationCode              |
| mgibSeparationCode             | String                                 | String                                | Separation Code                                  |
| pgibCd                         | String                                 | See 6.1.11                            | Code value for pgibSeparationCode                |
| pgibSeparationCode             | String                                 | See 6.1.11                            | Post-9/11 GI Bill (PGIB) separation description  |
| nrsCd                          | String                                 | See 6.1.12                            | Narrative Reason for Separation Code Value       |
| narrativeReason SeparationCode | String                                 | See 6.1.12                            | Narrative Reason for Separation Description      |
| exclusionPeriod                | ExclusionPeriod (Zero to many allowed) | Refer to ExclusionPeriod data element | Period of non- qualifying service                |
| trainingPeriod                 | TrainingPeriod (Zero to many allowed)  | Refer to TrainingPeriod data element  | Period under which service member is training.   |
| activePeriod                   | ActivePeriod (Zero to many allowed)    | Refer to ActivePeriod data element    | Period of active duty service                    |

Table 24: VADIR's exclusionPeriod Data Element

| Field              | Field Type   | Format                | Description                       |
|--------------------|--------------|-----------------------|-----------------------------------|
| beginDate          | String       | YYYY-MM-DD            | Begin Date                        |
| endDate            | String       | YYYY-MM-DD            | End Date                          |
| exclusionPerdTyp   | String       | 'ROTC' or 'APPELLATE' | Description of the Exclusion type |
| exclusionPerdTypCd | String       | String                | Raw code value for exclusion type |

## Table 25: VADIR's TrainingPeriod Data Element

| Field Name   | Field Type   | Format            | Description                                                                                                                               |
|--------------|--------------|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| beginDate    | String       | YYYY-DD-MM        | Begin Date                                                                                                                                |
| endDate      | String       | YYYY-DD-MM        | End Date                                                                                                                                  |
| projectCode  | String       | See Section 6.1.3 | Data element providing granularity to differentiate between the various contingencies, indicates training period, or indicates AGR Status |

Table 26: VADIR's activePeriod Data Element

| Field Name                    | Field Type   | Format     | Description                                                                                                                  |
|-------------------------------|--------------|------------|------------------------------------------------------------------------------------------------------------------------------|
| beginDate                     | String       | YYYY-MM-DD | Begin Date                                                                                                                   |
| charSvcCd                     | String       | See 6.1.2  | Code for character of service                                                                                                |
| characterOfService            | String       | See 6.1.2  | Description for character of service                                                                                         |
| endDate                       | String       | YYYY-MM-DD | End Date                                                                                                                     |
| statuteCd                     | String       |            | Code value for Statute                                                                                                       |
| Statute                       | String       | See 6.1.3  | The legal authority under which a Guard or Reserve member is called to Active Duty. Required under DoDI 7730.54 Enclosure 8. |
| mgibCd                        | String       |            | Code value for MGIB Separation                                                                                               |
| mgibSeparationCode            | String       |            | Description of MGIB Separation                                                                                               |
| pgibCd                        | String       | See 6.1.11 | Code value for PGIB Separation                                                                                               |
| pgibSeparationCode            | String       | See 6.1.11 | Description of PGIB Separation                                                                                               |
| nrsCd                         | String       | See 6.1.12 | Code value for narrative reason for the member's separation from the Service.                                                |
| narrativeReasonSeparationCode | String       | See 6.1.12 | The narrative reason for the member's separation from the Service.                                                           |
| projectCode                   | String       | See 6.1.3  | Data element providing granularity to differentiate between the various contingencies.                                       |

## Table 27: VADIR's purpleHearts Data Element

| Field Name   | Field Type   | Format                       | Description                      |
|--------------|--------------|------------------------------|----------------------------------|
| purpleHeart  | purpleHeart  | Container for repeating type | Zero to many purpleHeart objects |

## Table 28: VADIR's purpleHeart Data Element

| Field Name           | Field Type   | Format                                | Description                                     |
|----------------------|--------------|---------------------------------------|-------------------------------------------------|
| purpleHeartIndCd     | String       | 'Y' if evidence of purple heart found | Alone if no other data known.                   |
| awardBranchOfService | String       | See 6.1.4                             | Branch of service that awarded the purple Heart |
| awardDate            | String       | YYYY-MM-DD                            | Date medal awarded                              |
| awardServiceCd       | String       | See 6.1.4                             | Code value for awardBranchOfService             |

## Table 29: VADIR's bdnEnts Data Element

| Field Name   | Field Type   | Format                       | Description                 |
|--------------|--------------|------------------------------|-----------------------------|
| bdnEnt       | bdnEnt       | Container for repeating type | Zero to many bdnEnt objects |

## Table 30: VADIR's bdnEnt Data Element

| Field Name           | Field Type   | Format                | Description                                                       |
|----------------------|--------------|-----------------------|-------------------------------------------------------------------|
| bnftLstPmtDt         | String       | YYYY-MM-DD            | Benefit Last Payment Date                                         |
| bnftMasterRecStat    | String       | String                | Code value for bnftMasterRecStatDsc                               |
| bnftMasterRecStatDsc | String       | String                | Benefit Master Record Status                                      |
| eduPgmEntlDelimitDt  | String       | YYYY-MM-DD            | Benefit Program Delimit Date (Date by which benefit must be used) |
| eduPgmEntlDysQy      | String       | Always Zero           | Benefit Entitlement Days Quantity                                 |
| eduPgmEntlMtsQy      | String       | Numeric value 0 to 36 | Benefit Entitlement Months Quantity                               |
| eduPgmTypCd          | String       | '1','2','4','5'       | Program type Code                                                 |

## Table 31: VADIR's ch1606Ents Data Element

| Field Name   | Field Type   | Format                     | Description                    |
|--------------|--------------|----------------------------|--------------------------------|
| ch1606Ent    | ch1606Ent    | See Ch1606Ent Data Element | Zero to many ch1606Ent objects |

Table 32: VADIR's ch1606Ent Data Element

| Field Name    | Field Type   | Format     | Description                    |
|---------------|--------------|------------|--------------------------------|
| mgsrBgnDt     | String       | YYYY-MM-DD | Zero to many ch1606Ent objects |
| mgsrStatCd    | String       | See 6.1.10 | Mgsr Status Code               |
| mgsrStatCdDsc | String       | See 6.1.10 | Mgsr Status Description        |
| mgsrStatCdRsn | String       | See 6.1.10 | Mgsr Status Reason             |
| mgsrStatEffDt | String       | YYYY-MM-DD | Mgsr Status Effective Date     |
| pnlCatCd      | String       | See 6.1.6  | Military Component code        |
| pnlCatCdDsc   | String       | See 6.1.6  | Military Component             |

## Table 33: VADIR's militaryAcademyPeriods Data Element

| Field Name            | Field Type            | Format                       | Description                                |
|-----------------------|-----------------------|------------------------------|--------------------------------------------|
| militaryAcademyPeriod | militaryAcademyPeriod | Container for repeating type | Zero to many militaryAcademyPeriod objects |

## Table 34: VADIR's militaryAcademyPeriod Data Element

| Field Name                | Field Type   | Format     | Description                                                     |
|---------------------------|--------------|------------|-----------------------------------------------------------------|
| beginDate                 | String       | YYYY-MM-DD | Date academy participation began                                |
| branchOfService           | String       | See 6.1.4  | Name of service for the academy                                 |
| commissionBranchOfService | String       | See 6.1.4  | Name of service into which the person was commissioned.         |
| commissionSvcCd           | String       | See 6.1.4  | Service code of service into which the person was commissioned. |
| endDate                   | String       | YYYY-MM-DD | Date academy participation ended                                |
| svcCd                     | String       | See 6.1.4  | Service code of academy                                         |

## Table 35: VADIR's ch30Ent Data Element

| Field Name        | Field Type   | Format        | Description                                                           |
|-------------------|--------------|---------------|-----------------------------------------------------------------------|
| branchOfService   | String       | See 6.1.4     | Branch of Service under which entitlement secured.                    |
| ch30EnrlStatCd    | String       | See 6.19      | Ch 30 DoD Status Code                                                 |
| ch30EnrlStatCdDsc | String       | See 6.19      | Ch 30 DoD Status Description                                          |
| charSvcCd         | String       | See 6.1.2     | Character of Service Code                                             |
| charSvcCdDsc      | String       | See 6.1.2     | Character of Service Description                                      |
| eduLvlCd          | String       | See 6.1.8     | Education Level Code                                                  |
| eduLvlCdDsc       | String       | See 6.1.8     | Education Level Description                                           |
| entlDt            | String       | YYYY-MM-DD    | Entitlement Date                                                      |
| eod               | String       | YYYY-MM-DD    | Entered on Duty Date                                                  |
| mgadBprAm         | String       | Numeric value | Basic Pay Reduction Amount                                            |
| mgadCtrbAm        | String       | Numeric value | Contribution Amount                                                   |
| mgadEnlYrs        | String       | Numeric value | The length in years of the current enlisted active service agreement. |

| Field Name       | Field Type   | Format     | Description                                                       |
|------------------|--------------|------------|-------------------------------------------------------------------|
| mgadLossCatCd    | String       | See 6.1.7  | A code derived from the Separation Program Designator (SPD) code. |
| mgadLossCatCdDsc | String       | See 6.1.7  | Description of mgadLossCatCd                                      |
| rad              | String       | YYYY-MM-DD | Release from Active-Duty Date                                     |
| svcCd            | String       | See 6.1.4  | Code for Branch of Service                                        |

## Table 36: VADIR's cip Data Element

| Field Name   | Field Type   | Format      | Description                                                                                         |
|--------------|--------------|-------------|-----------------------------------------------------------------------------------------------------|
| cipInd       | String       | 'Y','N','X' | Yes, No, or No record (X). If this field is X the other date fields do not apply and are not shown. |
| cipBgnDt     | String       | YYYY-MM-DD  | Beginning of Sabbatical                                                                             |
| cipEndDt     | String       | YYYY-MM-DD  | End of Sabbatical                                                                                   |

## getKickerInfo Request

Table 37: VADIR's getKickerInfo Request

| Field    | Field Type   | Format          | Description                  |
|----------|--------------|-----------------|------------------------------|
| personId | String       | 10-digit number | EDIPI of the request Veteran |

## getKickerInfo Response

Table 38: VAIDR's kickerInfoResults Data element

| Field          | Field Type   | Format                       | Description               |
|----------------|--------------|------------------------------|---------------------------|
| results        | kickerinfos  | See kickerInfos Data Element | Container for the results |
| callStatus     | String       | Refer to section 6.1.1       | Refer to section 6.1.1    |
| callStatusNote | String       | Refer to section 6.1.1       | Refer to section 6.1.1    |

Table 39: VADIR's kickerInfos Data element

| Field      | Field Type   | Format                             | Description                                                                               |
|------------|--------------|------------------------------------|-------------------------------------------------------------------------------------------|
| kickerInfo | kickerinfo   | See kickerInfoResults Data Element | Container for the repeating element of kicker information for the veteran described below |

Table 40: VADIR's KickerInfo Data Element

| Field                 | Field Type   | Format                                     | Description                                                                       |
|-----------------------|--------------|--------------------------------------------|-----------------------------------------------------------------------------------|
| service               | String       | See 6.1.4                                  | A Single character that maps to a service type as described in the Format column. |
| component             | String       | See 6.1.6                                  | A single character that maps to a valid value as depicted in Format column.       |
| kickerType            | String       | Valid values are CH30 Kicker CH1606 Kicker | KickerType with a value of either CH30 Kicker or CH1601                           |
| kickerRateCode        | String       | See Section 6.1.5                          | A 2-letter code with a value as shown in Format column.                           |
| kickerDescription     | String       | String                                     | Description of the Kicker                                                         |
| beginDate             | String       | YYYY-MM-DD                                 | Begin Date                                                                        |
| endDate               | String       | YYYY-MM-DD                                 | End Date                                                                          |
| eligibilityStatus     | String       | String                                     | Eligibility Status                                                                |
| eligibilityStatusDate | String       | YYYY-MM-DD                                 | Eligibility Status Date                                                           |

## 6. Data Specification

Note: Though codes and expected values are listed here and are current as of the date of this document, this is not an exhaustive list. More codes can and will be added as the DoD and DMDC see fit in order to adequately track the careers and activities of military personnel and operations.

## callStatus Data Elements

Table 41: CallStatus and CallStatusNote Details

| callStatus     | callStatusNote                                                                                         |
|----------------|--------------------------------------------------------------------------------------------------------|
| Error 16820001 | Invalid Search Criteria. Verify input value for SSN/EDIPI                                              |
| Error 16820002 | Null Condition. Please contact VADIR Services Support                                                  |
| Error 16820003 | Error in Database Call. Please contact VADIR Services Support                                          |
| Error 16820004 | Error during transformation. Please contact VADIR Services Support                                     |
| Error 16820005 | General Error. Please contact VADIR Services Support - <additional information about unexpected error> |
| Success        | Person Not Found                                                                                       |
| Success        | No Data Found                                                                                          |
| Success        | Success                                                                                                |

## Character of Service Codes

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Note: Character of service is the lone exception to this rule as unknown or blank character of service codes are assumed to be honorable.  In this instance, the description may be honorable while the code accurately represents the blank that comes from the Database.

Table 42: Character of Service Codes

| Code   | Value                                |
|--------|--------------------------------------|
| A      | Honorable                            |
| B      | Under honorable conditions (general) |

| Code   | Value                                                        |
|--------|--------------------------------------------------------------|
| D      | Bad conduct                                                  |
| E      | Under other than honorable conditions                        |
| F      | Dishonorable                                                 |
| H      | Under honorable conditions (absence of a negative report)    |
| J      | Honorable for VA Purposes (Administrative use by VA only)    |
| K      | Dishonorable for VA Purposes (Administrative use by VA only) |
| Y      | Uncharacterized                                              |
| Z      | Unknown                                                      |

## Project Codes

The service returns a project code but does not return the description. The descriptions are provided in the table below for reference.

Where Training = Y the activation is for training and displayed as training.

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 43: Project Codes

| Code   | Description                                            | Training Indicator   |
|--------|--------------------------------------------------------|----------------------|
| 3AX    | Southwest Border Support                               | N                    |
| 3AZ    | COVID-19 Response                                      | N                    |
| 3GC    | Deepwater Horizon                                      | N                    |
| 3HQ    | Operation Unified Assistance (OUA) (West Africa/Ebola) | N                    |
| 3HS    | Operation Freedom's Sentinel                           | N                    |
| 3JH    | Mexico Wildland Firefighting                           | N                    |
| 3JO    | Border Patrol (Jump Start)                             | N                    |
| 3JT    | Unified Response (Haiti)                               | N                    |
| 9BU    | Southern Watch/Desert Thunder                          | N                    |
| 9EC    | Uphold Democracy (Haiti)                               | N                    |
| 9EV    | Joint Endeavor/Guard                                   | N                    |
| 9FC    | UNKNOWN - IGNORE                                       | N                    |
| 9FF    | Joint Forge                                            | N                    |
| 9FS    | Allied Force                                           | N                    |
| 9FV    | Joint Guardian                                         | N                    |
| 9GF    | Overseas Contingency Operation (OCO)                   | N                    |
| 9GY    | Hurricane Katrina (Aug 31, 2005)                       | N                    |
| 9HA    | Hurricane Ophelia (Wilma Sep 14, 2005)                 | N                    |
| 9HB    | Hurricane Rita (Sep 21, 2005)                          | N                    |
| 9HC    | Pakistan                                               | N                    |
| 999    | Unknown                                                | N                    |
| A20    | AD - ADT - IADT                                        | Y                    |
| A21    | AD - ADT - AT                                          | Y                    |
| A22    | AD - ADT - OTD                                         | Y                    |

| Code   | Description                                                                   | Training Indicator   |
|--------|-------------------------------------------------------------------------------|----------------------|
| A25    | AD - ADOT - ADOS                                                              | N                    |
| A26    | AD - ADOT - AGR                                                               | N                    |
| A27    | AD - ADOT - Involuntary                                                       | N                    |
| A28    | AD - Other                                                                    | N                    |
| A99    | AD - Unknown (derived period)                                                 | N                    |
| B21    | FTNG - AT                                                                     | Y                    |
| B22    | FTNGD - OTD                                                                   | Y                    |
| B25    | FTNGD - OS                                                                    | N                    |
| B26    | FTNGD - AGR                                                                   | N                    |
| B27    | FTNGD - Involuntary                                                           | N                    |
| B99    | FTNGD - Unknown (derived period)                                              | N                    |
| HSM    | Hurricane Maria                                                               | N                    |
| HSN    | Hurricane Nate                                                                | N                    |
| TSH    | Hurricane Harvey                                                              | N                    |
| TSI    | Hurricane Irma                                                                | N                    |
| X10    | Major Disaster Category                                                       | N                    |
| Y10    | Army Reserve Disaster or Emergency Event                                      | N                    |
| Y11    | Navy Reserve Disaster or Emergency Event                                      | N                    |
| Y12    | Marine Reserve Disaster or Emergency Event                                    | N                    |
| Y13    | Air Force Reserve Disaster or Emergency Event                                 | N                    |
| Y30    | USCGR Collector (Disaster or Emergency Event)                                 | N                    |
| Y60    | USCGR Southwest Border                                                        | N                    |
| Y61    | USCGR COVID-19 Response (Unverified)                                          | N                    |
| P01    | PHS Reserve Voluntary initial active duty training                            | Y                    |
| P02    | PHS Reserve Voluntary training                                                | Y                    |
| P05    | PHS Reserve Operational Use                                                   | N                    |
| PA1    | (Not Final) Public Health Emergency                                           | N                    |
| PA2    | (Not Final) Public Health Emergency                                           | N                    |
| PB1    | (Not Final) PHS Reserve National Emergency (Title 50)                         | N                    |
| PB2    | (Not Final) PHS Reserve National Emergency (Title 50)                         | N                    |
| VAB    | Record reported by VA from VBA Legacy BIRLS Data - No DoD Project Code Exists | N                    |

## Statute Codes

Table 44: Statute Codes

| Code   | Description                   |
|--------|-------------------------------|
| A      | Section 688 of 10 U.S.C.      |
| B      | Section 12301(a) of 10 U.S.C. |
| C      | Section 12301(d) of 10 U.S.C. |
| D      | Section 12302 of 10 U.S.C.    |
| E      | Section 12304 of 10 U.S.C.    |
| F      | Section 331 of 14 U.S.C.      |
| G      | Section 359 of 14 U.S.C.      |
| H      | Section 367 of 14 U.S.C.      |
| I      | Section 12406 of 10 U.S.C.    |
| J      | Section 502(f) of 32 U.S.C.   |

| Code   | Description                                    |
|--------|------------------------------------------------|
| K      | Section 12301(h) of 10 U.S.C.                  |
| L      | Section 712 of 14 U.S.C.                       |
| M      | Section 12301(b) of 10 U.S.C.                  |
| N      | Section 502(f)(1)(B) of 32 U.S.C.              |
| O      | Section 10147 of 10 U.S.C.                     |
| P      | Section 502(a) of 32 U.S.C.                    |
| Q      | Section 502(f)(1)(A) of 32 U.S.C.              |
| R      | Section 12322 of 10 U.S.C.                     |
| S      | Section 12301(g) of 10 U.S.C.                  |
| T      | Section 10148 of 10 U.S.C.                     |
| U      | Section 12303 of 10 U.S.C.                     |
| V      | Section 322 of 10 U.S.C.                       |
| W      | Section 333 of 10 U.S.C.                       |
| X      | Section 12402 of 10 U.S.C.                     |
| Y      | Section 802 of 10 U.S.C.                       |
| Z      | Unknown (for use with Project Code A99 or B99) |
| 1      | Section 12304(a) of 10 U.S.C.                  |
| 2      | Section 12304(b) of 10 U.S.C.                  |
| 3      | Section 12323 of 10 U.S.C.                     |
| 4      | Section 251 of 10 U.S.C.                       |
| 5      | Section 688A of 10 U.S.C.                      |
| 6      | Section 204(c)(2)(A) of 42 U.S.C.              |
| 7      | Section 204(c)(2)(C) of 42 U.S.C.              |
| 8      | Section 204(c)(2)(D) of 42 U.S.C.              |
| 9      | Section 204(c)(2)(B) of 42 U.S.C.              |

## Service Codes and Names/Descriptions

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 45: Service Codes

| Code   | Value                                           |
|--------|-------------------------------------------------|
| 1      | Foreign Army                                    |
| A      | Army                                            |
| C      | Coast Guard                                     |
| D      | Office of the Secretary of Defense              |
| F      | Air Force                                       |
| H      | Public Health Service                           |
| M      | Marine Corps                                    |
| N      | Navy                                            |
| O      | National Oceanic and Atmospheric Administration |
| S      | Space Force                                     |
| X      | Not applicable                                  |
| Z      | Unknown                                         |

## Kicker Rate Code

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 46: kickerRateCode

| Code   | Value                                                                                                        |
|--------|--------------------------------------------------------------------------------------------------------------|
| B1     | $28,500 Active Duty Kicker 20021001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). (OBSOLETE as of 20041001)  |
| B2     | $35,000 Active Duty Kicker 20021001, TOE 36 months. (OBSOLETE as of 20041001)                                |
| B3     | $30,000 Active Duty Kicker 20031001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). (OBSOLETE as of 20041001)  |
| B4     | $37,000 Active Duty Kicker 20031001, TOE 36 months. (OBSOLETE as of 20041001)                                |
| B5     | $42,000 Active Duty Kicker 20031001, TOE 48 months (OBSOLETE as of 20041001)                                 |
| B6     | $47,000 Active Duty Kicker 20031001, TOE 60 months. (OBSOLETE as of 20041001)                                |
| B7     | $50,000 Active Duty Kicker 20031001, TOE 72 months. (OBSOLETE as of 20041001)                                |
| B8     | $28,500 Active Duty Kicker 20021001, TOE 24 months. (OBSOLETE as of 20041001)                                |
| B9     | $30,000 Active Duty Kicker 20031001, TOE 24 months. (OBSOLETE as of 20041001)                                |
| BA     | $8,000 Active Duty Kicker (Navy) before 881001, TOE 24 Months (MGIB 2X4) (OBSOLETE as of 20041001)           |
| BC     | $26,500 Active Duty Kicker as of 970307, TOE 48 months (2yrs AD plus 2yrs Sel Res) (OBSOLETE as of 20041001) |
| BD     | $26,500 Active Duty Kicker as of 970307, TOE 24 months (OBSOLETE as of 20041001)                             |
| BE     | $33,000 Active Duty Kicker as of 970307, TOE 36 months (OBSOLETE as of 20041001)                             |
| BF     | $40,000 Active Duty Kicker as of 970307, TOE 48 months (OBSOLETE as of 20041001)                             |
| BG     | $50,000 Active Duty Kicker as of 981112, TOE 48 months (OBSOLETE as of 20041001)                             |
| BL     | $8,000 Active Duty Kicker 850701-930331, TOE 24 months (OBSOLETE as of 20041001)                             |
| BM     | $12,000. Active Duty Kicker 850701-930331, TOE 24 months (OBSOLETE as of 20041001)                           |
| BN     | $12,000 Active Duty Kicker 850701-930331, TOE 36 months (OBSOLETE as of 20041001)                            |
| BP     | $14,400 Active Duty Kicker 850701-930331, TOE 48 months (OBSOLETE as of 20041001)                            |
| BQ     | No Kicker - Active Duty Kicker as of 850701 (OBSOLETE as of 20041001)                                        |
| BR     | $8,000 Active Duty Kicker 850701-930401, TOE 24 months (MGIB 2x2x4) (OBSOLETE as of 20041001)                |
| BS     | $20,000 Active Duty Kicker 930401-970307, TOE 24 months (MGIB2x2x4) (OBSOLETE as of 20041001)                |
| BT     | $20,000 Active Duty Kicker 930401, TOE 24 months. (OBSOLETE as of 20041001)                                  |
| BV     | $25,000 Active Duty Kicker 930401, TOE 36 months. (OBSOLETE as of 20041001)                                  |
| BW     | $30,000 Active Duty Kicker 930401, TOE 48 months. (OBSOLETE as of 20041001)                                  |
| BX     | $30,000 Active Duty Kicker 991201, TOE 60 months. (OBSOLETE as of 20041001)                                  |
| BY     | $50,000 Active Duty Kicker 991201, TOE 60 months. (OBSOLETE as of 20041001)                                  |
| D2     | $150 Active Duty Kicker 20041001, TOE 24 months.                                                             |
| D3     | $150 Active Duty Kicker 20041001, TOE 36 months.                                                             |
| D4     | $150 Active Duty Kicker 20041001, TOE 48 months.                                                             |
| D5     | $150 Active Duty Kicker 20041001, TOE 60 months.                                                             |

| Code   | Value                                                                          |
|--------|--------------------------------------------------------------------------------|
| D6     | $150 Active Duty Kicker 20041001, TOE 72 months.                               |
| D9     | $150 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| E2     | $250 Active Duty Kicker 20041001, TOE 24 months.                               |
| E3     | $250 Active Duty Kicker 20041001, TOE 36 months.                               |
| E4     | $250 Active Duty Kicker 20041001, TOE 48 months.                               |
| E5     | $250 Active Duty Kicker 20041001, TOE 60 months.                               |
| E6     | $250 Active Duty Kicker 20041001, TOE 72 months.                               |
| E9     | $250 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| F2     | $350 Active Duty Kicker 20041001, TOE 24 months.                               |
| F3     | $350 Active Duty Kicker 20041001, TOE 36 months.                               |
| F4     | $350 Active Duty Kicker 20041001, TOE 48 months.                               |
| F5     | $350 Active Duty Kicker 20041001, TOE 60 months.                               |
| F6     | $350 Active Duty Kicker 20041001, TOE 72 months.                               |
| F9     | $350 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| G2     | $450 Active Duty Kicker 20041001, TOE 24 months.                               |
| G3     | $450 Active Duty Kicker 20041001, TOE 36 months.                               |
| G4     | $450 Active Duty Kicker 20041001, TOE 48 months.                               |
| G5     | $450 Active Duty Kicker 20041001, TOE 60 months.                               |
| G6     | $450 Active Duty Kicker 20041001, TOE 72 months.                               |
| G9     | $450 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| H2     | $550 Active Duty Kicker 20041001, TOE 24 months.                               |
| H3     | $550 Active Duty Kicker 20041001, TOE 36 months.                               |
| H4     | $550 Active Duty Kicker 20041001, TOE 48 months.                               |
| H5     | $550 Active Duty Kicker 20041001, TOE 60 months.                               |
| H6     | $550 Active Duty Kicker 20041001, TOE 72 months.                               |
| H9     | $550 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| J3     | $650 Active Duty Kicker 20041001, TOE 36 months.                               |
| J4     | Active Duty Kicker 20041001, TOE 48                                            |
|        | $650 months.                                                                   |
| J5     | $650 Active Duty Kicker 20041001, TOE 60 months.                               |
| J6     | $650 Active Duty Kicker 20041001, TOE 72 months.                               |
| J9     | $650 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| K2     | $750 Active Duty Kicker 20041001, TOE 24 months.                               |
| K3     | $750 Active Duty Kicker 20041001, TOE 36 months.                               |
| K4     | $750 Active Duty Kicker 20041001, TOE 48 months.                               |
| K5     | $750 Active Duty Kicker 20041001, TOE 60 months.                               |
| K6     | $750 Active Duty Kicker 20041001, TOE 72 months.                               |

| Code   | Value                                                                          |
|--------|--------------------------------------------------------------------------------|
| K9     | $750 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| L2     | $850 Active Duty Kicker 20041001, TOE 24 months.                               |
| L3     | $850 Active Duty Kicker 20041001, TOE 36 months.                               |
| L4     | $850 Active Duty Kicker 20041001, TOE 48 months.                               |
| L5     | $850 Active Duty Kicker 20041001, TOE 60 months.                               |
| L6     | $850 Active Duty Kicker 20041001, TOE 72 months.                               |
| L9     | $850 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| M2     | $950 Active Duty Kicker 20041001, TOE 24 months.                               |
| M3     | $950 Active Duty Kicker 20041001, TOE 36 months.                               |
| M4     | $950 Active Duty Kicker 20041001, TOE 48 months.                               |
| M5     | $950 Active Duty Kicker 20041001, TOE 60 months.                               |
| M6     | $950 Active Duty Kicker 20041001, TOE 72 months.                               |
| M9     | $950 Active Duty Kicker 20041001, TOE 48 months (2 yrs AD plus 2 yrs Sel Res). |
| RA     | $100 Selected Reserve Kicker                                                   |
| RB     | $200 Selected Reserve Kicker                                                   |
| RC     | $350 Selected Reserve Kicker                                                   |
| ZZ     | Unknown or not applicable                                                      |

## Component Codes and Names/Descriptions

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

## Table 47: pnlCatCd Codes

The below table shows the comprehensive list of all the PNL CAT Codes. The codes in Red are for information only and not available in VADIR DB as they are not relevant to the VA Benefits.

| Code   | Value                                                                                                      |
|--------|------------------------------------------------------------------------------------------------------------|
| A      | Active duty member                                                                                         |
| D      | Disabled American veteran                                                                                  |
| E      | DoD and Uniformed Service contract employee                                                                |
| F      | Former member (Reserve service, discharged from RR or SR following notification of retirement eligibility) |
| H      | Medal of Honor recipient                                                                                   |
| I      | Non-DoD civil service employee, except Presidential appointee                                              |
| J      | Academy student                                                                                            |
| K      | Non-appropriated fund DoD and Uniformed Service employee (NAF)                                             |
| L      | Lighthouse service                                                                                         |
| M      | Non-federal Agency civilian associates                                                                     |
| N      | National Guard member                                                                                      |

| Code   | Value                                                                                                                                              |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| O      | Non-DoD contract employee                                                                                                                          |
| Q      | Reserve retiree not yet eligible for retired pay ('Gray Area Retiree')                                                                             |
| R      | Retired military member eligible for retired pay                                                                                                   |
| T      | Foreign military member                                                                                                                            |
| U      | DoD OCONUS Hires                                                                                                                                   |
| V      | Reserve member                                                                                                                                     |
| W      | DoD Beneficiary, a person who receives benefits from the DoD based on prior association, condition or authorization, an example is a former spouse |
| Y      | Service affiliates                                                                                                                                 |

## MGIB Status Codes and Descriptions

Note: These codes come from the mgad\_loss\_cat\_codes table. The naming switch is confusing and is handled in the DB code for Ch33.  It is noted explicitly here for clarity that these are the values for the mgad\_los\_cat\_codes table in the VADIR DB used to represent MGIB Status.

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 48: mgad\_loss\_cat\_codes

|   Code | Value                                                             |
|--------|-------------------------------------------------------------------|
|     00 | Invalid, record correction, change of status                      |
|     01 | Service connected disability                                      |
|     02 | Disability existed prior to Military Service                      |
|     03 | Physical or mental condition interfering with performance of duty |
|     04 | Hardship                                                          |
|     05 | Reduction in force for the convenience of the Government          |
|     06 | Convenience of government, Other                                  |
|     07 | Expiration of term of service                                     |
|     08 | Other separation to civil life                                    |
|     09 | Death                                                             |
|     10 | Dropped from strength                                             |
|     11 | Immediate reenlistment                                            |

## Education Level Codes and Descriptions

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 49: eduLvl

|   Code | Value                                                     |
|--------|-----------------------------------------------------------|
|     11 | Less than high school diploma                             |
|     12 | Attending high school, junior or less                     |
|     13 | Attending high school, senior                             |
|     14 | Secondary school credential near completion               |
|     21 | Test-based equivalency diploma                            |
|     22 | Occupational program certificate                          |
|     23 | Correspondence school diploma                             |
|     24 | High school certificate of attendance                     |
|     25 | Home study diploma                                        |
|     26 | Adult education diploma                                   |
|     31 | High school diploma                                       |
|     41 | Completed one semester of college, no high school diploma |
|     42 | One year of college certificate of equivalency            |
|     43 | 1-2 years college, no degree                              |

|   Code | Value                                         |
|--------|-----------------------------------------------|
|     44 | Associate degree                              |
|     45 | Professional nursing diploma                  |
|     46 | 3-4 year college, no degree                   |
|     51 | Baccalaureate                                 |
|     52 | 1 or more years of graduate school, no degree |
|     61 | Master's Degree                               |
|     62 | Post Masters Degree                           |
|     63 | First professional degree                     |
|     64 | Doctorate Degree                              |
|     65 | Post doctorate degree                         |
|     99 | Unknown                                       |

## Chapter 30 Enroll Status Code and Description

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 50: ch30EnrlStat

|   Code | Value               |
|--------|---------------------|
|     00 | Unknown             |
|     01 | Ineligible          |
|     02 | Ineligible          |
|     03 | Participant         |
|     04 | Ineligible          |
|     05 | Participant         |
|     06 | Participant         |
|     09 | Participant         |
|     10 | Chapter 32 Transfer |
|     11 | Dual Eligibility    |
|     20 | Ineligible          |
|     21 | Participant         |
|     22 | Participant         |
|     23 | Participant         |
|     25 | Participant         |
|     26 | Participant         |
|     27 | Open Window         |
|     28 | Open Window         |
|     30 | Undetermined        |
|     32 | Ineligible          |
|     33 | Ineligible          |
|     34 | Ineligible          |
|     35 | Ineligible          |

|   Code | Value       |
|--------|-------------|
|     45 | Participant |

## MGSR Status Code, Description and Reason

Note:  New codes provided to VADIR won't display the description until the lookup table is updated with the new description value.

Table 51: Project Codes

| Code   | Description    | Reason                                                       |
|--------|----------------|--------------------------------------------------------------|
| AA     | No entitlement | Has not executed SR contract/service obligation              |
| AB     | No entitlement | Has not completed IADT                                       |
| AC     | No entitlement | Did not complete secondary school diploma or equivalent      |
| AD     | No entitlement | Erroneously reported as eligible                             |
| BA     | Eligible       | Serving in an initial period of eligibility                  |
| BB     | Eligible       | Serving in a subsequent period of eligibility                |
| BC     | Eligible       | Involuntarily transferred to non-qualifying position or unit |
| BD     | Eligible       | Completed service obligation                                 |
| BE     | Eligible       | Separated because of disability                              |
| BF     | Eligible       | Separated for unit inactivation or RIF                       |
| BG     | Eligible       | Separated for unit inactivation or RIF                       |
| CA     | Suspended      | Completed requirements of baccalaureate or equivalent degree |
| CB     | Suspended      | In period of non-availability, not for missionary obligation |
| CC     | Suspended      | In period of non-availability for missionary obligation      |
| CD     | Suspended      | Awaiting determination of unsatisfactory participation       |
| CE     | Suspended      | Voluntarily transferred to non-qualifying position or unit   |
| CF     | Suspended      | Began AGR Status                                             |
| CG     | Suspended      | In receipt of ROTC scholarship                               |
| DA     | Terminated     | Failed to reaffiliate within time limit                      |
| DB     | Terminated     | Discharged without grant of authorized non-availability      |
| DC     | Terminated     | Deceased                                                     |
| DD     | Terminated     | Unsatisfactory participation                                 |
| DE     | Terminated     | Failed to participate satisfactorily                         |
| WW     | Not Applicable | Not Applicable                                               |
| ZZ     | Unknown        | Unknown                                                      |

## PGIB Loss Code and Description

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 52: pgib Codes

|   Code | Value                                                                                                                |
|--------|----------------------------------------------------------------------------------------------------------------------|
|     00 | Invalid, record correction, change of status                                                                         |
|     01 | Service connected disability                                                                                         |
|     02 | Disability existed prior to Military Service                                                                         |
|     03 | Physical or mental condition interfering with performance of duty                                                    |
|     04 | Hardship                                                                                                             |
|     05 | Reduction in force for the convenience of the Government                                                             |
|     06 | Qualifying active duty period                                                                                        |
|     07 | Disqualifying active duty period                                                                                     |
|     08 | Non qualifying Active Duty Period                                                                                    |
|     09 | Qualifying Active Duty Period when all Active Duty exceeds 2 years. Note: MCReserve requires additional calculation. |
|     10 | Partially Qualifying Active Duty Period: Qualifying service based on event Start and Stop Dates.                     |
|     16 | Qualifying Open Active Duty Period: If period concludes honorably then will qualify                                  |
|     18 | Non Qualifying Open Active Duty Period                                                                               |
|     19 | Qualifying Open Active Duty Period when all Active Duty exceeds 2 years. Note: MCReserve requires additional calc.   |
|     97 | Non Qualifying Period due to erroneous report from the Service.                                                      |
|     98 | Cannot determine qualifying period. Data quality issue in transaction.                                               |
|     99 | Unknown/Not Applicable                                                                                               |

## Narrative Reason for Separation Code and Description

Note: Where Codes in a lookup table are not present, the value or description field for that code will be blank while the code value will be returned as is.

Table 53: narrativeReasonForSeparation Codes

|   Code | Value                                                  |
|--------|--------------------------------------------------------|
|    001 | WEIGHT CONTROL FAILURE                                 |
|    002 | FRAUDULENT ENTRY INTO MILITARY SERVICE                 |
|    003 | PARENTHOOD OR CUSTODY OF MINOR CHILDREN                |
|    004 | MILITARY PERSONNEL SECURITY PROGRAM                    |
|    005 | FRAUDULENT ENTRY INTO MILITARY SERVICE (DRUG ABUSE)    |
|    006 | FRAUDULENT ENTRY INTO MILITARY SERVICE (ALCOHOL ABUSE) |
|    007 | DISRUPTIVE BEHAVIOR DISORDER                           |
|    008 | MENTAL DISORDER (OTHER)                                |
|    009 | PHYSICAL STANDARDS                                     |
|    010 | CONDITION, NOT A DISABILITY                            |
|    011 | PERSONALITY DISORDER                                   |

|   Code | Value                                                      |
|--------|------------------------------------------------------------|
|    012 | ADJUSTMENT DISORDER                                        |
|    013 | IMPULSE CONTROL DISORDER                                   |
|    014 | FAILURE TO COMPLETE ACOURSE OF INSTRUCTION                 |
|    015 | UNSATISFACTORY PERFORMANCE                                 |
|    016 | SUBSTANDARD PERFORMANCE                                    |
|    017 | PATTERN OF MISCONDUCT                                      |
|    018 | MISCONDUCT (CIVIL CONVICTION)                              |
|    019 | MISCONDUCT (DRUG ABUSE)                                    |
|    020 | MISCONDUCT (SEXUAL PERVERSION)                             |
|    021 | MISCONDUCT (OTHER)                                         |
|    022 | MISCONDUCT (MINOR INFRACTIONS)                             |
|    023 | MISCONDUCT (SERIOUS OFFENSE)                               |
|    024 | MISCONDUCT (ANTHRAX REFUSAL)                               |
|    025 | UNACCEPTABLE CONDUCT (ANTHRAX REFUSAL)                     |
|    026 | UNACCEPTABLE CONDUCT                                       |
|    027 | DRUG REHABILITATION FAILURE                                |
|    028 | ALCOHOL REHABILITATION FAILURE                             |
|    029 | HOMOSEXUAL CONDUCT (ACTS)                                  |
|    030 | HOMOSEXUAL CONDUCT (STATEMENT)                             |
|    031 | HOMOSEXUAL CONDUCT (MARRIAGE OR ATTEMPTED MARRIAGE)        |
|    032 | IN LIEU OF TRIAL BY COURT MARTIAL                          |
|    033 | SUFFICIENT SERVICE FOR RETIREMENT                          |
|    034 | MEDAL OF HONOR RECIPIENT                                   |
|    035 | COMPLETION OF REQUIRED ACTIVE SERVICE                      |
|    036 | EARLY RELEASE PROGRAM-VOLUNTARY SEPARATION INCENTIVE (VSI) |
|    037 | EARLY RELEASE PROGRAM-SPECIAL SEPARATION BENEFIT (SSB)     |
|    038 | REDUCTION IN FORCE                                         |
|    039 | ATTEND CIVILIAN SCHOOL                                     |
|    040 | CIVIL OFFICE                                               |
|    041 | CONSCIENTIOUS OBJECTOR                                     |
|    042 | FORCE SHAPING (VSP)                                        |
|    043 | ALIEN                                                      |
|    044 | SURVIVING FAMILY MEMBER - SOLE SURVIVORSHIP                |
|    045 | HARDSHIP                                                   |
|    046 | PREGNANCY OR CHILDBIRTH                                    |
|    047 | ECCLESIASTICAL ENDORSEMENT                                 |
|    048 | HOLIDAY EARLY RELEASE PROGRAM                              |
|    049 | SECRETARIAL AUTHORITY                                      |
|    050 | FAILED MEDICAL/PHYSICAL PROCUREMENT STANDARDS              |
|    051 | INTERDEPARTMENTAL TRANSFER                                 |

|   Code | Value                                                      |
|--------|------------------------------------------------------------|
|    052 | INTRADEPARTMENTAL TRANSFER                                 |
|    053 | IMMEDIATE ENLISTMENT OR REENLISTMENT                       |
|    054 | DISMISSAL - NO REVIEW                                      |
|    055 | MISCELLANEOUS/ GENERAL REASONS                             |
|    056 | FORCE SHAPING (BOARD SELECTED)                             |
|    057 | ERRONEOUS ENTRY (OTHER)                                    |
|    058 | NON-RETENTION ONACTIVE DUTY                                |
|    059 | MISCONDUCT (AWOL)                                          |
|    060 | MISCONDUCT (DESERTION)                                     |
|    061 | MAXIMUM AGE                                                |
|    062 | MAXIMUM SERVICE OR TIME IN GRADE                           |
|    063 | INSUFFICIENT RETAINABILITY (ECONOMIC REASONS)              |
|    064 | LACK OF JURISDICTION                                       |
|    065 | DISABILITY, SEVERANCE PAY, COMBAT RELATED (ENHANCED)       |
|    066 | DISABILITY, SEVERANCE PAY, NONCOMBAT (ENHANCED)            |
|    067 | DISABILITY, EXISTED PRIOR TO SERVICE, PEB (ENHANCED)       |
|    068 | DISABILITY, SEVERANCE PAY (ENHANCED)                       |
|    069 | DISABILITY, EXISTED PRIOR TO SERVICE, MED BOARD (ENHANCED) |
|    070 | DISABILITY, NOT IN LINE OF DUTY (ENHANCED)                 |
|    071 | DISABILITY, AGGRAVATION (ENHANCED)                         |
|    072 | DISABILITY, OTHER (ENHANCED)                               |
|    073 | ERRONEOUS ENTRY (ALCOHOL ABUSE)                            |
|    074 | UNDER AGE                                                  |
|    075 | COMPETENT AUTHORITY, WITHOUT BOARD ACTION                  |
|    076 | DISABILITY, SEVERANCE PAY, COMBAT RELATED                  |
|    077 | DISABILITY, SEVERANCE PAY                                  |
|    078 | DISABILITY, EXISTED PRIOR TO SERVICE, PEB                  |
|    079 | DISABILITY, EXISTED PRIOR TO SERVICE, MED BOARD            |
|    080 | DISABILITY, SEVERANCE PAY, NONCOMBAT                       |
|    081 | DISABILITY, NOT IN LINE OF DUTY                            |
|    082 | DISABILITY, AGGRAVATION                                    |
|    083 | DISABILITY, OTHER                                          |
|    084 | ERRONEOUS ENTRY (DRUG ABUSE)                               |
|    085 | ENTRY LEVEL PERFORMANCE ANDCONDUCT                         |
|    086 | NON-SELECTION, PERMANENT PROMOTION                         |
|    087 | NON-SELECTION, TEMPORARY PROMOTION                         |
|    088 | FAILURE TO COMPLETE COMMISSIONING OR WARRANT PROGRAM       |
|    089 | COURT MARTIAL (ALCOHOL)                                    |
|    090 | COURT MARTIAL (HOMOSEXUAL CONDUCT)                         |
|    091 | COURT MARTIAL (DESERTION)                                  |

|   Code | Value                                                     |
|--------|-----------------------------------------------------------|
|    092 | COURT MARTIAL (OTHER)                                     |
|    093 | COURT MARTIAL (DRUG ABUSE)                                |
|    094 | COURT MARTIAL (ANTHRAX REFUSAL)                           |
|    095 | SURVIVING FAMILY MEMBER                                   |
|    096 | DEFECTIVE ENLISTMENT AGREEMENT                            |
|    097 | FAILURE TO ACCEPT REGULAR APPOINTMENT                     |
|    098 | ACCEPT COMMISSION OR WARRANT IN SAME BRANCH OF SERVICE    |
|    099 | ACCEPT COMMISSION OR WARRANT IN ANOTHER BRANCH OF SERVICE |
|    100 | ENTER OFFICER TRAINING PROGRAM                            |
|    101 | REQUEST FOR EXTENSION OF SERVICE DENIED                   |
|    102 | DISMISSAL - AWAITING APPELLATE REVIEW                     |
|    103 | ENROLLMENT IN SERVICE ACADEMY                             |
|    104 | EARLY RETIREMENT                                          |
|    105 | DISABILITY, PERMANENT (ENHANCED)                          |
|    106 | DISABILITY, TEMPORARY (ENHANCED)                          |
|    107 | DISABILITY, PERMANENT                                     |
|    108 | DISABILITY, TEMPORARY                                     |
|    109 | PERSONAL ALCOHOL ABUSE                                    |
|    110 | PERSONAL DRUG ABUSE                                       |
|    111 | EARLY SEPARATION                                          |
|    112 | VOLUNTARY RETIREMENT                                      |
|    113 | EARLY RETIREMENT FROM SERVICE                             |
|    114 | CAREER INTERMISSION PROGRAM                               |
|    115 | DISABILITY, COMBAT RELATED, IDES                          |
|    900 | NOT APPLICABLE                                            |
|    999 | UNKNOWN                                                   |

## 7. Summary of Technical Changes for version 2.x

The changes from previous versions of the VADIR Chapter 33 LTS web service are a direct result of security mandates, or due to address operational concerns made evident over time. Many of these are invisible in the interface.

The below summary describes the changes addressed that may be visible to end users. The changes here do not reflect data changes, specifically the changes between v2.0.x and v2.1.x

## 7.1. Date and Number Data Elements changed to Strings

Date and number elements now show in the .xsd as type string.  This completed a previous interface revision that changed some types to string.  The format of the dates is the same and while this changes the .xsd, the output remains the same.

## 7.2. Procedural .wsdl and .xsd

The exposed and functional .wsdl and .xsd files are now generated by the system and must be reached by the ?WSDL and ?XSD signifiers in the URL. This is part of the above-mentioned rewrite and simplification. As a part of this, the hard control over the XML Namespaces from the previous version has been replaced by auto assigned names.  If the name of the namespaces for the datatypes is a part of the client app, accommodations need to be made.

## 7.3. Type Suffix in type definitions

Again, in the ?WSDL and ?XSD, the addition of the suffix 'type' to many type definitions was necessary to avoid name collisions that were not accommodated in the more simplified underlying architecture's libraries. This change does affect the tags that show up in the output and will require accommodation by the consuming system.

## 7.4. Changes to The Production URL to Accommodate Disaster Recovery

We introduced a Global Traffic Manager (GTM) entry to the address routing for services, starting with v2.  The new top level name is https://vavdrappprd.va.gov , which is a change from the previous https://vavdrappprd.aac.va.gov . While the old URL address works, the new address allows administrators to repoint to VADIR's Disaster Recovery site in Philadelphia without having client applications alter their configuration. Please note the change.

## 8. ICD Review and Concurrence

The parties below have reviewed the Chapter 33 Long Term Solution (LTS) Web Service (WS) Interface Control Document and concur.

.

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Alex Torres, VADIR System Owner

Date

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Riley Ross, Chapter 33 IT Project Manager

Date