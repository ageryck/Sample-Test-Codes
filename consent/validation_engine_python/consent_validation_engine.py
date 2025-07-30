import json
import uuid
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from consent_status import ConsentStatus
from consent_decision_type import ConsentDecisionType
from sensitivity_level import SensitivityLevel
from consent_request import ConsentRequest
from consent_decision import ConsentDecision
from data_permissions import DataPermissions
from utils import parse_datetime_safe, get_current_utc, validate_patient_id_format

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MINIMUM_MATCH_THRESHOLD = 0.7
REUSE_THRESHOLD = 0.8
HIGH_SENSITIVITY = 3
EMERGENCY_ACCESS_DURATION = timedelta(hours=24)
DEFAULT_TOKEN_DURATION = timedelta(hours=24)


class ConsentValidationEngine:
    """Main consent validation engine with fixed datetime handling"""

    def __init__(self):
        self.sensitivity_map = self._initialize_sensitivity_map()
        self.purpose_duration_map = self._initialize_purpose_durations()
        self.role_permissions = self._initialize_role_permissions()
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

    def _initialize_role_permissions(self) -> Dict[str, Dict[str, Any]]:
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
            "researcher": {
                "allowed_data": ["*"],
                "denied_data": [],
                "masked_fields": [],
                "pseudonymized_fields": ["Patient.identifier", "Patient.name", "Patient.telecom", "Patient.address"],
                "can_override_emergency": False
            },
            "pharmacist": {
                "allowed_data": ["MedicationRequest", "MedicationDispense", "AllergyIntolerance",
                                 "Patient.demographics"],
                "denied_data": ["DiagnosticReport.*", "Observation.laboratory"],
                "masked_fields": ["Patient.address", "Patient.telecom"],
                "can_override_emergency": False
            }
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
        """Main consent validation entry point with proper error handling"""
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

            # Step 4: Find matching consent
            matching_consent = self._find_best_consent_match(active_consents, request.data_types[0], request.purpose,
                                                             requester)
            if not matching_consent:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason="No valid consent found for requested data types",
                    audit_info={"step": "consent_matching", "request_id": request.request_id}
                )

            # Step 5: Temporal Validation (FIXED - no more datetime comparison errors)
            temporal_valid = self._validate_temporal_scope(
                matching_consent.get("provision", {}).get("dataPeriod", {}),
                request.time_range
            )

            if not temporal_valid:
                return ConsentDecision(
                    decision=ConsentDecisionType.DENIED,
                    reason="Request falls outside consent temporal scope",
                    audit_info={"step": "temporal_validation"}
                )

            # Step 6: Generate permissions and token
            permissions = self._evaluate_granular_permissions(matching_consent, request.data_types[0], request.purpose,
                                                              request.requester_role)
            access_token = self._generate_access_token(permissions,
                                                       matching_consent.get("provision", {}).get("dataPeriod", {}).get(
                                                           "end"), requester, request)

            return ConsentDecision(
                decision=ConsentDecisionType.APPROVED,
                reason="Consent validation successful",
                permissions=permissions.__dict__,
                access_token=access_token,
                expiry_time=parse_datetime_safe(
                    matching_consent.get("provision", {}).get("dataPeriod", {}).get("end", "")),
                audit_info={
                    "consent_id": matching_consent.get("id"),
                    "step": "validation_complete"
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
        """Validate input parameters with improved checks"""
        if not request.patient_id or len(request.patient_id.strip()) == 0:
            return "Patient ID is required"

        if not validate_patient_id_format(request.patient_id):
            logger.warning(f"Patient ID {request.patient_id} does not match expected format")

        if not request.requester_id or len(request.requester_id.strip()) == 0:
            return "Requester ID is required"

        if not request.data_types or len(request.data_types) == 0:
            return "At least one data type must be specified"

        if not request.purpose or request.purpose not in self.purpose_duration_map:
            return f"Invalid purpose code: {request.purpose}"

        # Validate time range format (fixed datetime parsing)
        try:
            if request.time_range:
                start = request.time_range.get("start")
                end = request.time_range.get("end")
                if start:
                    parse_datetime_safe(start)
                if end:
                    parse_datetime_safe(end)
        except Exception as e:
            return f"Invalid date format in time range: {str(e)}"

        return None

    def _validate_patient_identity(self, patient_id: str) -> Optional[Dict]:
        """Validate patient identity and return patient data"""
        if not patient_id or len(patient_id) < 5:
            return None

        # Mock implementation - replace with actual patient registry lookup
        mock_patients = {
            "CR123456789": {
                "id": "CR123456789",
                "identifier": [{"value": "CR123456789", "system": "national-health-id"}],
                "name": [{"given": ["Mukami"], "family": "Cynthia"}],
                "managingOrganization": {"reference": "Organization/moh-kenya"},
                "preferences": {"marketing_opt_out": True},
                "active": True
            },
            "CR123456790": {
                "id": "CR123456790",
                "identifier": [{"value": "CR123456790", "system": "national-health-id"}],
                "name": [{"given": ["Ngecha"], "family": "Tyrus"}],
                "managingOrganization": {"reference": "Organization/moh-kenya"},
                "preferences": {"marketing_opt_out": True},
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
                "license": "KE-MD-12345"
            },
            "researcher-001": {
                "id": "researcher-001",
                "organization": "research-institute",
                "verified": True,
                "active": True,
                "role": "researcher",
                "irb_approval": "IRB-2025-001"
            },
            "pharmacist-006": {
                "id": "pharmacist-006",
                "organization": "mtrh",
                "verified": True,
                "active": True,
                "role": "pharmacist",
                "irb_approval": "KE-PHARM-171"
            }
        }

        requester = mock_requesters.get(requester_id)
        if requester and requester.get("organization") == organization and requester.get("active"):
            return requester

        return None

    def _find_best_consent_match(self, consents: List[Dict], data_type: str, purpose: str, requester: Dict) -> Optional[
        Dict]:
        """Find the best matching consent for the request"""
        best_match = None
        highest_score = 0

        for consent in consents:
            if consent.get("status") != ConsentStatus.ACTIVE.value:
                continue

            score = self._calculate_consent_match_score(consent, data_type, purpose, requester)

            if score > highest_score and score >= MINIMUM_MATCH_THRESHOLD:
                highest_score = score
                best_match = consent

        return best_match

    def _calculate_consent_match_score(self, consent: Dict, data_type: str, purpose: str, requester: Dict) -> float:
        """Calculate consent match score"""
        score = 0.0

        # Data type matching (50% of score)
        data_type_score = self._calculate_data_type_match(
            consent.get("provision", {}).get("class", []),
            data_type
        )
        score += data_type_score * 0.5

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

        return score

    def _calculate_data_type_match(self, consent_classes: List[Dict], requested_type: str) -> float:
        """Calculate data type match score"""
        if not consent_classes:
            return 0.0

        for consent_class in consent_classes:
            class_code = consent_class.get("code", "")

            # Exact match
            if class_code == requested_type:
                return 1.0

            # Resource type matching
            if requested_type.startswith(class_code + "."):
                return 0.9

            # Category matching (e.g., Patient matches Patient.demographics)
            requested_parts = requested_type.split(".")
            if len(requested_parts) > 0 and requested_parts[0] == class_code:
                return 0.8

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

        for actor in consent_actors:
            reference = actor.get("reference", {}).get("reference", "")

            # Organization match
            if requester_org and requester_org in reference:
                return 1.0

        return 0.2

    def _validate_temporal_scope(self, consent_period: Dict, request_time_range: Dict) -> bool:
        """
        Validate temporal scope of the request.
        FIXED: Proper timezone-aware datetime comparison to avoid offset-naive vs offset-aware errors.
        """
        try:
            current_time = get_current_utc()  # Always timezone-aware

            # Check consent validity
            if consent_period:
                consent_start_str = consent_period.get("start", "")
                consent_end_str = consent_period.get("end", "")

                if consent_start_str and consent_end_str:
                    # Use our safe datetime parser that handles timezones properly
                    consent_start = parse_datetime_safe(consent_start_str)
                    consent_end = parse_datetime_safe(consent_end_str)

                    # Now all datetime objects are timezone-aware, safe to compare
                    if not (consent_start <= current_time <= consent_end):
                        logger.warning(
                            f"Consent period invalid: {consent_start} to {consent_end}, current: {current_time}")
                        return False

            # Check request time range if specified
            if request_time_range and request_time_range.get("start") and request_time_range.get("end"):
                request_start = parse_datetime_safe(request_time_range["start"])
                request_end = parse_datetime_safe(request_time_range["end"])

                # Validate request time range is reasonable
                if request_start >= request_end:
                    logger.warning("Request start time is after end time")
                    return False

                # Check if request is within consent period (if consent period exists)
                if consent_period and consent_period.get("start") and consent_period.get("end"):
                    consent_start = parse_datetime_safe(consent_period["start"])
                    consent_end = parse_datetime_safe(consent_period["end"])

                    # Request must be within consent period
                    if not (consent_start <= request_start and request_end <= consent_end):
                        logger.warning("Request time range outside consent period")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating temporal scope: {e}")
            return False

    def _evaluate_granular_permissions(self, consent: Dict, data_type: str, purpose: str,
                                       requester_role: str) -> DataPermissions:
        """Evaluate granular permissions for the request"""
        permissions = DataPermissions()

        # Base permissions from consent provision
        provision = consent.get("provision", {})
        base_type = provision.get("type", "permit")

        if base_type == "permit":
            permissions.allowed.append(data_type)
        else:
            permissions.denied.append(data_type)

        # Apply role-based filtering
        role_config = self.role_permissions.get(requester_role, {})

        # Apply purpose-specific restrictions
        if purpose == "HRESCH":  # Research
            permissions.pseudonymized.extend(["Patient.identifier", "Patient.name"])
        elif purpose == "HMARKT":  # Marketing
            permissions.masked.extend(["detailed-clinical-data", "sensitive-demographics"])

        # Apply role-specific masking
        if requester_role == "researcher":
            research_fields = role_config.get("pseudonymized_fields", [])
            permissions.pseudonymized.extend(research_fields)

        return permissions

    def _generate_access_token(self, permissions: DataPermissions, expiry: Optional[str], requester: Dict,
                               request: ConsentRequest) -> str:
        """Generate OAuth 2.0 access token"""
        token_id = str(uuid.uuid4())

        # Calculate expiry time using safe datetime parsing
        if expiry:
            expiry_time = parse_datetime_safe(expiry)
        else:
            default_duration = self.purpose_duration_map.get(request.purpose, DEFAULT_TOKEN_DURATION)
            expiry_time = get_current_utc() + default_duration

        # Create token payload
        token_data = {
            "token_id": token_id,
            "patient_id": request.patient_id,
            "requester_id": requester.get("id"),
            "issued_at": get_current_utc().isoformat(),
            "expires_at": expiry_time.isoformat()
        }

        # In real implementation, this would be a proper JWT token
        token_hash = hashlib.sha256(json.dumps(token_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"Bearer_{token_hash}_{token_id[:8]}"