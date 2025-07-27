# Consent Governance Rules and Implementation Framework

## 1. Data Classification and Consent Provision Rules

### 1.1 Granular Data Classification Matrix

| **Data Category** | **FHIR Resource Type** | **Consent.provision.class** | **Sensitivity Level** | **Default Expiry** | **Special Requirements** |
|-------------------|------------------------|----------------------------|----------------------|-------------------|------------------------|
| **Patient Demographics** | Patient | `http://hl7.org/fhir/resource-types#Patient` | Low | 1 year | Identity verification required |
| **Vital Signs** | Observation (vital-signs) | `http://loinc.org/vs/LL715-4` | Low-Medium | 6 months | Real-time monitoring context |
| **Clinical History** | Condition, AllergyIntolerance | `http://hl7.org/fhir/resource-types#Condition` | Medium | 6 months | Chronic vs acute differentiation |
| **Laboratory Results** | Observation (laboratory) | `http://loinc.org/vs/LL1001-8` | Medium | 3 months | Test-specific granularity |
| **Imaging Results** | DiagnosticReport, ImagingStudy | `http://hl7.org/fhir/resource-types#DiagnosticReport` | Medium-High | 3 months | Modality-specific consent |
| **Diagnosis** | Condition, Encounter | `http://hl7.org/fhir/resource-types#Condition` | High | 3 months | ICD-11 classification |
| **Clinical Conditions** | Condition | `http://snomed.info/sct#404684003` | High | 3 months | Mental health separation |
| **Prescriptions** | MedicationRequest | `http://hl7.org/fhir/resource-types#MedicationRequest` | High | 3 months | Controlled substances flag |
| **Medication Dispensed** | MedicationDispense | `http://hl7.org/fhir/resource-types#MedicationDispense` | Medium-High | 3 months | Pharmacy integration |
| **Drug Allergies** | AllergyIntolerance | `http://hl7.org/fhir/resource-types#AllergyIntolerance` | Critical | 1 year | Emergency access override |

### 1.2 Purpose-Driven Use Case Classification

| **Purpose Code** | **Consent.provision.purpose** | **Description** | **Typical Duration** | **Access Restrictions** |
|------------------|------------------------------|-----------------|-------------------|----------------------|
| **TREAT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#TREAT` | Treatment and care delivery | 30 days | Active care team only |
| **ETREAT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#ETREAT` | Emergency treatment | 24 hours | Emergency department staff |
| **HPAYMT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#HPAYMT` | Healthcare payment processing | 6 months | Billing and insurance |
| **HOPERAT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#HOPERAT` | Healthcare operations | 3 months | Quality and administration |
| **HRESCH** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#HRESCH` | Healthcare research | 5 years | IRB-approved studies |
| **PUBHLTH** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#PUBHLTH` | Public health reporting | 1 year | Health authorities |
| **HMARKT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#HMARKT` | Healthcare marketing | 90 days | Marketing department |
| **HDIRECT** | `http://terminology.hl7.org/CodeSystem/v3-ActReason#HDIRECT` | Healthcare directory | 1 year | Provider networks |

## 2. Detailed Consent Provision Specifications

### 2.1 Patient Demographics Consent Rules

```json
{
  "resourceType": "Consent",
  "provision": {
    "type": "permit",
    "class": [
      {
        "system": "http://hl7.org/fhir/resource-types",
        "code": "Patient",
        "display": "Patient Demographics"
      }
    ],
    "data": [
      {
        "meaning": "related",
        "reference": {
          "reference": "Patient/*"
        }
      }
    ],
    "purpose": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "TREAT"
      }
    ],
    "dataPeriod": {
      "start": "2025-01-01",
      "end": "2026-01-01"
    },
    "provision": [
      {
        "type": "deny",
        "class": [
          {
            "system": "http://hl7.org/fhir/patient-fields",
            "code": "Patient.photo",
            "display": "Patient Photo"
          }
        ]
      }
    ]
  }
}
```

**Specific Fields Captured:**
- Name (with pseudonymization options)
- Date of birth (with age-only options)
- Gender
- Contact information (with emergency-only options)
- Address (with region-only options)
- Identifiers (with masking options)

### 2.2 Laboratory Results Consent Rules

