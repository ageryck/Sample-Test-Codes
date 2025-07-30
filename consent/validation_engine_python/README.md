# FHIR R4B Consent Validation Engine

## Overview

The Consent Validation Engine is a Python-based system designed to validate and manage healthcare data access requests according to FHIR R4B consent standards. This system ensures compliance with patient consent policies while providing secure, auditable access to healthcare data.

## Architecture

### Core Components

#### 1. ConsentValidationEngine (`consent_validation_engine.py`)
The main validation engine that processes consent requests and makes access decisions.

**Key Features:**
- Validates consent requests against active consent records
- Performs patient identity and requester credential validation
- Implements role-based access control (RBAC)
- Handles temporal consent validation with timezone-aware datetime comparisons
- Generates OAuth 2.0 access tokens for approved requests
- Provides comprehensive audit logging

**Main Methods:**
- `validate_consent_request()`: Main entry point for consent validation
- `_find_best_consent_match()`: Finds the most appropriate consent for a request
- `_validate_temporal_scope()`: Validates time-based consent constraints
- `_evaluate_granular_permissions()`: Determines specific data access permissions

#### 2. Data Models

**ConsentRequest** (`consent_request.py`)
```python
@dataclass
class ConsentRequest:
    request_id: str
    patient_id: str
    requester_id: str
    requester_organization: str
    requester_role: str
    data_types: List[str]
    purpose: str
    time_range: Dict[str, str]
    emergency_context: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
```

**ConsentDecision** (`consent_decision.py`)
```python
@dataclass
class ConsentDecision:
    decision: ConsentDecisionType
    reason: str
    permissions: Dict[str, Any] = field(default_factory=dict)
    access_token: Optional[str] = None
    expiry_time: Optional[Any] = None
    restrictions: List[str] = field(default_factory=list)
    audit_info: Dict[str, Any] = field(default_factory=dict)
```

**DataPermissions** (`data_permissions.py`)
```python
@dataclass
class DataPermissions:
    allowed: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)
    masked: List[str] = field(default_factory=list)
    pseudonymized: List[str] = field(default_factory=list)
```

#### 3. Enumerations

**ConsentStatus** (`consent_status.py`)
- `DRAFT`: Consent is being prepared
- `PROPOSED`: Consent has been proposed but not yet active
- `ACTIVE`: Consent is currently valid and enforceable
- `REJECTED`: Consent has been rejected
- `INACTIVE`: Consent is no longer active
- `ENTERED_IN_ERROR`: Consent was entered in error

**ConsentDecisionType** (`consent_decision_type.py`)
- `APPROVED`: Access request approved
- `DENIED`: Access request denied
- `PENDING`: Access request requires additional review

**SensitivityLevel** (`sensitivity_level.py`)
- `LOW`: Basic demographic data
- `MEDIUM`: General clinical data
- `HIGH`: Sensitive diagnoses and medications
- `CRITICAL`: Mental health, genetic data, controlled substances

#### 4. FHIR Integration (`fhir_utils.py`)

**Functions:**
- `create_fhir_consent_from_decision()`: Generates FHIR Consent resources
- `generate_audit_event()`: Creates FHIR AuditEvent resources for compliance

#### 5. Utilities (`utils.py`)

**Key Functions:**
- `parse_datetime_safe()`: Timezone-aware datetime parsing
- `get_current_utc()`: Gets current UTC time with timezone awareness
- `validate_patient_id_format()`: Validates Kenyan National Health ID format
- `get_data_sensitivity_level()`: Determines data sensitivity levels

## Data Sensitivity Levels

| Data Type | Sensitivity Level | Description |
|-----------|------------------|-------------|
| Patient.demographics | LOW (1) | Basic patient information |
| Observation.vital-signs | LOW (1) | Basic vital signs |
| Observation.laboratory | MEDIUM (2) | Lab results |
| DiagnosticReport.imaging | MEDIUM (2) | Medical imaging reports |
| Condition.diagnosis | HIGH (3) | General diagnoses |
| Condition.mental-health | CRITICAL (4) | Mental health conditions |
| MedicationRequest.controlled | CRITICAL (4) | Controlled substances |
| AllergyIntolerance | CRITICAL (4) | Allergy information |
| Observation.genetic | CRITICAL (5) | Genetic data |

## Purpose Codes and Durations

| Purpose Code | Description | Default Duration |
|-------------|-------------|------------------|
| TREAT | Treatment | 30 days |
| ETREAT | Emergency Treatment | 24 hours |
| HPAYMT | Healthcare Payment | 180 days |
| HOPERAT | Healthcare Operations | 90 days |
| HRESCH | Healthcare Research | 5 years |
| PUBHLTH | Public Health | 1 year |
| HMARKT | Healthcare Marketing | 90 days |
| HDIRECT | Healthcare Directory | 1 year |

## Role-Based Access Control

