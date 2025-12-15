# Afya Yangu - Household & Dependent Management

## Overview

The Household & Dependent Management module enables patients to create household structures, link family members as dependents, and manage these relationships across the Client Registry (CR) and Benefits Management System (BMS).

**Key Principle**: Every person exists as a single Patient resource in CR, and each dependent can only belong to ONE household at any given time.

---

## Household vs Family Concepts

### Household
- A **household** is a group of related individuals managed by a primary member (household head)
- Tracked in **Afya Yangu** and **CR** via RelatedPerson resources
- Used for dependent management and access control
- **Rule**: One dependent can only belong to one household at a time

### Insurance Beneficiaries
- A **beneficiary** is a person covered under an insurance scheme
- Tracked in **BMS** with references to CR Patient IDs
- A person can be a beneficiary in **multiple** insurance schemes simultaneously
- Beneficiaries are selected from the household's dependents

---

## Architecture: CR-BMS-Afya Yangu Integration

```mermaid
graph TB
    subgraph "Afya Yangu Portal"
        UI[Web/Mobile UI]
        HH[Household Service]
        INS[Insurance Service]
    end
    
    subgraph "Client Registry CR"
        CRP[Patient Resources]
        CRR[RelatedPerson Resources]
        CRHH[Household Membership]
    end
    
    subgraph "Benefits Management System BMS"
        BMSS[Scheme Management]
        BMSE[Enrollment Service]
        BMSB[Beneficiary Management]
    end
    
    subgraph "OpenHIE IOL"
        IOL[Interoperability Layer]
        Events[Event Bus]
    end
    
    UI --> HH
    UI --> INS
    
    HH -->|FHIR API| IOL
    INS -->|FHIR API| IOL
    
    IOL --> CRP
    IOL --> CRR
    IOL --> CRHH
    IOL --> BMSS
    IOL --> BMSE
    IOL --> BMSB
    
    BMSB -.->|Reference| CRP
    CRR -.->|Links| CRP
    
    BMSE -->|Events| Events
    Events -->|Subscribe| INS
    
    style CRP fill:#2ecc71,color:#fff
    style BMSS fill:#f39c12,color:#fff
    style HH fill:#3498db,color:#fff
    style IOL fill:#9b59b6,color:#fff
```

---

## Data Model

### Household Structure

```typescript
interface Household {
  primaryMemberId: string;  // CR Patient ID of household head
  householdName?: string;   // Optional: "Juma Family"
  members: HouseholdMember[];
  createdDate: Date;
  lastUpdated: Date;
}

interface HouseholdMember {
  patientId: string;  // Reference to CR Patient ID (unique)
  relationship: RelationshipType;
  isDependent: boolean;
  isPrimaryDependent: boolean;
  addedBy: string;  // PatientId who added this member
  addedDate: Date;
  status: 'ACTIVE' | 'REMOVED';
  previousHousehold?: string;  // Track transfers
}

enum RelationshipType {
  SELF = 'SELF',           // Household head
  SPOUSE = 'SPOUSE',
  CHILD = 'CHILD',
  PARENT = 'PARENT',
  SIBLING = 'SIBLING',
  GUARDIAN = 'GUARDIAN',
  OTHER = 'OTHER'
}
```

### CR-BMS Relationship

```typescript
// CR: Patient (one per person)
interface CRPatient {
  id: string;  // e.g., "patient-123"
  identifier: Identifier[];
  name: HumanName[];
  birthDate: string;
  // ... other demographics
}

// CR: RelatedPerson (household membership)
interface CRRelatedPerson {
  id: string;
  patient: Reference;  // Primary member
  relatedPatient: Reference;  // Dependent
  relationship: CodeableConcept;
  active: boolean;
  period: Period;
}

// BMS: Insurance Enrollment
interface BMSEnrollment {
  enrollmentId: string;
  schemeId: string;
  primaryMemberId: string;  // CR Patient ID
  memberNumber: string;
  beneficiaries: BMSBeneficiary[];
}

// BMS: Beneficiary
interface BMSBeneficiary {
  beneficiaryId: string;
  patientId: string;  // CR Patient ID (reference)
  relationship: RelationshipType;
  memberCardNumber: string;
  status: 'ACTIVE' | 'PENDING' | 'REMOVED';
}
```

---

## Process Flows

### Flow 1: Register New Client to CR