```json
{
  "resourceType": "Consent",
  "provision": {
    "type": "permit",
    "class": [
      {
        "system": "http://loinc.org",
        "code": "11502-2",
        "display": "Laboratory report"
      }
    ],
    "code": [
      {
        "coding": [
          {
            "system": "http://loinc.org/granularity",
            "code": "CBC",
            "display": "Complete Blood Count"
          }
        ]
      }
    ],
    "purpose": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "TREAT"
      }
    ],
    "dataPeriod": {
      "start": "2025-01-01",
      "end": "2025-04-01"
    },
    "provision": [
      {
        "type": "deny",
        "code": [
          {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "33747-0",
                "display": "Genetic analysis"
              }
            ]
          }
        ]
      },
      {
        "type": "deny",
        "code": [
          {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "Drug-screen",
                "display": "Drug screening tests"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 2.3 Mental Health Clinical Conditions (Special Handling)

```json
{
  "resourceType": "Consent",
  "provision": {
    "type": "permit",
    "class": [
      {
        "system": "http://snomed.info/sct",
        "code": "74732009",
        "display": "Mental disorder"
      }
    ],
    "purpose": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "TREAT"
      }
    ],
    "actor": [
      {
        "role": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
              "code": "CST",
              "display": "Custodian"
            }
          ]
        },
        "reference": {
          "reference": "Organization/mental-health-certified"
        }
      }
    ],
    "securityLabel": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
        "code": "R",
        "display": "Restricted"
      }
    ],
    "dataPeriod": {
      "start": "2025-01-01",
      "end": "2025-04-01"
    }
  }
}
```

### 2.4 Emergency Access Override Rules

```json
{
  "resourceType": "Consent",
  "provision": {
    "type": "permit",
    "class": [
      {
        "system": "http://hl7.org/fhir/resource-types",
        "code": "AllergyIntolerance",
        "display": "Drug Allergies - Emergency Access"
      }
    ],
    "purpose": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "ETREAT"
      }
    ],
    "actor": [
      {
        "role": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
              "code": "ER",
              "display": "Emergency Room"
            }
          ]
        }
      }
    ],
    "securityLabel": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "EMRGONLY",
        "display": "Emergency Only"
      }
    ]
  }
}
```

## 3. Operating Procedures by Data Type

### 3.1 Patient Demographics Access Procedure

**Consent Validation Steps:**
1. **Identity Verification**: Validate requesting organization against Patient.managingOrganization
2. **Purpose Alignment**: Ensure requested purpose matches organizational role
3. **Field-Level Filtering**: Apply granular field restrictions (e.g., photo exclusion)
4. **Pseudonymization**: Apply data masking based on purpose and requester relationship
5. **Audit Logging**: Record demographics access with specific fields accessed

**Specific Rules:**
- **Treatment Purpose**: Full demographics except sensitive identifiers
- **Payment Purpose**: Financial and insurance-related fields only
- **Research Purpose**: De-identified demographics with IRB approval verification
- **Marketing Purpose**: Opt-in required, contact preferences respected

### 3.2 Laboratory Results Access Procedure

**Consent Validation Steps:**
1. **Test Category Validation**: Match requested lab categories against consented classes
2. **Temporal Scope Check**: Validate request date range against consent period
3. **Exclusion Processing**: Apply specific test exclusions (genetic, drug screening)
4. **Clinical Context**: Verify requesting provider's clinical relationship
5. **Result Sensitivity**: Apply additional restrictions for abnormal/critical values

**Granular Lab Categories:**
```
- Basic Metabolic Panel (BMP): Low sensitivity, 6-month consent
- Complete Blood Count (CBC): Low sensitivity, 6-month consent  
- Lipid Panel: Medium sensitivity, 3-month consent
- Liver Function Tests: Medium sensitivity, 3-month consent
- Genetic Testing: High sensitivity, explicit consent required
- Drug Screening: High sensitivity, explicit consent + legal review
- Infectious Disease Testing: High sensitivity, purpose-specific consent
```

### 3.3 Imaging Results Access Procedure

**Consent Validation Steps:**
1. **Modality-Specific Consent**: Validate against specific imaging types
2. **Anatomical Region Check**: Ensure consented body regions match request
3. **Clinical Indication**: Verify imaging purpose aligns with consent purpose
4. **Report vs Images**: Differentiate consent for reports vs actual imaging data
5. **Retention Policy**: Apply modality-specific retention and access rules

**Imaging Modality Rules:**
```
- X-Ray: Standard consent, 6-month validity
- CT Scan: Enhanced consent, 3-month validity
- MRI: Enhanced consent, 3-month validity
- Ultrasound: Standard consent, special rules for reproductive health
- Nuclear Medicine: High-sensitivity consent, radiation exposure disclosure
- Mammography: Gender-specific consent, privacy-enhanced handling
```

### 3.4 Prescription and Medication Access Procedure

**Consent Validation Steps:**
1. **Controlled Substance Check**: Enhanced validation for scheduled medications
2. **Prescriber Verification**: Validate requesting provider's prescribing authority
3. **Pharmacy Integration**: Cross-check with medication dispensing records
4. **Drug Interaction Context**: Ensure access supports clinical decision-making
5. **Abuse Prevention**: Apply additional checks for high-risk medications

**Medication Categories:**
```
- Over-the-Counter: Basic consent, extended validity
- Prescription (Non-controlled): Standard consent, 3-month validity
- Controlled Substances (Schedule III-V): Enhanced consent, 1-month validity
- Controlled Substances (Schedule I-II): Explicit consent, 2-week validity
- Mental Health Medications: Specialized consent, mental health provider only
- Reproductive Health: Gender-specific consent, enhanced privacy
```

## 4. Consent Matching and Reusability Algorithm

### 4.1 Intelligent Consent Matching Pseudocode

```pseudocode
ALGORITHM: IntelligentConsentMatching
INPUT: ConsentRequest (requester, patient, dataTypes, purpose, timeRange)
OUTPUT: ConsentDecision (approved/denied, restrictions, expiryTime)

