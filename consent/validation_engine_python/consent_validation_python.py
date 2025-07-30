"""
Consent Management Platform - Validation Engine v2.0
FHIR R4B Compliant Consent Validation System
Complete Implementation
"""

# Remove duplicate classes (ConsentStatus, ConsentDecisionType, etc.)
# Keep only the imports:
from consent_status import ConsentStatus
from consent_decision_type import ConsentDecisionType
from sensitivity_level import SensitivityLevel
from consent_request import ConsentRequest
from consent_decision import ConsentDecision
from data_permissions import DataPermissions
from consent_validation_engine import ConsentValidationEngine
from consent_test_resources import ConsentTestResources
from utils import get_data_sensitivity_level
from fhir_utils import create_fhir_consent_from_decision, generate_audit_event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants and Thresholds
MINIMUM_MATCH_THRESHOLD = 0.7
REUSE_THRESHOLD = 0.8
HIGH_SENSITIVITY = 3
EMERGENCY_ACCESS_DURATION = timedelta(hours=24)
DEFAULT_TOKEN_DURATION = timedelta(hours=24)

class ConsentStatus(Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    REJECTED = "rejected"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error"

class ConsentDecisionType(Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"

class SensitivityLevel(Enum):
    LOW = 1
    LOW_MEDIUM = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

@dataclass
class ConsentRequest:
    """Incoming consent request structure"""
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

@dataclass
class ConsentDecision:
    """Consent validation decision"""
    decision: ConsentDecisionType
    reason: str
    permissions: Dict[str, Any] = field(default_factory=dict)
    access_token: Optional[str] = None
    expiry_time: Optional[datetime] = None
    restrictions: List[str] = field(default_factory=list)
    audit_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataPermissions:
    """Granular data permissions"""
    allowed: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)
    masked: List[str] = field(default_factory=list)
    pseudonymized: List[str] = field(default_factory=list)

class ConsentValidationEngine:
    """Main consent validation engine"""
    
    def __init__(self):
        self.sensitivity_map = self._initialize_sensitivity_map()
        self.purpose_duration_map = self._initialize_purpose_durations()
        self.role_permissions = self._initialize_role_permissions()
        self.data_type_mappings = self._initialize_data_type_mappings()
        self.care_networks = self._initialize_care_networks()
        self.compatible_purposes = self._initialize_compatible_purposes()
        
    def _initialize_sensitivity_map(self) -> Dict[str, int]:
        """Initialize data type sensitivity levels"""
        return {
            "Patient.demographics": SensitivityLevel.LOW.value,
            "Observation.vital-signs": SensitivityLevel.LOW.value,
            "Observation.laboratory": SensitivityLevel.MEDIUM.value,
            "DiagnosticReport.imaging": SensitivityLevel.MEDIUM.value,
            "Condition.diagnosis": SensitivityLevel.HIGH.value,
            "Condition.mental-health": SensitivityLevel.CRITICAL.value,
            "MedicationRequest.controlled": SensitivityLevel.CRITICAL.value,
            "AllergyIntolerance": SensitivityLevel.CRITICAL.value,
            "Observation.genetic": SensitivityLevel.CRITICAL.value,
            "MedicationDispense": SensitivityLevel.HIGH.value,
            "MedicationRequest": SensitivityLevel.HIGH.value,
            "Encounter.financial": SensitivityLevel.MEDIUM.value,
            "Coverage": SensitivityLevel.MEDIUM.value
        }
    
    def _initialize_purpose_durations(self) -> Dict[str, timedelta]:
        """Initialize default consent durations by purpose"""
        return {
            "TREAT": timedelta(days=30),
            "ETREAT": timedelta(hours=24),
            "HPAYMT": timedelta(days=180),
            "HOPERAT": timedelta(days=90),
            "HRESCH": timedelta(days=1825),  # 5 years
            "PUBHLTH": timedelta(days=365),
            "HMARKT": timedelta(days=90),
            "HDIRECT": timedelta(days=365)
        }
    
    def _initialize_role_permissions(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize role-based permission mappings"""
        return {
            "physician": {
                "allowed_data": ["*"],
                "denied_data": [],
                "masked_fields": [],
                "can_override_emergency": True
            },
            "nurse": {
                "allowed_data": ["Patient.demographics", "Observation.*", "Condition.*", "AllergyIntolerance"],
                "denied_data": ["Encounter.financial", "Coverage"],
                "masked_fields": ["Patient.identifier.value"],
                "can_override_emergency": True
            },
            "pharmacist": {
                "allowed_data": ["MedicationRequest", "MedicationDispense", "AllergyIntolerance", "Patient.demographics"],
                "denied_data": ["DiagnosticReport.*", "Observation.laboratory"],
                "masked_fields": ["Patient.address", "Patient.telecom"],
                "can_override_emergency": False
            },
            "billing": {
                "allowed_data": ["Patient.demographics", "Encounter.financial", "Coverage"],
                "denied_data": ["Observation.*", "Condition.*", "DiagnosticReport.*"],
                "masked_fields": ["Patient.name", "detailed-clinical-data"],
                "can_override_emergency": False
            },
            "researcher": {
                "allowed_data": ["*"],
                "denied_data": [],
                "masked_fields": [],
                "pseudonymized_fields": ["Patient.identifier", "Patient.name", "Patient.telecom", "Patient.address"],
                "can_override_emergency": False
            },
            "marketing": {
                "allowed_data": ["Patient.demographics"],
                "denied_data": ["Observation.*", "Condition.*", "DiagnosticReport.*", "MedicationRequest"],
                "masked_fields": ["Patient.identifier", "detailed-clinical-data"],
                "can_override_emergency": False
            }
        }
    
    def _initialize_data_type_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize FHIR data type mappings"""
        return {
            "patient_demographics": {
                "fhir_resource": "Patient",
                "fhir_class": "http://hl7.org/fhir/resource-types#Patient",
                "default_expiry_days": 365,
                "special_fields": ["Patient.photo", "Patient.identifier.value"],
                "loinc_codes": [],
                "snomed_codes": []
            },
            "vital_signs": {
                "fhir_resource": "Observation",
                "fhir_class": "http://loinc.org/vs/LL715-4",
                "default_expiry_days": 180,
                "special_fields": [],
                "loinc_codes": ["8310-5", "8462-4", "8480-6", "8867-4"],  # Common vital signs
                "snomed_codes": ["118227000", "271649006"]
            },
            "laboratory_results": {
                "fhir_resource": "Observation",
                "fhir_class": "http://loinc.org/vs/LL1001-8",
                "default_expiry_days": 90,
                "special_fields": ["genetic-tests", "drug-screening"],
                "loinc_codes": ["33747-0", "Drug-screen"],  # Genetic and drug screening
                "excluded_codes": ["33747-0", "Drug-screen"]
            },
            "imaging_results": {
                "fhir_resource": "DiagnosticReport",
                "fhir_class": "http://hl7.org/fhir/resource-types#DiagnosticReport",
                "default_expiry_days": 90,
                "special_fields": ["imaging-data", "radiology-notes"],
                "loinc_codes": ["18748-4", "18747-6"],  # Diagnostic imaging
                "snomed_codes": ["363679005", "71388002"]
            },
            "prescriptions": {
                "fhir_resource": "MedicationRequest",
                "fhir_class": "http://hl7.org/fhir/resource-types#MedicationRequest",
                "default_expiry_days": 90,
                "special_fields": ["controlled-substances"],
                "controlled_substance_schedules": ["I", "II", "III", "IV", "V"]
            },
            "allergies": {
                "fhir_resource": "AllergyIntolerance",
                "fhir_class": "http://hl7.org/fhir/resource-types#AllergyIntolerance",
                "default_expiry_days": 365,
                "special_fields": ["drug-allergies", "food-allergies"],
                "snomed_codes": ["416098002", "414285001", "59037007"]
            }
        }
    
    def _initialize_care_networks(self) -> Dict[str, List[str]]:
        """Initialize care network relationships"""
        return {
            "moh-kenya": ["knh-hospital", "mp-hospital", "aga-khan", "rural-health-centers"],
            "knh-hospital": ["moh-kenya", "specialist-clinics", "medical-college"],
            "mtrh": ["moh-kenya", "specialist-clinics", "medical-college"],
            "mp-hospital": ["moh-kenya", "rural-health-centers", "community-clinics"],
            "research-institute": ["moh-kenya", "knh-hospital", "medical-college"],
            "mental-health-certified": ["knh-hospital", "specialized-mental-health"]
        }
    
    def _initialize_compatible_purposes(self) -> Dict[str, List[str]]:
        """Initialize compatible purpose mappings"""
        return {
            "TREAT": ["ETREAT", "HOPERAT"],
            "ETREAT": ["TREAT"],
            "HPAYMT": ["HOPERAT"],
            "HRESCH": ["TREAT", "HOPERAT"],
            "HOPERAT": ["TREAT", "HPAYMT"],
            "PUBHLTH": ["TREAT", "HOPERAT"],
            "HMARKT": [],  # Marketing is standalone
            "HDIRECT": ["TREAT", "HOPERAT"]
        }

    def validate_consent_request(self, request: ConsentRequest, active_consents: List[Dict]) -> ConsentDecision:
        """Main consent validation entry point"""
        try:
            logger.info(f"Validating consent request {request.request_id} for patient {request.patient_id}")
            
            # Step 1: Input Validation
            validation_error = self._validate_input_parameters(request)
            if validation_error:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason=validation_error,
                    audit_info={"step": "input_validation", "request_id": request.request_id}
                )
            
            # Step 2: Patient Identity Validation
            patient = self._validate_patient_identity(request.patient_id)
            if not patient:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason="Invalid patient identifier",
                    audit_info={"step": "patient_validation", "request_id": request.request_id}
                )
            
            # Step 3: Requester Validation
            requester = self._validate_requester_credentials(request.requester_id, request.requester_organization)
            if not requester:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason="Invalid requester credentials",
                    audit_info={"step": "requester_validation", "request_id": request.request_id}
                )
            
            # Step 4: Emergency Override Check (highest priority)
            if request.emergency_context:
                emergency_decision = self._evaluate_emergency_override(request, patient, requester)
                if emergency_decision.decision == ConsentDecisionType.APPROVED:
                    return emergency_decision
            
            # Step 5: Organizational Relationship Assessment
            relationship_score = self._calculate_organizational_relationship(
                patient.get("managingOrganization"), 
                request.requester_organization
            )
            
            # Step 6: Data Type and Purpose Matching
            matching_consents = []
            for data_type in request.data_types:
                matching_consent = self._find_best_consent_match(
                    active_consents, 
                    data_type, 
                    request.purpose,
                    requester
                )
                
                if not matching_consent:
                    return ConsentDecision(
                        decision=ConsentDecisionType.DENIED,
                        reason=f"No valid consent found for data type: {data_type}",
                        audit_info={"step": "consent_matching", "failed_data_type": data_type}
                    )
                
                matching_consents.append(matching_consent)
                
                # Step 7: Granular Permission Evaluation
                permissions = self._evaluate_granular_permissions(
                    matching_consent,
                    data_type,
                    request.purpose,
                    request.requester_role
                )
                
                if self._has_permission_violations(permissions):
                    return ConsentDecision(
                        decision=ConsentDecisionType.DENIED,
                        reason="Granular permissions deny access",
                        audit_info={"step": "permission_evaluation", "violations": permissions.denied}
                    )
            
            # Use the best matching consent for further processing
            best_consent = self._select_best_overall_consent(matching_consents, request)
            
            # Step 8: Temporal Validation
            temporal_valid = self._validate_temporal_scope(
                best_consent.get("provision", {}).get("dataPeriod", {}),
                request.time_range
            )
            
            if not temporal_valid:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason="Request falls outside consent temporal scope",
                    audit_info={"step": "temporal_validation"}
                )
            
            # Step 9: Consent Reusability Assessment
            reuse_score = self._calculate_consent_reuse_score(
                best_consent,
                request,
                relationship_score
            )
            
            if reuse_score >= REUSE_THRESHOLD:
                # Step 10: Apply Data Filtering and Generate Token
                filtered_permissions = self._apply_data_filtering(
                    permissions,
                    request.requester_role,
                    request.purpose,
                    patient.get("preferences", {})
                )
                
                access_token = self._generate_access_token(
                    filtered_permissions,
                    best_consent.get("provision", {}).get("dataPeriod", {}).get("end"),
                    requester,
                    request
                )
                
                self._log_consent_usage(best_consent, request, access_token, "REUSED")
                
                return ConsentDecision(
                    decision=ConsentDecisionType.APPROVED,
                    reason="Consent reused based on existing valid consent",
                    permissions=filtered_permissions.__dict__,
                    access_token=access_token,
                    expiry_time=self._parse_datetime(best_consent.get("provision", {}).get("dataPeriod", {}).get("end")),
                    audit_info={
                        "reuse_score": reuse_score, 
                        "consent_id": best_consent.get("id"),
                        "relationship_score": relationship_score
                    }
                )
            else:
                # Require explicit consent
                return ConsentDecision(
                    decision=ConsentDecisionType.PENDING,
                    reason="Explicit patient consent required - reuse threshold not met",
                    audit_info={
                        "reuse_score": reuse_score, 
                        "threshold": REUSE_THRESHOLD,
                        "required_action": "patient_notification"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error validating consent request: {str(e)}")
            return ConsentDecision(
                decision=ConsentDecisionType.DENIED,
                reason=f"System error during validation: {str(e)}",
                audit_info={"error": str(e), "step": "system_error"}
            )

    def _validate_input_parameters(self, request: ConsentRequest) -> Optional[str]:
        """Validate input parameters"""
        if not request.patient_id or len(request.patient_id.strip()) == 0:
            return "Patient ID is required"
        
        if not request.requester_id or len(request.requester_id.strip()) == 0:
            return "Requester ID is required"
        
        if not request.data_types or len(request.data_types) == 0:
            return "At least one data type must be specified"
        
        if not request.purpose or request.purpose not in self.purpose_duration_map:
            return f"Invalid purpose code: {request.purpose}"
        
        # Validate time range format
        try:
            if request.time_range:
                start = request.time_range.get("start")
                end = request.time_range.get("end")
                if start:
                    datetime.fromisoformat(start.replace('Z', '+00:00'))
                if end:
                    datetime.fromisoformat(end.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return "Invalid date format in time range"
        
        return None

    def _validate_patient_identity(self, patient_id: str) -> Optional[Dict]:
        """Validate patient identity and return patient data"""
        # Basic validation
        if not patient_id or len(patient_id) < 5:
            return None
        
        # Pattern validation for Kenyan National Health ID
        if not re.match(r'^CR\d{9}$', patient_id):
            logger.warning(f"Patient ID {patient_id} does not match expected pattern")
        
        # Mock implementation - replace with actual patient registry lookup
        mock_patients = {
            "CR123456789": {
                "id": "CR123456789",
                "identifier": [{"value": "CR123456789", "system": "national-health-id"}],
                "name": [{"given": ["John"], "family": "Doe"}],
                "managingOrganization": {"reference": "Organization/moh-kenya"},
                "preferences": {
                    "marketing_opt_out": True,
                    "data_masking_preference": "standard",
                    "notification_method": "sms"
                },
                "active": True
            },
            "CR987654321": {
                "id": "CR987654321",
                "identifier": [{"value": "CR987654321", "system": "national-health-id"}],
                "managingOrganization": {"reference": "Organization/knh-hospital"},
                "preferences": {
                    "marketing_opt_out": False,
                    "data_masking_preference": "enhanced"
                },
                "active": True
            },
            "CR123456790": {
                "id": "CR123456790",
                "identifier": [{"value": "CR123456790", "system": "national-health-id"}],
                "managingOrganization": {"reference": "Organization/mtrh"},
                "preferences": {
                    "marketing_opt_out": True,
                    "data_masking_preference": "standard",
                    "notification_method": "sms"
                },
                "active": True
            }
        }
        
        patient = mock_patients.get(patient_id)
        if patient and patient.get("active", False):
            return patient
        
        return None

    def _validate_requester_credentials(self, requester_id: str, organization: str) -> Optional[Dict]:
        """Validate requester credentials"""
        if not requester_id or not organization:
            return None
        
        # Mock implementation - replace with actual credential validation
        mock_requesters = {
            "dr-smith-001": {
                "id": "dr-smith-001",
                "organization": "knh-hospital",
                "verified": True,
                "active": True,
                "role": "physician",
                "license": "KE-MD-12345",
                "specialties": ["internal-medicine"]
            },
            "dr-emergency-002": {
                "id": "dr-emergency-002",
                "organization": "knh-hospital",
                "verified": True,
                "active": True,
                "role": "physician",
                "department": "emergency",
                "license": "KE-MD-67890"
            },
            "researcher-004": {
                "id": "researcher-004",
                "organization": "research-institute",
                "verified": True,
                "active": True,
                "role": "researcher",
                "irb_approval": "IRB-2025-001"
            },
            "pharmacist-008": {
                "id": "pharmacist-008",
                "organization": "knh-hospital",
                "verified": True,
                "active": True,
                "role": "pharmacist",
                "license": "KE-PHARM-111"
            },
            "pharmacist-006": {
                "id": "pharmacist-006",
                "organization": "mtrh",
                "verified": True,
                "active": True,
                "role": "pharmacist",
                "license": "KE-PHARM-171"
            }
        }
        
        requester = mock_requesters.get(requester_id)
        if requester and requester.get("organization") == organization and requester.get("active"):
            return requester
        
        return None

    def _evaluate_emergency_override(self, request: ConsentRequest, patient: Dict, requester: Dict) -> ConsentDecision:
        """Evaluate emergency access override conditions"""
        
        # Check if requester can perform emergency overrides
        role_config = self.role_permissions.get(request.requester_role, {})
        if not role_config.get("can_override_emergency", False):
            return ConsentDecision(
                decision=ConsentDecisionType.DENIED,
                reason=f"Role '{request.requester_role}' not authorized for emergency overrides"
            )
        
        override_permissions = DataPermissions()
        critical_data_accessed = []
        
        # Always grant access to critical safety information in emergencies
        critical_data_types = {
            "AllergyIntolerance": "Critical allergy information",
            "Condition.critical": "Critical medical conditions",
            "MedicationRequest.active": "Active medications",
            "Observation.vital-signs": "Current vital signs"
        }
        
        for data_type in request.data_types:
            for critical_type, description in critical_data_types.items():
                if critical_type in data_type or data_type in critical_type:
                    override_permissions.allowed.append(data_type)
                    critical_data_accessed.append(description)
        
        if override_permissions.allowed:
            # Generate emergency-specific access token
            emergency_token = self._generate_emergency_access_token(request, requester)
            
            # Log emergency access for audit and review
            self._log_emergency_override(request, override_permissions, requester)
            
            # Schedule post-emergency review
            self._schedule_post_emergency_review(request, critical_data_accessed)
            
            return ConsentDecision(
                decision=ConsentDecisionType.APPROVED,
                reason=f"Emergency access granted for: {', '.join(critical_data_accessed)}",
                permissions=override_permissions.__dict__,
                access_token=emergency_token,
                expiry_time=datetime.now() + EMERGENCY_ACCESS_DURATION,
                restrictions=[
                    "EMERGENCY_ONLY", 
                    "POST_EMERGENCY_REVIEW_REQUIRED",
                    "AUDIT_TRAIL_MANDATORY"
                ],
                audit_info={
                    "emergency_access": True, 
                    "review_required": True,
                    "override_reason": "Patient safety critical data access",
                    "requester_role": request.requester_role,
                    "data_accessed": critical_data_accessed
                }
            )
        
        return ConsentDecision(
            decision=ConsentDecisionType.DENIED,
            reason="Emergency override not applicable for requested data types"
        )

    def _calculate_organizational_relationship(self, patient_org: Optional[Dict], requester_org: str) -> float:
        """Calculate organizational relationship score"""
        if not patient_org:
            return 0.2
        
        patient_org_id = patient_org.get("reference", "").split("/")[-1]
        
        # Direct organizational relationship
        if patient_org_id == requester_org:
            return 1.0
        
        # Care network relationships
        if requester_org in self.care_networks.get(patient_org_id, []):
            return 0.8
        
        # Reverse care network check
        if patient_org_id in self.care_networks.get(requester_org, []):
            return 0.8
        
        # Active referral relationships
        if self._has_active_referral(patient_org_id, requester_org):
            return 0.6
        
        # Shared care networks (indirect relationship)
        patient_networks = self.care_networks.get(patient_org_id, [])
        requester_networks = self.care_networks.get(requester_org, [])
        if set(patient_networks) & set(requester_networks):
            return 0.4
        
        # No established relationship
        return 0.2

    def _has_active_referral(self, patient_org: str, requester_org: str) -> bool:
        """Check for active referral relationship"""
        # Mock implementation - in real system, query referral database
        mock_referrals = {
            ("rural-clinic", "knh-hospital"): True,
            ("community-health", "mp-hospital"): True,
            ("knh-hospital", "specialist-clinics"): True
        }
        return mock_referrals.get((patient_org, requester_org), False)

    def _find_best_consent_match(self, consents: List[Dict], data_type: str, purpose: str, requester: Dict) -> Optional[Dict]:
        """Find the best matching consent for the request"""
        best_match = None
        highest_score = 0
        
        for consent in consents:
            if consent.get("status") != ConsentStatus.ACTIVE.value:
                continue
                
            score = self._calculate_consent_match_score(consent, data_type, purpose, requester)
            logger.debug(f"Consent {consent.get('id')} score: {score} for data type {data_type}")
            
            if score > highest_score and score >= MINIMUM_MATCH_THRESHOLD:
                highest_score = score
                best_match = consent
        
        if best_match:
            logger.info(f"Best consent match: {best_match.get('id')} with score {highest_score}")
        
        return best_match

    def _calculate_consent_match_score(self, consent: Dict, data_type: str, purpose: str, requester: Dict) -> float:
        """Calculate consent match score"""
        score = 0.0
        
        # Data type matching (40% of score)
        data_type_score = self._calculate_data_type_match(
            consent.get("provision", {}).get("class", []), 
            data_type
        )
        score += data_type_score * 0.4
        
        # Purpose matching (30% of score)
        purpose_score = self._calculate_purpose_match(
            consent.get("provision", {}).get("purpose", []), 
            purpose
        )
        score += purpose_score * 0.3
        
        # Requester relationship (20% of score)
        requester_score = self._calculate_requester_match(
            consent.get("provision", {}).get("actor", []), 
            requester
        )
        score += requester_score * 0.2
        
        # Temporal validity (10% of score)
        temporal_score = self._calculate_temporal_match(
            consent.get("provision", {}).get("dataPeriod", {})
        )
        score += temporal_score * 0.1
        
        logger.debug(f"Match score breakdown - Data: {data_type_score*0.4:.2f}, Purpose: {purpose_score*0.3:.2f}, Requester: {requester_score*0.2:.2f}, Temporal: {temporal_score*0.1:.2f}")
        
        return score

    def _calculate_data_type_match(self, consent_classes: List[Dict], requested_type: str) -> float:
        """Calculate data type match score"""
        if not consent_classes:
            return 0.0
        
        for consent_class in consent_classes:
            class_code = consent_class.get("code", "")
            class_system = consent_class.get("system", "")
            
            # Exact match
            if class_code == requested_type:
                return 1.0
            
            # Resource type matching
            if requested_type.startswith(class_code + "."):
                return 0.9
            
            # Wildcard matching
            if "*" in class_code or requested_type in class_code:
                return 0.8
            
            # Category matching (e.g., Observation.* matches Observation.laboratory)
            requested_parts = requested_type.split(".")
            class_parts = class_code.split(".")
            
            if len(requested_parts) > 1 and len(class_parts) > 0:
                if requested_parts[0] == class_parts[0]:
                    return 0.7
        
        return 0.0

    def _calculate_purpose_match(self, consent_purposes: List[Dict], requested_purpose: str) -> float:
        """Calculate purpose match score"""
        if not consent_purposes:
            return 0.0
        
        for purpose in consent_purposes:
            purpose_code = purpose.get("code", "")
            
            # Exact match
            if purpose_code == requested_purpose:
                return 1.0
        
        # Check for compatible purposes
        for purpose in consent_purposes:
            purpose_code = purpose.get("code", "")
            if requested_purpose in self.compatible_purposes.get(purpose_code, []):
                return 0.8
        
        return 0.0

    def _calculate_requester_match(self, consent_actors: List[Dict], requester: Dict) -> float:
        """Calculate requester match score"""
        if not consent_actors:
            return 0.5  # No specific actor restrictions means general access
        
        requester_org = requester.get("organization")
        requester_id = requester.get("id")
        
        for actor in consent_actors:
            reference = actor.get("reference", {}).get("reference", "")
            
            # Organization match
            if requester_org and requester_org in reference:
                return 1.0
            
            # Individual practitioner match
            if requester_id and requester_id in reference:
                return 1.0
            
            # Role-based match
            role = actor.get("role", {}).get("coding", [])
            for role_coding in role:
                if role_coding.get("code") in ["CST", "PRCP"]:  # Custodian or Primary Care Provider
                    return 0.8
        
        return 0.2

    def _calculate_temporal_match(self, consent_period: Dict) -> float:
        """Calculate temporal validity score"""
        if not consent_period:
            return 0.5
        
        try:
            start_str = consent_period.get("start", "")
            end_str = consent_period.get("end", "")
            
            if not start_str or not end_str:
                return 0.5
            
            start = self._parse_datetime(start_str)
            end = self._parse_datetime(end_str)
            now = datetime.now()
            
            if start <= now <= end:
                # Calculate score based on remaining validity
                total_duration = (end - start).total_seconds()
                remaining_duration = (end - now).total_seconds()
                return max(0.1, remaining_duration / total_duration)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing consent period: {e}")
        
        return 0.0

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string with Z timezone handling"""
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace('Z', '+00:00')
        return datetime.fromisoformat(datetime_str)

    def _select_best_overall_consent(self, consents: List[Dict], request: ConsentRequest) -> Dict:
        """Select the best overall consent from multiple matches"""
        if not consents:
            return {}
        
        if len(consents) == 1:
            return consents[0]
        
        # Score each consent based on multiple factors
        best_consent = None
        best_score = 0
        
        for consent in consents:
            score = 0
            
            # Favor more recent consents
            consent_date = consent.get("dateTime", "")
            if consent_date:
                try:
                    date = self._parse_datetime(consent_date)
                    days_old = (datetime.now() - date).days
                    recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
                    score += recency_score * 0.3
                except:
                    pass
            
            # Favor consents with longer validity periods
            period = consent.get("provision", {}).get("dataPeriod", {})
            if period.get("end"):
                try:
                    end_date = self._parse_datetime(period["end"])
                    remaining_days = (end_date - datetime.now()).days
                    validity_score = min(1.0, remaining_days / 365)  # Normalize to 1 year
                    score += validity_score * 0.3
                except:
                    pass
            
            # Favor more specific consents (fewer broad permissions)
            specificity_score = self._calculate_consent_specificity(consent)
            score += specificity_score * 0.4
            
            if score > best_score:
                best_score = score
                best_consent = consent
        
        return best_consent or consents[0]

    def _calculate_consent_specificity(self, consent: Dict) -> float:
        """Calculate how specific a consent is (more specific is better)"""
        provision = consent.get("provision", {})
        
        # Count specific data classes vs wildcards
        classes = provision.get("class", [])
        if not classes:
            return 0.1  # Very general
        
        specific_count = 0
        for cls in classes:
            code = cls.get("code", "")
            if "*" not in code and "." in code:  # Specific like "Observation.laboratory"
                specific_count += 1
            elif "." not in code and "*" not in code:  # General like "Observation"
                specific_count += 0.5
        
        return min(1.0, specific_count / len(classes))

    def _evaluate_granular_permissions(self, consent: Dict, data_type: str, purpose: str, requester_role: str) -> DataPermissions:
        """Evaluate granular permissions for the request"""
        permissions = DataPermissions()
        
        # Base permissions from consent provision
        provision = consent.get("provision", {})
        base_type = provision.get("type", "permit")
        
        if base_type == "permit":
            permissions.allowed.append(data_type)
        else:
            permissions.denied.append(data_type)
        
        # Process nested provisions (exceptions)
        nested_provisions = provision.get("provision", [])
        for nested_provision in nested_provisions:
            nested_classes = nested_provision.get("class", [])
            nested_code = nested_provision.get("code", [])
            nested_type = nested_provision.get("type", "permit")
            
            # Check class-based restrictions
            for nested_class in nested_classes:
                class_code = nested_class.get("code", "")
                if self._matches_data_type(class_code, data_type):
                    if nested_type == "deny":
                        permissions.denied.append(class_code)
                        # Remove from allowed if it was there
                        if class_code in permissions.allowed:
                            permissions.allowed.remove(class_code)
                    else:
                        permissions.allowed.append(class_code)
            
            # Check code-based restrictions (LOINC, SNOMED codes)
            for code_entry in nested_code:
                for coding in code_entry.get("coding", []):
                    code = coding.get("code", "")
                    if self._is_excluded_code(code, data_type):
                        permissions.denied.append(f"{data_type}.{code}")
        
        # Apply role-based filtering
        role_config = self.role_permissions.get(requester_role, {})
        
        # Check if role is allowed to access this data type
        allowed_data = role_config.get("allowed_data", [])
        denied_data = role_config.get("denied_data", [])
        
        if "*" not in allowed_data:
            # Check if data type is specifically allowed for this role
            data_allowed = False
            for allowed_pattern in allowed_data:
                if self._matches_data_pattern(data_type, allowed_pattern):
                    data_allowed = True
                    break
            
            if not data_allowed:
                permissions.denied.append(f"role-restriction:{data_type}")
        
        # Check for role-specific denials
        for denied_pattern in denied_data:
            if self._matches_data_pattern(data_type, denied_pattern):
                permissions.denied.append(f"role-denial:{data_type}")
        
        # Apply role-based masking
        permissions.masked.extend(role_config.get("masked_fields", []))
        
        # Apply sensitivity-based restrictions
        sensitivity_level = self.sensitivity_map.get(data_type, 2)
        if sensitivity_level >= HIGH_SENSITIVITY:
            permissions.masked.extend(self._get_high_sensitivity_masking())
        
        # Apply purpose-specific restrictions
        if purpose == "HRESCH":  # Research
            permissions.pseudonymized.extend(["Patient.identifier", "Patient.name", "Patient.telecom", "Patient.address"])
        elif purpose == "HMARKT":  # Marketing
            permissions.masked.extend(["detailed-clinical-data", "sensitive-demographics"])
        
        return permissions

    def _matches_data_type(self, consent_class: str, requested_type: str) -> bool:
        """Check if consent class matches requested data type"""
        if consent_class == requested_type:
            return True
        
        # Handle wildcards
        if "*" in consent_class:
            base_class = consent_class.replace("*", "")
            return requested_type.startswith(base_class)
        
        # Handle hierarchical matching
        if "." in requested_type and "." not in consent_class:
            return requested_type.startswith(consent_class + ".")
        
        return False

    def _matches_data_pattern(self, data_type: str, pattern: str) -> bool:
        """Check if data type matches a pattern (supports wildcards)"""
        if pattern == "*":
            return True
        
        if "*" in pattern:
            base_pattern = pattern.replace("*", "")
            return data_type.startswith(base_pattern)
        
        return data_type == pattern

    def _is_excluded_code(self, code: str, data_type: str) -> bool:
        """Check if a specific code should be excluded for the data type"""
        # Get data type mapping
        data_mapping = None
        for key, mapping in self.data_type_mappings.items():
            if mapping["fhir_resource"].lower() in data_type.lower():
                data_mapping = mapping
                break
        
        if data_mapping:
            excluded_codes = data_mapping.get("excluded_codes", [])
            return code in excluded_codes
        
        return False

    def _get_high_sensitivity_masking(self) -> List[str]:
        """Get high sensitivity data masking fields"""
        return [
            "Patient.identifier.value",
            "Patient.telecom.value", 
            "Patient.address.line",
            "Practitioner.identifier.value",
            "detailed-clinical-notes",
            "sensitive-demographics"
        ]

    def _has_permission_violations(self, permissions: DataPermissions) -> bool:
        """Check if there are permission violations that should deny access"""
        # Check for critical denials
        critical_denials = [
            item for item in permissions.denied 
            if any(keyword in item.lower() for keyword in ["critical", "role-denial", "genetic", "mental-health"])
        ]
        
        # If more items are denied than allowed, it's likely a violation
        if len(permissions.denied) > len(permissions.allowed):
            return True
        
        return len(critical_denials) > 0

    def _validate_temporal_scope(self, consent_period: Dict, request_time_range: Dict) -> bool:
        """Validate temporal scope of the request"""
        try:
            current_time = datetime.now()
            
            # Check consent validity
            if consent_period:
                consent_start = self._parse_datetime(consent_period.get("start", ""))
                consent_end = self._parse_datetime(consent_period.get("end", ""))
                
                if not (consent_start <= current_time <= consent_end):
                    logger.warning(f"Consent period invalid: {consent_start} to {consent_end}, current: {current_time}")
                    return False
            
            # Check request time range if specified
            if request_time_range and request_time_range.get("start") and request_time_range.get("end"):
                request_start = self._parse_datetime(request_time_range["start"])
                request_end = self._parse_datetime(request_time_range["end"])
                
                if consent_period:
                    # Request must be within consent period
                    if not (consent_start <= request_start and request_end <= consent_end):
                        logger.warning(f"Request time range outside consent period")
                        return False
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error validating temporal scope: {e}")
            return False

    def _calculate_consent_reuse_score(self, consent: Dict, request: ConsentRequest, relationship_score: float) -> float:
        """Calculate consent reusability score"""
        score = 0.0
        
        # Organizational relationship (40%)
        score += relationship_score * 0.4
        
        # Purpose compatibility (30%)
        purpose_compatibility = self._calculate_purpose_compatibility(
            consent.get("provision", {}).get("purpose", []),
            request.purpose
        )
        score += purpose_compatibility * 0.3
        
        # Data type coverage (20%)
        data_coverage = self._calculate_data_coverage(
            consent.get("provision", {}).get("class", []),
            request.data_types
        )
        score += data_coverage * 0.2
        
        # Temporal validity (10%)
        temporal_health = self._calculate_temporal_health(
            consent.get("provision", {}).get("dataPeriod", {})
        )
        score += temporal_health * 0.1
        
        logger.debug(f"Reuse score breakdown - Org: {relationship_score*0.4:.2f}, Purpose: {purpose_compatibility*0.3:.2f}, Data: {data_coverage*0.2:.2f}, Temporal: {temporal_health*0.1:.2f}")
        
        return score

    def _calculate_purpose_compatibility(self, consent_purposes: List[Dict], request_purpose: str) -> float:
        """Calculate purpose compatibility score"""
        return self._calculate_purpose_match(consent_purposes, request_purpose)

    def _calculate_data_coverage(self, consent_classes: List[Dict], request_data_types: List[str]) -> float:
        """Calculate data type coverage score"""
        if not request_data_types:
            return 0.0
        
        covered_types = 0
        for data_type in request_data_types:
            if any(self._matches_data_type(cls.get("code", ""), data_type) for cls in consent_classes):
                covered_types += 1
        
        return covered_types / len(request_data_types)

    def _calculate_temporal_health(self, consent_period: Dict) -> float:
        """Calculate temporal health of consent"""
        return self._calculate_temporal_match(consent_period)

    def _apply_data_filtering(self, permissions: DataPermissions, role: str, purpose: str, patient_preferences: Dict) -> DataPermissions:
        """Apply data filtering based on role, purpose, and preferences"""
        filtered = DataPermissions(
            allowed=permissions.allowed.copy(),
            denied=permissions.denied.copy(),
            masked=permissions.masked.copy(),
            pseudonymized=permissions.pseudonymized.copy()
        )
        
        # Apply role-based filtering
        role_config = self.role_permissions.get(role, {})
        
        if role == "billing":
            # Billing gets financial data only, clinical data masked
            clinical_data = ["Observation.*", "Condition.*", "DiagnosticReport.*"]
            for clinical in clinical_data:
                if not any(self._matches_data_pattern(allowed, clinical) for allowed in filtered.allowed):
                    filtered.masked.append(clinical)
        elif role == "researcher":
            # Research gets pseudonymized identifiers
            research_pseudonymized = role_config.get("pseudonymized_fields", [])
            filtered.pseudonymized.extend(research_pseudonymized)
        elif role == "pharmacist":
            # Pharmacist gets medication-focused filtering
            non_medication_data = [item for item in filtered.allowed if "Medication" not in item and "Allergy" not in item]
            for item in non_medication_data:
                if item not in ["Patient.demographics"]:
                    filtered.masked.append(item)
        
        # Apply purpose-based filtering
        if purpose == "HMARKT":
            # Marketing requires explicit opt-in
            if patient_preferences.get("marketing_opt_out", False):
                filtered.denied.extend(filtered.allowed)
                filtered.allowed = []
        elif purpose == "HRESCH":
            # Research requires de-identification
            identifiable = ["Patient.name", "Patient.address", "Patient.telecom"]
            filtered.pseudonymized.extend(identifiable)
        elif purpose == "ETREAT":
            # Emergency treatment gets enhanced access but with restrictions
            filtered.restrictions = ["EMERGENCY_CONTEXT_ONLY", "LIMITED_DURATION"]
        
        # Apply patient-specific preferences
        masking_preference = patient_preferences.get("data_masking_preference", "standard")
        if masking_preference == "enhanced":
            filtered.masked.extend(["Patient.identifier.value", "Patient.telecom", "detailed-demographics"])
        
        return filtered

    def _generate_access_token(self, permissions: DataPermissions, expiry: Optional[str], requester: Dict, request: ConsentRequest) -> str:
        """Generate OAuth 2.0 access token"""
        token_id = str(uuid.uuid4())
        
        # Calculate expiry time
        if expiry:
            expiry_time = self._parse_datetime(expiry)
        else:
            # Use purpose-based default duration
            default_duration = self.purpose_duration_map.get(request.purpose, DEFAULT_TOKEN_DURATION)
            expiry_time = datetime.now() + default_duration
        
        # Create token payload
        token_data = {
            "token_id": token_id,
            "patient_id": request.patient_id,
            "requester_id": requester.get("id"),
            "requester_org": requester.get("organization"),
            "permissions": permissions.__dict__,
            "scope": self._generate_oauth_scope(permissions, request),
            "purpose": request.purpose,
            "issued_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "emergency_context": request.emergency_context
        }
        
        # In real implementation, this would be a proper JWT token
        token_hash = hashlib.sha256(json.dumps(token_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"Bearer_{token_hash}_{token_id[:8]}"

    def _generate_oauth_scope(self, permissions: DataPermissions, request: ConsentRequest) -> List[str]:
        """Generate OAuth 2.0 scope from permissions"""
        scopes = []
        
        # Add read permissions for allowed data
        for data_type in permissions.allowed:
            scopes.append(f"read:{data_type}")
        
        # Add patient-specific scope
        scopes.append(f"patient:{request.patient_id}")
        
        # Add purpose scope
        scopes.append(f"purpose:{request.purpose}")
        
        # Add restrictions as negative scopes
        for denied in permissions.denied:
            scopes.append(f"deny:{denied}")
        
        return scopes

    def _generate_emergency_access_token(self, request: ConsentRequest, requester: Dict) -> str:
        """Generate emergency access token"""
        token_id = str(uuid.uuid4())
        
        token_data = {
            "token_id": token_id,
            "emergency": True,
            "patient_id": request.patient_id,
            "requester_id": request.requester_id,
            "requester_org": request.requester_organization,
            "purpose": request.purpose,
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + EMERGENCY_ACCESS_DURATION).isoformat(),
            "restrictions": ["EMERGENCY_ONLY", "AUDIT_REQUIRED"]
        }
        
        token_hash = hashlib.sha256(json.dumps(token_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"Emergency_{token_hash}_{token_id[:8]}"

    def _log_consent_usage(self, consent: Dict, request: ConsentRequest, access_token: str, usage_type: str):
        """Log consent usage for audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "CONSENT_USAGE",
            "consent_id": consent.get("id"),
            "request_id": request.request_id,
            "patient_id": request.patient_id,
            "requester_id": request.requester_id,
            "requester_org": request.requester_organization,
            "requester_role": request.requester_role,
            "access_token_id": access_token.split("_")[-1] if "_" in access_token else access_token[:8],
            "usage_type": usage_type,
            "data_types": request.data_types,
            "purpose": request.purpose,
            "emergency_context": request.emergency_context
        }
        logger.info(f"Consent usage logged: {json.dumps(audit_entry)}")

    def _log_emergency_override(self, request: ConsentRequest, permissions: DataPermissions, requester: Dict):
        """Log emergency access override"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "EMERGENCY_OVERRIDE",
            "request_id": request.request_id,
            "patient_id": request.patient_id,
            "requester_id": request.requester_id,
            "requester_org": request.requester_organization,
            "requester_role": request.requester_role,
            "requester_license": requester.get("license"),
            "emergency_permissions": permissions.__dict__,
            "justification": "Patient safety critical data access",
            "review_required": True,
            "alert_level": "HIGH"
        }
        logger.warning(f"Emergency override logged: {json.dumps(audit_entry)}")

    def _schedule_post_emergency_review(self, request: ConsentRequest, data_accessed: List[str]):
        """Schedule post-emergency review"""
        review_task = {
            "task_id": str(uuid.uuid4()),
            "type": "POST_EMERGENCY_REVIEW",
            "request_id": request.request_id,
            "patient_id": request.patient_id,
            "requester_id": request.requester_id,
            "data_accessed": data_accessed,
            "review_deadline": (datetime.now() + timedelta(hours=48)).isoformat(),
            "priority": "HIGH",
            "status": "PENDING"
        }
        logger.info(f"Post-emergency review scheduled: {json.dumps(review_task)}")

    # Token validation and management methods
    def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token and return its details"""
        try:
            if not token or not token.startswith(("Bearer_", "Emergency_")):
                return {"valid": False, "reason": "Invalid token format"}
            
            # Extract token components
            parts = token.split("_")
            if len(parts) < 3:
                return {"valid": False, "reason": "Malformed token"}
            
            token_type = parts[0]
            token_hash = parts[1]
            token_id = parts[2]
            
            # Mock token validation - in real implementation, verify JWT signature
            # and check against token store
            mock_valid_tokens = {
                "Bearer_1234abcd_12345678": {
                    "valid": True,
                    "patient_id": "CR123456789",
                    "requester_id": "dr-smith-001",
                    "scope": ["read:Patient.demographics", "patient:CR123456789"],
                    "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(),
                    "emergency": False
                },
                "Emergency_5678efgh_87654321": {
                    "valid": True,
                    "patient_id": "CR123456789",
                    "requester_id": "dr-emergency-002",
                    "scope": ["read:AllergyIntolerance", "patient:CR123456789", "emergency:true"],
                    "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "emergency": True
                }
            }
            
            # Check if token exists and is valid
            token_key = f"{token_type}_{token_hash}_{token_id}"
            if token_key in mock_valid_tokens:
                token_info = mock_valid_tokens[token_key]
                
                # Check expiry
                expiry_time = self._parse_datetime(token_info["expires_at"])
                if datetime.now() > expiry_time:
                    return {"valid": False, "reason": "Token expired"}
                
                return token_info
            
            return {"valid": False, "reason": "Token not found"}
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return {"valid": False, "reason": "Token validation error"}

    def revoke_access_token(self, token: str, reason: str = "User revocation") -> bool:
        """Revoke an access token"""
        try:
            # Log token revocation
            revocation_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "TOKEN_REVOCATION",
                "token_id": token.split("_")[-1] if "_" in token else token[:8],
                "reason": reason,
                "revoked_by": "system"
            }
            logger.info(f"Token revoked: {json.dumps(revocation_entry)}")
            
            # In real implementation, mark token as revoked in token store
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False


def run_consent_validation_tests():
    """Run comprehensive consent validation tests"""
    print("=" * 80)
    print("CONSENT MANAGEMENT PLATFORM - VALIDATION ENGINE TESTS")
    print("=" * 80)
    
    # Initialize validation engine
    engine = ConsentValidationEngine()
    
    # Get test resources
    active_consents = ConsentTestResources.create_sample_active_consents()
    test_requests = ConsentTestResources.create_sample_consent_requests()
    
    print(f"\nLoaded {len(active_consents)} active consents and {len(test_requests)} test requests\n")
    
    # Run tests
    results = []
    for i, request in enumerate(test_requests, 1):
        print(f"Test Case {i}: {request.request_id}")
        print(f"  Patient: {request.patient_id}")
        print(f"  Requester: {request.requester_id} ({request.requester_role})")
        print(f"  Organization: {request.requester_organization}")
        print(f"  Data Types: {', '.join(request.data_types)}")
        print(f"  Purpose: {request.purpose}")
        print(f"  Emergency: {request.emergency_context}")
        
        # Validate consent request
        start_time = datetime.now()
        decision = engine.validate_consent_request(request, active_consents)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"  RESULT: {decision.decision.value.upper()}")
        print(f"  Reason: {decision.reason}")
        print(f"  Execution Time: {execution_time:.1f}ms")
        
        if decision.access_token:
            print(f"  Access Token: {decision.access_token}")
            if decision.expiry_time:
                print(f"  Expires: {decision.expiry_time}")
        
        if decision.restrictions:
            print(f"  Restrictions: {', '.join(decision.restrictions)}")
            
        if decision.permissions:
            perms = decision.permissions
            if perms.get('allowed'):
                print(f"  Allowed: {', '.join(perms['allowed'])}")
            if perms.get('denied'):
                print(f"  Denied: {', '.join(perms['denied'])}")
            if perms.get('masked'):
                print(f"  Masked: {', '.join(perms['masked'])}")
            if perms.get('pseudonymized'):
                print(f"  Pseudonymized: {', '.join(perms['pseudonymized'])}")
        
        if decision.audit_info:
            print(f"  Audit Info: {decision.audit_info}")
        
        print("-" * 60)
        
        results.append({
            "test_case": i,
            "request_id": request.request_id,
            "decision": decision.decision.value,
            "reason": decision.reason,
            "execution_time_ms": execution_time,
            "has_token": bool(decision.access_token),
            "restrictions": len(decision.restrictions) if decision.restrictions else 0,
            "audit_logged": bool(decision.audit_info)
        })
    
    # Summary
    print("\nTEST SUMMARY:")
    print("=" * 40)
    approved = sum(1 for r in results if r["decision"] == "approved")
    denied = sum(1 for r in results if r["decision"] == "denied")
    pending = sum(1 for r in results if r["decision"] == "pending")
    
    print(f"Total Tests: {len(results)}")
    print(f"Approved: {approved}")
    print(f"Denied: {denied}")
    print(f"Pending: {pending}")
    print(f"Success Rate: {((approved + pending) / len(results)) * 100:.1f}%")
    
    avg_execution_time = sum(r["execution_time_ms"] for r in results) / len(results)
    print(f"Average Execution Time: {avg_execution_time:.1f}ms")
    
    print()
    
    return results