```mermaid
sequenceDiagram
    participant User
    participant AY as Afya Yangu
    participant Reg as Registration Service
    participant NRB as National Registration Bureau
    participant CR
    participant Auth
    
    User->>AY: Access Registration Page
    User->>AY: Enter Personal Details
    
    AY->>Reg: Submit Registration
    Reg->>NRB: Verify National ID
    NRB-->>Reg: ID Valid + Demographics
    
    Reg->>CR: Search for Existing Patient
    CR-->>Reg: Not Found
    
    Reg->>CR: Create Patient (FHIR POST)
    Note over CR: New Patient Resource<br/>patient-123
    CR-->>Reg: Patient ID
    
    Reg->>Auth: Create User Account
    Auth-->>Reg: Credentials Created
    
    Reg->>User: Send Verification Email/SMS
    User->>AY: Verify Email/Phone
    
    AY-->>User: Registration Complete
    Note over User: Can now login to Afya Yangu
```

**FHIR Patient Creation**:
```json
POST https://cr.hie.example.com/fhir/Patient

{
  "resourceType": "Patient",
  "identifier": [{
    "use": "official",
    "system": "http://nationalid.gov.ke",
    "value": "12345678"
  }],
  "active": true,
  "name": [{
    "use": "official",
    "family": "Juma",
    "given": ["John"]
  }],
  "gender": "male",
  "birthDate": "1985-06-15",
  "telecom": [
    {"system": "phone", "value": "+254712345678"},
    {"system": "email", "value": "john.juma@example.com"}
  ]
}
```

---

### Flow 2: Household Head Registers New Dependent

```mermaid
sequenceDiagram
    participant Head as Household Head
    participant AY as Afya Yangu
    participant HH as Household Service
    participant CR
    participant NRB
    
    Head->>AY: Login to Afya Yangu
    Head->>AY: Navigate to "My Household"
    Head->>AY: Click "Add Dependent"
    
    Head->>AY: Enter Dependent Details
    Note over Head,AY: Name, DOB, Gender,<br/>National ID, Relationship
    
    AY->>HH: Submit New Dependent
    
    HH->>NRB: Verify National ID (if provided)
    NRB-->>HH: Verification Result
    
    HH->>CR: Search for Existing Patient
    Note over CR: Search by National ID,<br/>Name + DOB
    
    alt Dependent Already Exists
        CR-->>HH: Found Patient (patient-456)
        
        HH->>CR: Check Existing Household Membership
        Note over CR: Query RelatedPerson<br/>where related-patient=patient-456
        
        alt Already in Another Household
            CR-->>HH: Active Membership Found
            HH-->>AY: Error: Already in another household
            AY-->>Head: Cannot add - already a dependent elsewhere
        else Not in Any Household
            CR-->>HH: No Active Membership
            HH->>CR: Create RelatedPerson
            Note over CR: Links patient-123 (head)<br/>to patient-456 (dependent)
            CR-->>HH: Relationship Created
            HH-->>AY: Dependent Added
        end
        
    else Dependent Does Not Exist
        HH->>CR: Create New Patient
        CR-->>HH: New Patient ID (patient-789)
        
        HH->>CR: Create RelatedPerson
        Note over CR: Links patient-123 (head)<br/>to patient-789 (dependent)
        CR-->>HH: Relationship Created
        HH-->>AY: New Dependent Created & Added
    end
    
    AY-->>Head: Household Updated
```

**FHIR RelatedPerson Creation**:
```json
POST https://cr.hie.example.com/fhir/RelatedPerson

{
  "resourceType": "RelatedPerson",
  "active": true,
  "patient": {
    "reference": "Patient/patient-123",
    "display": "John Juma (Household Head)"
  },
  "relationship": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "CHILD",
      "display": "child"
    }]
  }],
  "period": {
    "start": "2025-11-23"
  },
  "extension": [{
    "url": "http://afya-yangu.hie.example.com/fhir/StructureDefinition/dependent-patient-ref",
    "valueReference": {
      "reference": "Patient/patient-789",
      "display": "Mary Juma"
    }
  }, {
    "url": "http://afya-yangu.hie.example.com/fhir/StructureDefinition/household-membership",
    "valueBoolean": true
  }]
}
```

---

### Flow 3: BMS Adds Existing CR Client as Primary Policyholder