FUNCTION validateConsentRequest(request):
    // Step 1: Patient Identity Validation
    patient = validatePatientIdentity(request.patientId)
    IF patient == NULL:
        RETURN DENIED("Invalid patient identifier")
    
    // Step 2: Retrieve Active Consents
    activeConsents = getActiveConsents(patient.id, currentTimestamp)
    
    // Step 3: Requester Validation
    requester = validateRequesterCredentials(request.requester)
    IF requester == NULL:
        RETURN DENIED("Invalid requester credentials")
    
    // Step 4: Organizational Relationship Check
    relationshipScore = calculateOrganizationalRelationship(
        patient.managingOrganization, 
        requester.organization
    )
    
    // Step 5: Data Type and Purpose Matching
    FOR each dataType IN request.dataTypes:
        matchingConsent = findBestConsentMatch(
            activeConsents, 
            dataType, 
            request.purpose,
            requester
        )
        
        IF matchingConsent == NULL:
            RETURN DENIED("No valid consent for " + dataType)
        
        // Step 6: Granular Permission Check
        permissions = evaluateGranularPermissions(
            matchingConsent,
            dataType,
            request.purpose,
            requester.role
        )
        
        IF permissions.denied:
            RETURN DENIED("Granular permissions deny access")
    
    // Step 7: Temporal Validation
    temporalValid = validateTemporalScope(
        matchingConsent.dataPeriod,
        request.timeRange
    )
    
    IF NOT temporalValid:
        RETURN DENIED("Temporal scope violation")
    
    // Step 8: Emergency Override Check
    IF request.purpose == "ETREAT":
        emergencyOverride = evaluateEmergencyOverride(
            request,
            patient.allergies,
            patient.criticalConditions
        )
        IF emergencyOverride.granted:
            RETURN APPROVED(emergencyOverride.permissions, "24H")
    
    // Step 9: Consent Reusability Assessment
    reuseScore = calculateConsentReuseScore(
        matchingConsent,
        request,
        relationshipScore
    )
    
    IF reuseScore >= REUSE_THRESHOLD:
        // Step 10: Apply Data Filtering and Masking
        filteredPermissions = applyDataFiltering(
            permissions,
            requester.role,
            request.purpose,
            patient.preferences
        )
        
        // Step 11: Generate Access Token
        accessToken = generateAccessToken(
            filteredPermissions,
            matchingConsent.dataPeriod.end,
            requester
        )
        
        // Step 12: Log Consent Usage
        logConsentUsage(
            matchingConsent.id,
            request,
            accessToken.id,
            "REUSED"
        )
        
        RETURN APPROVED(filteredPermissions, accessToken)
    ELSE:
        // Require explicit consent
        RETURN PENDING("Explicit consent required")