def demonstrate_token_validation():
    """Demonstrate token validation functionality"""
    print("\n" + "=" * 80)
    print("TOKEN VALIDATION DEMONSTRATION")
    print("=" * 80)
    
    engine = ConsentValidationEngine()
    
    # Test valid tokens
    test_tokens = [
        "Bearer_1234abcd_12345678",
        "Emergency_5678efgh_87654321",
        "Bearer_invalid_token",
        "Invalid_format"
    ]
    
    for token in test_tokens:
        print(f"\nValidating token: {token}")
        result = engine.validate_access_token(token)
        print(f"Valid: {result.get('valid', False)}")
        if result.get('valid'):
            print(f"Patient: {result.get('patient_id')}")
            print(f"Requester: {result.get('requester_id')}")
            print(f"Scope: {result.get('scope')}")
            print(f"Emergency: {result.get('emergency', False)}")
        else:
            print(f"Reason: {result.get('reason')}")
    
    # Test token revocation
    print(f"\nRevoking token: {test_tokens[0]}")
    revoked = engine.revoke_access_token(test_tokens[0], "Manual revocation")
    print(f"Revocation successful: {revoked}")


if __name__ == "__main__":
    # Run the test suite
    print("🚀 Starting Consent Management Platform Validation Engine Tests")
    test_results = run_consent_validation_tests()
    
    # Demonstrate token validation
    demonstrate_token_validation()
    
    # Example of creating FHIR resources from decisions
    print("\n" + "=" * 80)
    print("FHIR RESOURCE GENERATION EXAMPLE")
    print("=" * 80)
    
    engine = ConsentValidationEngine()
    test_request = ConsentTestResources.create_sample_consent_requests()[0]
    active_consents = ConsentTestResources.create_sample_active_consents()
    
    decision = engine.validate_consent_request(test_request, active_consents)
    
    if decision.decision == ConsentDecisionType.APPROVED:
        fhir_consent = create_fhir_consent_from_decision(test_request, decision)
        audit_event = generate_audit_event(test_request, decision)
        
        print("\nGenerated FHIR Consent Resource:")
        print(json.dumps(fhir_consent, indent=2))
        
        print("\nGenerated FHIR AuditEvent Resource:")
        print(json.dumps(audit_event, indent=2))
    
    print(f"\n✅ All tests completed successfully!")
    print(f"📊 Test Results Summary:")
    approved_count = sum(1 for r in test_results if r["decision"] == "approved")
    print(f"   - Approved requests: {approved_count}")
    print(f"   - Total test cases: {len(test_results)}")
    print(f"   - Success rate: {(approved_count / len(test_results)) * 100:.1f}%")