```mermaid
sequenceDiagram
    participant Admin as BMS Administrator
    participant BMS
    participant CR
    participant IOL
    
    Admin->>BMS: Create New Insurance Enrollment
    Admin->>BMS: Enter Member National ID
    
    BMS->>IOL: Search for Patient
    IOL->>CR: Query Patient by National ID
    CR-->>IOL: Patient Found (patient-123)
    IOL-->>BMS: Patient Details
    
    BMS->>BMS: Display Patient Info for Confirmation
    Note over BMS: John Juma, DOB: 1985-06-15,<br/>National ID: 12345678
    
    Admin->>BMS: Confirm Patient
    Admin->>BMS: Select Insurance Scheme
    Admin->>BMS: Enter Enrollment Details
    
    BMS->>BMS: Create Enrollment Record
    Note over BMS: Enrollment ID: ENR-2025-001<br/>Member Number: NHIF-12345<br/>Primary Member: patient-123<br/>Scheme: NHIF Family Cover
    
    BMS->>BMS: Generate Member Card Number
    BMS-->>Admin: Enrollment Created
    
    BMS->>IOL: Publish EnrollmentCreated Event
    Note over IOL: Event: New enrollment<br/>for patient-123
    IOL-->>AY: Event Delivered
    
    AY->>AY: Invalidate Insurance Cache
    AY->>AY: Notify Patient
```

---

### Flow 4: Member Adds Household Dependent as Scheme Beneficiary

```mermaid
sequenceDiagram
    participant Member as Primary Member
    participant AY as Afya Yangu
    participant INS as Insurance Service
    participant HH as Household Service
    participant BMS
    participant CR
    
    Member->>AY: Login to Afya Yangu
    Member->>AY: Navigate to "My Insurance"
    
    AY->>INS: Get User's Enrollments
    INS->>BMS: Query Enrollments
    BMS-->>INS: List of Schemes
    Note over INS: NHIF-12345 (Active)<br/>Private Insurance (Active)
    INS-->>AY: Display Enrollments
    
    Member->>AY: Select NHIF Scheme
    Member->>AY: Click "Add Beneficiary"
    
    AY->>HH: Get Household Members
    HH->>CR: Query RelatedPersons
    CR-->>HH: Household Members
    Note over HH: Jane Juma (Spouse)<br/>Mary Juma (Child)<br/>Tom Juma (Child)
    HH-->>AY: Display Available Dependents
    
    Member->>AY: Select "Mary Juma (Child)"
    
    AY->>INS: Add Beneficiary Request
    INS->>BMS: Validate Eligibility
    
    BMS->>BMS: Check Business Rules
    Note over BMS: - Max beneficiaries: 3/6 ✓<br/>- Age limit for child: 12 years ✓<br/>- Relationship allowed: CHILD ✓<br/>- Not already enrolled ✓
    
    alt Eligible
        BMS->>BMS: Create Beneficiary Record
        Note over BMS: Beneficiary ID: BEN-456<br/>Patient ID: patient-789<br/>Member Card: NHIF-12345-03<br/>Relationship: CHILD
        
        BMS->>BMS: Allocate Benefits
        BMS-->>INS: Beneficiary Created
        
        INS->>INS: Update Local Cache
        INS-->>AY: Success
        
        AY-->>Member: Mary added as beneficiary
        
        BMS->>IOL: Publish BeneficiaryAdded Event
        IOL-->>AY: Event Notification
        
    else Not Eligible
        BMS-->>INS: Validation Failed
        Note over BMS: Reason: Already enrolled<br/>in another scheme
        INS-->>AY: Error Message
        AY-->>Member: Cannot add: Already beneficiary elsewhere
    end
```

---

### Flow 5: Query Available Schemes and View Household Eligibility

```mermaid
sequenceDiagram
    participant Member
    participant AY as Afya Yangu
    participant INS as Insurance Service
    participant BMS
    participant HH as Household Service
    participant CR
    
    Member->>AY: View "Available Insurance Schemes"
    
    AY->>INS: Get Available Schemes
    INS->>BMS: Query Public Schemes
    BMS-->>INS: List of Schemes
    Note over BMS: - NHIF Family Cover<br/>- NHIF Individual<br/>- Private Insurance A<br/>- Private Insurance B
    
    par Get Current Enrollments
        INS->>BMS: Get Member's Enrollments
        BMS-->>INS: Current Enrollments
    and Get Household Info
        AY->>HH: Get Household Size
        HH->>CR: Count Dependents
        CR-->>HH: 3 dependents
        HH-->>AY: Household Size: 4 total
    end
    
    INS->>INS: Filter & Annotate Schemes
    Note over INS: - Mark enrolled schemes<br/>- Show eligibility<br/>- Calculate costs
    
    INS-->>AY: Annotated Scheme List
    AY-->>Member: Display Schemes
    
    Note over Member: Scheme Card Shows:<br/>✓ NHIF Family Cover (Enrolled)<br/>  3/6 beneficiaries<br/>○ Private Insurance A (Eligible)<br/>  Covers up to 5 members<br/>  Premium: 5,000 KES/month
    
    Member->>AY: Click "Enroll in Private Insurance A"
    
    AY->>INS: Initiate Enrollment
    INS->>BMS: Create Enrollment Request
    BMS->>BMS: Validate & Create
    BMS-->>INS: Enrollment Pending Payment
    
    INS-->>AY: Redirect to Payment
    AY-->>Member: Complete Payment to Activate
```