FUNCTION findBestConsentMatch(consents, dataType, purpose, requester):
    bestMatch = NULL
    highestScore = 0
    
    FOR each consent IN consents:
        score = calculateConsentMatchScore(consent, dataType, purpose, requester)
        IF score > highestScore AND score >= MINIMUM_MATCH_THRESHOLD:
            highestScore = score
            bestMatch = consent
    
    RETURN bestMatch

FUNCTION calculateConsentMatchScore(consent, dataType, purpose, requester):
    score = 0
    
    // Data type matching (40% of score)
    dataTypeScore = calculateDataTypeMatch(consent.provision.class, dataType)
    score += dataTypeScore * 0.4
    
    // Purpose matching (30% of score)
    purposeScore = calculatePurposeMatch(consent.provision.purpose, purpose)
    score += purposeScore * 0.3
    
    // Requester relationship (20% of score)
    requesterScore = calculateRequesterMatch(consent.provision.actor, requester)
    score += requesterScore * 0.2
    
    // Temporal validity (10% of score)
    temporalScore = calculateTemporalMatch(consent.provision.dataPeriod)
    score += temporalScore * 0.1
    
    RETURN score

FUNCTION evaluateGranularPermissions(consent, dataType, purpose, requesterRole):
    permissions = {
        "allowed": [],
        "denied": [],
        "masked": [],
        "pseudonymized": []
    }
    
    // Apply base permissions from consent.provision
    basePermissions = consent.provision.type // permit or deny
    
    // Process nested provisions (exceptions)
    FOR each nestedProvision IN consent.provision.provision:
        IF matchesDataType(nestedProvision.class, dataType):
            IF nestedProvision.type == "deny":
                permissions.denied.add(nestedProvision.class)
            ELSE IF nestedProvision.type == "permit":
                permissions.allowed.add(nestedProvision.class)
    
    // Apply role-based filtering
    roleBasedFilter = getRoleBasedFiltering(requesterRole, dataType)
    permissions.masked.addAll(roleBasedFilter.maskedFields)
    permissions.pseudonymized.addAll(roleBasedFilter.pseudonymizedFields)
    
    // Apply sensitivity-based restrictions
    sensitivityLevel = getDataSensitivityLevel(dataType)
    IF sensitivityLevel >= HIGH_SENSITIVITY:
        permissions.masked.addAll(getHighSensitivityMasking())
    
    RETURN permissions

FUNCTION calculateOrganizationalRelationship(patientOrg, requesterOrg):
    // Direct organizational relationship
    IF patientOrg.id == requesterOrg.id:
        RETURN 1.0 // Same organization
    
    // Care network relationship
    IF isInCareNetwork(patientOrg, requesterOrg):
        RETURN 0.8 // Network partner
    
    // Referral relationship
    IF hasActiveReferral(patientOrg, requesterOrg):
        RETURN 0.6 // Active referral
    
    // No established relationship
    RETURN 0.2 // Unknown organization

FUNCTION validateTemporalScope(consentPeriod, requestTimeRange):
    currentTime = getCurrentTimestamp()
    
    // Check if consent is currently active
    IF currentTime < consentPeriod.start OR currentTime > consentPeriod.end:
        RETURN FALSE
    
    // Check if request time range is within consent period
    IF requestTimeRange.start < consentPeriod.start:
        RETURN FALSE
    
    IF requestTimeRange.end > consentPeriod.end:
        RETURN FALSE
    
    RETURN TRUE

FUNCTION evaluateEmergencyOverride(request, allergies, criticalConditions):
    override = {
        "granted": FALSE,
        "permissions": {},
        "auditRequired": TRUE,
        "notificationRequired": TRUE
    }
    
    // Always grant access to critical safety information
    IF request.dataTypes.contains("AllergyIntolerance"):
        override.granted = TRUE
        override.permissions.add("read:allergies")
    
    IF request.dataTypes.contains("CriticalConditions"):
        override.granted = TRUE
        override.permissions.add("read:critical-conditions")
    
    // Log emergency access for review
    IF override.granted:
        logEmergencyOverride(request, "Emergency access granted")
        schedulePostEmergencyReview(request)
    
    RETURN override

