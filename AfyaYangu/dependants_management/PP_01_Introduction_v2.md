# Patient Portal (Afya Yangu) - Introduction

## Overview

The Patient Portal, branded as **Afya Yangu** (My Health), is a consumer-facing digital platform that empowers patients with secure access to their health information, insurance benefits, household dependents management, and care coordination within the national Health Information Exchange (HIE) ecosystem.

**Purpose**: Provide patients with a unified, mobile-first interface to manage their healthcare journey, from registration to clinical data access and insurance benefit tracking.

---

## What is Afya Yangu?

Afya Yangu serves as the primary digital touchpoint between patients and the healthcare system, enabling:

- **Self-Service Registration**: Patients can register themselves and their family members
- **Health Information Access**: View clinical encounters, prescriptions, lab results, and appointments
- **Insurance Management**: Track benefit balances, manage dependents as beneficiaries, and monitor enrollments
- **Household Management**: Create and maintain household structures with dependent relationships
- **Care Coordination**: Schedule appointments, communicate with providers, and manage health records

---

## Key Capabilities

### 1. Patient Registration & Identity Management
- Self-registration with national ID verification
- Integration with Client Registry (CR) for master patient index
- Duplicate detection to ensure one unique identity per person
- Secure credential creation with email/SMS verification

### 2. Household & Dependent Management
- Add dependents (spouse, children, parents) to household
- Link existing patients as dependents (reuse CR records)
- **One dependent, one household rule**: Each dependent can only belong to one household at a time
- Manage dependent relationships across multiple insurance schemes
- Support for guardianship and minor access controls

### 3. Insurance & Benefits
- View all insurance enrollments (national and private)
- Real-time benefit balance tracking
- Add household dependents as beneficiaries to insurance schemes
- Support for multiple scheme enrollments (one person can be beneficiary in multiple schemes)
- Integration with Benefits Management System (BMS)

### 4. Clinical Data Access
- Timeline view of clinical encounters
- Active prescriptions from e-Prescription system (eRX)
- Recent lab results and imaging reports
- Immunization history and vital signs
- Allergy and condition tracking

### 5. Appointment Management
- View upcoming appointments
- Schedule new appointments with providers
- Receive appointment reminders
- Telemedicine consultation support

---

## Core Architectural Principles

### 1. HIE Integration First
All data flows through the OpenHIE Interoperability Layer (IOL) using HL7 FHIR R4 standards, ensuring:
- Standardized data exchange
- Interoperability with existing health systems
- Centralized security and audit logging
- Consistent terminology and coding

### 2. Client Registry as Source of Truth
- Every person has ONE unique Patient record in the Client Registry
- Relationships stored as FHIR RelatedPerson resources
- Household structures reference existing CR Patient IDs
- Insurance beneficiaries link to CR Patient records

### 3. Real-Time Data Aggregation
- GraphQL Backend-for-Frontend (BFF) aggregates data from multiple sources
- Scatter-gather pattern for parallel data fetching
- Multi-layer caching for performance optimization
- Event-driven updates for insurance balances

### 4. Security & Privacy by Design
- OAuth 2.0 + OpenID Connect authentication
- Role-based access control with consent management
- End-to-end encryption for sensitive data
- Comprehensive audit logging (ATNA compliant)
- Separate access controls for minors' data

---

## System Integration Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Afya Yangu Portal                     │
│              (Web App + Mobile App)                      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   GraphQL BFF Layer   │
            │   (Data Aggregation)  │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  OpenHIE IOL (FHIR)  │
            │  Interoperability     │
            └───────────┬───────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        ▼               ▼               ▼              ▼
    ┌───────┐      ┌───────┐      ┌──────┐      ┌──────┐
    │  CR   │      │  SHR  │      │ BMS  │      │ eRX  │
    │(MPI)  │      │(EHR)  │      │(Ins) │      │(Rx)  │
    └───────┘      └───────┘      └──────┘      └──────┘