---

## Household Management Architecture

```mermaid
graph TB
    subgraph "Afya Yangu - Household Management"
        AYUI[Web/Mobile UI]
        AYHH[Household Service]
        AYINS[Insurance Service]
        AYCACHE[Redis Cache]
    end
    
    subgraph "Client Registry - Source of Truth"
        CRPAT[Patient Resources]
        CRREL[RelatedPerson Resources]
        CRIDX[Household Index]
    end
    
    subgraph "BMS - Insurance & Benefits"
        BMSSCH[Schemes Catalog]
        BMSENR[Enrollments]
        BMSBEN[Beneficiaries]
        BMSRULES[Eligibility Rules]
    end
    
    AYUI -->|1. Add Dependent| AYHH
    AYHH -->|2. Check Existing| CRREL
    CRREL -->|3. No Active Household| AYHH
    AYHH -->|4. Create Patient if needed| CRPAT
    AYHH -->|5. Create RelatedPerson| CRREL
    CRREL -->|6. Index Household| CRIDX
    
    AYUI -->|7. View Schemes| AYINS
    AYINS -->|8. Query| BMSSCH
    BMSSCH -->|9. Available Schemes| AYINS
    
    AYUI -->|10. Add Beneficiary| AYINS
    AYINS -->|11. Get Household| AYHH
    AYHH -->|12. Query| CRREL
    CRREL -->|13. Dependents List| AYINS
    AYINS -->|14. Add Beneficiary| BMSENR
    BMSENR -->|15. Validate| BMSRULES
    BMSRULES -->|16. Check CR Patient| CRPAT
    BMSENR -->|17. Create Beneficiary| BMSBEN
    BMSBEN -.->|References| CRPAT
    
    style CRPAT fill:#2ecc71,color:#fff
    style CRREL fill:#2ecc71,color:#fff
    style BMSBEN fill:#f39c12,color:#fff
    style AYHH fill:#3498db,color:#fff
```

---

## Validation Rules

### One Dependent, One Household Rule

```typescript
async function validateHouseholdMembership(
  dependentPatientId: string,
  newHouseholdHeadId: string
): Promise<ValidationResult> {
  // Check for existing active household membership
  const existingMembership = await cr.searchRelatedPerson({
    'related-patient': dependentPatientId,
    active: true,
    _has: 'Extension:household-membership:value=true'
  });
  
  if (existingMembership.total > 0) {
    const currentHead = existingMembership.entry[0].resource.patient.display;
    
    return {
      valid: false,
      reason: `Already a dependent in ${currentHead}'s household`,
      currentHousehold: existingMembership.entry[0].resource.patient.reference
    };
  }
  
  return { valid: true };
}
```

### BMS Beneficiary Eligibility Rules

```typescript
interface EligibilityRules {
  maxBeneficiaries: number;
  allowedRelationships: RelationshipType[];
  ageRestrictions: {
    [key in RelationshipType]?: {
      minAge?: number;
      maxAge?: number;
    };
  };
  oneSchemePerDependent?: boolean;  // Optional: restrict to one scheme
}

async function validateBeneficiaryEligibility(
  enrollmentId: string,
  dependentPatientId: string,
  relationship: RelationshipType
): Promise<ValidationResult> {
  const enrollment = await bms.getEnrollment(enrollmentId);
  const rules = enrollment.scheme.eligibilityRules;
  
  // Check 1: Max beneficiaries
  if (enrollment.beneficiaries.length >= rules.maxBeneficiaries) {
    return {
      valid: false,
      reason: `Maximum ${rules.maxBeneficiaries} beneficiaries reached`
    };
  }
  
  // Check 2: Relationship allowed
  if (!rules.allowedRelationships.includes(relationship)) {
    return {
      valid: false,
      reason: `${relationship} relationship not allowed in this scheme`
    };
  }
  
  // Check 3: Age restrictions
  const dependent = await cr.getPatient(dependentPatientId);
  const age = calculateAge(dependent.birthDate);
  const ageRule = rules.ageRestrictions[relationship];
  
  if (ageRule) {
    if (ageRule.minAge && age < ageRule.minAge) {
      return { valid: false, reason: `Minimum age ${ageRule.minAge}` };
    }
    if (ageRule.maxAge && age > ageRule.maxAge) {
      return { valid: false, reason: `Maximum age ${ageRule.maxAge} exceeded` };
    }
  }
  
  // Check 4: Not already a beneficiary in THIS scheme
  const alreadyBeneficiary = enrollment.beneficiaries.some(
    b => b.patientId === dependentPatientId
  );
  
  if (alreadyBeneficiary) {
    return {
      valid: false,
      reason: 'Already a beneficiary in this scheme'
    };
  }
  
  // Optional Check 5: One scheme per dependent rule
  if (rules.oneSchemePerDependent) {
    const otherEnrollments = await bms.getBeneficiaryEnrollments(dependentPatientId);
    if (otherEnrollments.length > 0) {
      return {
        valid: false,
        reason: 'Already a beneficiary in another scheme'
      };
    }
  }
  
  return { valid: true };
}
```

---

## Example: John Juma's Household

```
Household Head: John Juma (patient-123)
└── Household Members:
    ├── Jane Juma (patient-456) - Spouse
    ├── Mary Juma (patient-789) - Child (Age 12)
    └── Tom Juma (patient-012) - Child (Age 8)