FUNCTION applyDataFiltering(permissions, role, purpose, patientPreferences):
    filteredPermissions = permissions.clone()
    
    // Apply role-based data filtering
    SWITCH role:
        CASE "physician":
            // Full clinical data access
            BREAK
        CASE "nurse":
            // Limited to care-relevant data
            filteredPermissions.denied.add("financial-data")
            BREAK
        CASE "pharmacist":
            // Medication and allergy focus
            filteredPermissions.allowed = filterToMedicationRelevant(permissions.allowed)
            BREAK
        CASE "billing":
            // Financial and administrative data only
            filteredPermissions.allowed = filterToFinancialRelevant(permissions.allowed)
            filteredPermissions.masked.addAll(getAllClinicalData())
            BREAK
    
    // Apply purpose-based filtering
    SWITCH purpose:
        CASE "TREAT":
            // Treatment-relevant data only
            BREAK
        CASE "HPAYMT":
            // Payment-relevant data, mask clinical details
            filteredPermissions.masked.addAll(getDetailedClinicalData())
            BREAK
        CASE "HRESCH":
            // Research data with de-identification
            filteredPermissions.pseudonymized.addAll(getIdentifiableData())
            BREAK
    
    // Apply patient preferences
    FOR each preference IN patientPreferences:
        IF preference.type == "MASK_DEMOGRAPHIC":
            filteredPermissions.masked.add("Patient.name")
            filteredPermissions.masked.add("Patient.address")
        
        IF preference.type == "NO_MARKETING":
            IF purpose == "HMARKT":
                filteredPermissions.denied.addAll(permissions.allowed)
    
    RETURN filteredPermissions

// Constants and Thresholds
MINIMUM_MATCH_THRESHOLD = 0.7
REUSE_THRESHOLD = 0.8
HIGH_SENSITIVITY = 3
```

### 4.2 Data Sensitivity Classification Algorithm

```pseudocode
FUNCTION getDataSensitivityLevel(dataType):
    sensitivityMap = {
        "Patient.demographics": 1,
        "Observation.vital-signs": 1,
        "Observation.laboratory": 2,
        "DiagnosticReport.imaging": 2,
        "Condition.diagnosis": 3,
        "Condition.mental-health": 4,
        "MedicationRequest.controlled": 4,
        "AllergyIntolerance": 4,
        "Observation.genetic": 5
    }
    
    RETURN sensitivityMap.get(dataType, 2) // Default to medium sensitivity

FUNCTION getHighSensitivityMasking():
    RETURN [
        "Patient.identifier.value",
        "Patient.telecom.value",
        "Patient.address.line",
        "Practitioner.identifier.value"
    ]
```

## 5. Implementation Guidelines

### 5.1 FHIR Resource Integration Points

**Core Resources Used:**
- `Consent`: Primary consent management
- `Patient`: Subject of consent decisions  
- `Organization`: Healthcare organizations and requesters
- `Practitioner`: Individual healthcare providers
- `PractitionerRole`: Provider roles and relationships
- `Provenance`: Consent decision audit trail
- `AuditEvent`: Access logging and monitoring

### 5.2 Terminology Service Integration

**Required Code Systems:**
- LOINC: Laboratory and clinical observations
- SNOMED CT: Clinical terminology and conditions
- ICD-11: Diagnosis classification
- HL7 ActReason: Purpose codes
- HL7 RoleCode: Actor role definitions

### 5.3 Performance Optimization

**Caching Strategy:**
- Active consent cache with 5-minute TTL
- Organizational relationship cache with 1-hour TTL
- Terminology mapping cache with 24-hour TTL
- Patient preference cache with immediate invalidation

**Indexing Requirements:**
- Patient ID + Consent Status composite index
- Data Type + Purpose composite index  
- Temporal range index on consent periods
- Requester organization index for quick lookup

This comprehensive framework provides the foundation for implementing sophisticated, FHIR-compliant consent governance that balances patient privacy, clinical needs, and regulatory requirements while maintaining system performance and usability.