### Physician
- **Allowed Data**: All data types (*)
- **Denied Data**: None
- **Special Permissions**: Can override emergency restrictions
- **Masked Fields**: None

### Nurse
- **Allowed Data**: Patient demographics, observations, conditions, allergies
- **Denied Data**: Financial data, coverage information
- **Masked Fields**: Patient identifier values
- **Special Permissions**: Can override emergency restrictions

### Researcher
- **Allowed Data**: All data types (*)
- **Pseudonymized Fields**: Patient identifiers, names, contact info, addresses
- **Special Permissions**: Cannot override emergency restrictions

### Pharmacist
- **Allowed Data**: Medications, allergies, basic demographics
- **Denied Data**: Diagnostic reports, lab results
- **Masked Fields**: Patient address, telecom
- **Special Permissions**: Cannot override emergency restrictions

## Testing Framework

### ConsentTestResources (`consent_test_resources.py`)

Provides sample data for testing:
- `create_sample_active_consents()`: Returns sample FHIR consent resources
- `create_sample_consent_requests()`: Returns sample consent requests

### Test Runner (`main.py`)

Comprehensive test suite including:
- Consent validation tests
- FHIR resource generation examples
- Datetime handling validation
- Performance metrics

**Key Test Functions:**
- `run_consent_validation_tests()`: Main test suite
- `demonstrate_fhir_generation()`: FHIR resource creation examples
- `test_datetime_fixes()`: Timezone handling validation

## Security Features

### Authentication & Authorization
- OAuth 2.0 access token generation
- Role-based access control (RBAC)
- Organization-based access restrictions
- Multi-factor validation (patient + requester + organization)

### Audit & Compliance
- Comprehensive audit logging
- FHIR AuditEvent generation
- Request tracking and monitoring
- Compliance with healthcare data protection standards

### Data Protection
- Field-level masking and pseudonymization
- Sensitivity-based access controls
- Time-bound access tokens
- Emergency access overrides

## Error Handling

### Fixed Issues
- **Timezone-aware datetime comparisons**: Resolved offset-naive vs offset-aware comparison errors
- **Robust datetime parsing**: Safe handling of various datetime formats
- **Input validation**: Comprehensive parameter validation with clear error messages

### Error Categories
- **Input Validation Errors**: Invalid parameters, malformed data
- **Authentication Errors**: Invalid credentials, inactive users
- **Authorization Errors**: Insufficient permissions, expired consents
- **System Errors**: Database connectivity, parsing errors

## Usage Examples

### Basic Consent Validation
```python
from consent_validation_engine import ConsentValidationEngine
from consent_request import ConsentRequest

# Initialize engine
engine = ConsentValidationEngine()

# Create request
request = ConsentRequest(
    request_id="req-001",
    patient_id="CR123456789",
    requester_id="dr-smith-001",
    requester_organization="knh-hospital",
    requester_role="physician",
    data_types=["Patient.demographics"],
    purpose="TREAT",
    time_range={
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-12-31T23:59:59Z"
    }
)

# Validate consent
decision = engine.validate_consent_request(request, active_consents)
print(f"Decision: {decision.decision.value}")
print(f"Reason: {decision.reason}")
```

### FHIR Resource Generation
```python
from fhir_utils import create_fhir_consent_from_decision, generate_audit_event

# Generate FHIR Consent resource
if decision.decision == ConsentDecisionType.APPROVED:
    fhir_consent = create_fhir_consent_from_decision(request, decision)
    audit_event = generate_audit_event(request, decision)
```

## Installation & Dependencies

### Required Packages
- Python 3.8+
- dataclasses (for data models)
- datetime (for time handling)
- typing (for type hints)
- json (for FHIR resource serialization)
- logging (for audit trails)
- uuid (for token generation)
- hashlib (for token security)

### Running Tests
```bash
python main.py
```

## Configuration

### Environment Variables
- Patient registry endpoints
- Credential validation services
- Audit logging destinations
- Token encryption keys

### Customization Points
- Sensitivity level mappings
- Purpose duration configurations
- Role permission matrices
- Compatible purpose relationships

## Compliance & Standards

- **FHIR R4B**: Full compliance with FHIR consent resource specifications
- **ISO 27001**: Security management standards
- **GDPR**: Data protection and privacy compliance
- **HIPAA**: Healthcare data protection (where applicable)
- **Kenya Data Protection Act**: Local data protection compliance

## Version History

- **v2.0.0**: Current version with timezone-aware datetime handling, enhanced security, and comprehensive test suite
- **v1.x**: Initial implementation with basic consent validation

## Contributing

1. Follow existing code patterns and conventions
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure FHIR compliance for all healthcare data handling
5. Implement proper error handling and logging

## Support & Maintenance

For issues or questions:
1. Check the test suite in `main.py` for usage examples
2. Review error logs for debugging information
3. Validate FHIR resource structures against the specification
4. Ensure timezone-aware datetime handling for temporal validations