Insurance Enrollments:

1. NHIF Family Cover (NHIF-12345)
   Primary Member: John Juma (patient-123)
   Beneficiaries:
   ├── Jane Juma (NHIF-12345-02)
   ├── Mary Juma (NHIF-12345-03)
   └── Tom Juma (NHIF-12345-04)

2. Private Insurance (PVT-67890)
   Primary Member: Jane Juma (patient-456)
   Beneficiaries:
   ├── John Juma (PVT-67890-02)
   └── Mary Juma (PVT-67890-03)
   
Note: 
- All 4 people have ONE Patient record in CR
- Household structure defined by RelatedPerson resources
- Mary is beneficiary in both schemes (allowed)
- Tom is only in NHIF (parents' choice)
```

---

## Household Transfer Process

```mermaid
sequenceDiagram
    participant OldHead as Old Household Head
    participant Dependent
    participant NewHead as New Household Head
    participant AY as Afya Yangu
    participant HH as Household Service
    participant CR
    participant BMS
    
    Note over OldHead,BMS: Scenario: Dependent moving to new household
    
    OldHead->>AY: Remove Dependent from Household
    AY->>HH: Remove Request
    
    HH->>BMS: Check Insurance Coverage
    BMS-->>HH: Dependent is beneficiary in 1 scheme
    
    HH-->>AY: Warning: Remove from insurance first
    AY-->>OldHead: Must remove from insurance schemes
    
    OldHead->>AY: Remove from Insurance
    AY->>BMS: Remove Beneficiary
    BMS-->>AY: Removed
    
    OldHead->>AY: Confirm Household Removal
    AY->>HH: Remove Dependent
    HH->>CR: Update RelatedPerson (set active=false)
    CR-->>HH: Updated
    HH-->>AY: Removed from Household
    
    Note over Dependent,NewHead: Dependent can now join new household
    
    NewHead->>AY: Add Dependent to My Household
    AY->>HH: Add Dependent Request
    HH->>CR: Check Active Membership
    CR-->>HH: No active membership ✓
    HH->>CR: Create New RelatedPerson
    CR-->>HH: Created
    HH-->>AY: Added to Household
    
    NewHead->>AY: Add to Insurance Scheme
    AY->>BMS: Add Beneficiary
    BMS-->>AY: Added
```

---

## GraphQL Queries

```graphql
type Query {
  myHousehold: Household!
  availableInsuranceSchemes: [InsuranceScheme!]!
  householdDependentEligibility(
    dependentId: ID!
    schemeId: ID!
  ): EligibilityResult!
}

type Mutation {
  addHouseholdDependent(input: DependentInput!): HouseholdMember!
  removeHouseholdDependent(dependentId: ID!): Boolean!
  transferDependent(
    dependentId: ID!
    newHouseholdHeadId: ID!
  ): HouseholdMember!
  addSchemeBeneficiary(
    enrollmentId: ID!
    dependentId: ID!
  ): Beneficiary!
}

type Household {
  primaryMember: Patient!
  members: [HouseholdMember!]!
  insuranceEnrollments: [InsuranceEnrollment!]!
  totalMembers: Int!
}

type HouseholdMember {
  patient: Patient!
  relationship: RelationshipType!
  isDependent: Boolean!
  addedDate: DateTime!
  insuranceCoverage: [InsuranceCoverage!]!
  canBeAddedToSchemes: [InsuranceScheme!]!
}

type EligibilityResult {
  eligible: Boolean!
  reasons: [String!]!
  constraints: SchemeConstraints
}
```

---

**Next Document**: [PP_05_Insurance_Benefits.md](PP_05_Insurance_Benefits.md)