```

**Key Integration Points**:
- **Client Registry (CR)**: Patient demographics, identity management, household relationships
- **Shared Health Record (SHR)**: Clinical encounters, diagnoses, procedures
- **Benefits Management System (BMS)**: Insurance enrollments, benefit balances, claims, scheme management
- **e-Prescription (eRX)**: Active prescriptions, medication history
- **Health Facility Registry (HFR)**: Facility information for appointments
- **Appointment Scheduler**: Appointment booking and management

---

## Key Technical Features

### GraphQL API for Efficient Data Access
- Single endpoint for all patient data needs
- Client controls exactly what data to fetch
- Automatic query batching and deduplication
- Built-in caching and performance optimization

### Event-Driven Architecture
- Real-time benefit balance updates via Kafka events
- Insurance status change notifications
- Clinical data availability alerts
- Asynchronous processing for non-blocking operations

### Multi-Layer Caching
- **Client-side**: Service workers for offline access
- **Server-side**: Redis for frequently accessed data
- **CDN**: Static assets and public content
- Cache invalidation via event triggers

### Offline-First Mobile App
- React Native for cross-platform (iOS/Android)
- Local SQLite database for offline data
- Background sync when connectivity restored
- Progressive Web App (PWA) for web users

---

## Unique Architectural Considerations

### 1. One Client, Multiple Roles
**Challenge**: A person can be:
- Primary member in Insurance Scheme A
- Beneficiary in Insurance Scheme B (under spouse)
- Beneficiary in Insurance Scheme C (under parent)

**Solution**: 
- ONE Patient record in Client Registry (patientId: ABC)
- Multiple Insurance Enrollment records referencing same patientId
- Each enrollment specifies role (PRIMARY vs BENEFICIARY)

### 2. One Dependent, One Household
**Challenge**: Prevent a dependent from being added to multiple households simultaneously

**Solution**:
- Household ownership tracked in CR via RelatedPerson resources
- System enforces single active household membership per dependent
- Transfers between households require explicit removal and re-assignment
- Audit trail maintained for all household changes

### 3. Household Structure with Circular Dependencies
**Challenge**: Household relationships can be bidirectional
- John Juma (primary) has Jane Juma as spouse
- Jane Juma (primary) has John Juma as spouse
- Both can add Mary Juma as child

**Solution**:
- RelatedPerson resources in CR define relationships
- Afya Yangu UI manages bidirectional display
- Validation prevents duplicate relationships
- Each household member can have their own portal account

### 4. Real-Time Benefit Updates
**Challenge**: Benefit balances change when patient uses healthcare services

**Solution**:
- BMS publishes events when benefits are utilized
- Afya Yangu subscribes to events via Kafka
- Cache invalidated immediately
- Push notification sent to patient
- Next portal access shows updated balance

---

## Security Highlights

### Authentication
- OAuth 2.0 Authorization Code + PKCE flow
- Multi-factor authentication support
- Biometric login for mobile (fingerprint, Face ID)
- Session management with refresh tokens

### Authorization
- Patient can view own data
- Parent/guardian can view minor dependent data
- Spouse can view spouse data (with consent)
- No access to adult dependent clinical data without explicit consent

### Data Privacy
- FHIR Consent resources for data sharing
- Audit logging for all data access (ATNA)
- Encryption at rest and in transit (TLS 1.3)
- Anonymized analytics and reporting

---

## Document Structure

This Afya Yangu architecture documentation is organized into focused sections:

1. **[Introduction](PP_01_Introduction.md)** (This Document)
   - Overview and core capabilities
   - Integration summary
   - Key architectural principles

2. **[Core Architecture](PP_02_Core_Architecture.md)**
   - System architecture diagrams
   - Component descriptions
   - Technology stack

3. **[Registration & Identity](PP_03_Registration_Identity.md)**
   - Patient registration flow
   - CR integration patterns
   - Identity verification

4. **[Household & Dependent Management](PP_04_Family_Dependents.md)**
   - Household structure architecture
   - Dependent linking (existing vs new)
   - Relationship management
   - BMS-CR-Afya Yangu dependent workflows

5. **[Insurance & Benefits](PP_05_Insurance_Benefits.md)**
   - Insurance enrollment architecture
   - BMS integration (sync + async)
   - Beneficiary management
   - Real-time balance updates

6. **[Clinical Data Access](PP_06_Clinical_Data.md)**
   - Clinical data aggregation patterns
   - SHR, eRX, Lab integration
   - Timeline view architecture

7. **[Security & Privacy](PP_07_Security_Privacy.md)**
   - Authentication & authorization
   - Consent management
   - Audit logging
   - Data protection

---

## Target Audience

This documentation is designed for:
- **System Architects**: Understanding integration patterns and data flows
- **Software Developers**: Implementing Afya Yangu features
- **Technical Leads**: Making technology and design decisions
- **Integration Engineers**: Connecting to HIE registries and ecosystem apps
- **Security Officers**: Reviewing security and privacy controls
- **Project Managers**: Planning implementation roadmap

---

## Key Takeaways

1. **Afya Yangu is NOT a standalone system** - it's a consumer-facing interface to the national HIE ecosystem

2. **Client Registry (CR) is the source of truth** for patient identity - portal creates and references CR records

3. **One person = One CR Patient record** - regardless of how many insurance schemes or household relationships they have

4. **One dependent, one household** - ensures clear household structure and prevents conflicts in dependent management

5. **BMS manages insurance schemes** - Afya Yangu queries available schemes and enrolls household dependents as beneficiaries

6. **Real-time integration** is critical for benefit balances and insurance status to ensure patients have accurate information

7. **GraphQL BFF layer** optimizes data access by aggregating from multiple backend systems into patient-friendly responses

8. **Event-driven architecture** enables asynchronous updates without constant polling, improving performance and user experience

9. **Security and privacy** are built-in at every layer, with comprehensive audit logging and consent management

---

## Glossary

- **Afya Yangu**: "My Health" in Swahili - the patient portal brand name
- **Household**: A group of related individuals managed by a primary member (household head)
- **Dependent**: A household member managed by the household head (can be spouse, child, parent, etc.)
- **Primary Member/Policyholder**: The main account holder in an insurance scheme
- **Beneficiary**: A person covered under an insurance scheme (can be primary or dependent)
- **CR**: Client Registry - the master patient index
- **BMS**: Benefits Management System - manages insurance schemes and enrollments
- **HIE**: Health Information Exchange

---

**Next Document**: [PP_02_Core_Architecture.md](PP_02_Core_Architecture.md) - Detailed system architecture and components
