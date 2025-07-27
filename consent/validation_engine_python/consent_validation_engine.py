import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .consent_status import ConsentStatus
from .consent_decision_type import ConsentDecisionType
from .sensitivity_level import SensitivityLevel
from .consent_request import ConsentRequest
from .consent_decision import ConsentDecision
from .data_permissions import DataPermissions
import logging
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MINIMUM_MATCH_THRESHOLD = 0.7
REUSE_THRESHOLD = 0.8
HIGH_SENSITIVITY = 3
EMERGENCY_ACCESS_DURATION = timedelta(hours=24)
DEFAULT_TOKEN_DURATION = timedelta(hours=24)

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

    def _initialize_data_type_mappings(self) -> Dict[str, str]:
        """Initialize data type to FHIR resource type mappings"""
        return {
            "Patient.demographics": "Patient",
            "Observation.vital-signs": "Observation",
            "Observation.laboratory": "Observation",
            "DiagnosticReport.imaging": "DiagnosticReport",
            "Condition.diagnosis": "Condition",
            "Condition.mental-health": "Condition",
            "MedicationRequest.controlled": "MedicationRequest",
            "AllergyIntolerance": "AllergyIntolerance",
            "Observation.genetic": "Observation",
            "MedicationDispense": "MedicationDispense",
            "MedicationRequest": "MedicationRequest",
            "Encounter.financial": "Encounter",
            "Coverage": "Coverage"
        }

    def _initialize_care_networks(self) -> Dict[str, List[str]]:
        """Initialize care networks (example list)"""
        return {
            "Network A": ["Provider 1", "Provider 2"],
            "Network B": ["Provider 3", "Provider 4"],
            "Network C": ["Provider 5"]
        }

    def _initialize_compatible_purposes(self) -> Dict[str, List[str]]:
        """Initialize compatible purposes for data sharing"""
        return {
            "TREAT": ["ETREAT", "HPAYMT", "HOPERAT", "HRESCH", "PUBHLTH", "HMARKT", "HDIRECT"],
            "ETREAT": ["TREAT", "HPAYMT", "HOPERAT", "HRESCH", "PUBHLTH", "HMARKT", "HDIRECT"],
            "HPAYMT": ["TREAT", "ETREAT", "HOPERAT", "HRESCH", "PUBHLTH", "HMARKT", "HDIRECT"],
            "HOPERAT": ["TREAT", "ETREAT", "HPAYMT", "HRESCH", "PUBHLTH", "HMARKT", "HDIRECT"],
            "HRESCH": ["TREAT", "ETREAT", "HPAYMT", "HOPERAT", "PUBHLTH", "HMARKT", "HDIRECT"],
            "PUBHLTH": ["TREAT", "ETREAT", "HPAYMT", "HOPERAT", "HRESCH", "HMARKT", "HDIRECT"],
            "HMARKT": ["TREAT", "ETREAT", "HPAYMT", "HOPERAT", "HRESCH", "PUBHLTH", "HDIRECT"],
            "HDIRECT": ["TREAT", "ETREAT", "HPAYMT", "HOPERAT", "HRESCH", "PUBHLTH", "HMARKT"]
        }

    def _initialize_purpose_duration(self, purpose_code: str) -> timedelta:
        """Get the duration for a specific purpose code"""
        return self.purpose_duration_map.get(purpose_code, DEFAULT_TOKEN_DURATION)

    def _get_resource_type(self, data_type: str) -> str:
        """Get the FHIR resource type for a given data type"""
        return self.data_type_mappings.get(data_type)

    def _get_sensitivity_level(self, data_type: str) -> int:
        """Get the sensitivity level for a given data type"""
        return self.sensitivity_map.get(data_type, SensitivityLevel.LOW.value)

    def _is_emergency_access(self, consent: Dict) -> bool:
        """Check if a consent is for emergency access"""
        return consent.get("emergency_access", False)

    def _is_purpose_valid(self, consent: Dict, purpose_code: str) -> bool:
        """Check if a consent's purpose is valid for a given purpose code"""
        return purpose_code in self.compatible_purposes.get(consent.get("purpose_code"), [])

    def _is_duration_valid(self, consent: Dict, purpose_code: str) -> bool:
        """Check if a consent's duration is valid for a given purpose code"""
        consent_duration = consent.get("duration", DEFAULT_TOKEN_DURATION)
        purpose_duration = self._initialize_purpose_duration(purpose_code)
        return consent_duration >= purpose_duration

    def _is_data_type_allowed(self, consent: Dict, data_type: str) -> bool:
        """Check if a consent allows a specific data type"""
        resource_type = self._get_resource_type(data_type)
        if not resource_type:
            return False

        # Check if the resource type is explicitly allowed
        if resource_type in consent.get("allowed_resources", []):
            return True

        # Check if the resource type is explicitly denied
        if resource_type in consent.get("denied_resources", []):
            return False

        # If not explicitly allowed or denied, check if the data type is allowed
        # This is a simplified check; a more robust solution would involve
        # a more complex permission model.
        return True # Assuming all data types are allowed unless explicitly denied

    def _is_data_type_sensitive(self, data_type: str) -> bool:
        """Check if a data type is sensitive"""
        return self._get_sensitivity_level(data_type) >= HIGH_SENSITIVITY

    def _is_data_type_masked(self, consent: Dict, data_type: str) -> bool:
        """Check if a data type is masked in a consent"""
        resource_type = self._get_resource_type(data_type)
        if not resource_type:
            return False

        # Check if the resource type is explicitly masked
        if resource_type in consent.get("masked_resources", []):
            return True

        # Check if the resource type is explicitly denied
        if resource_type in consent.get("denied_resources", []):
            return False

        # If not explicitly masked or denied, check if the data type is masked
        # This is a simplified check; a more robust solution would involve
        # a more complex permission model.
        return False # Assuming all data types are not masked unless explicitly masked

    def _is_pseudonymized(self, consent: Dict, data_type: str) -> bool:
        """Check if a data type is pseudonymized in a consent"""
        resource_type = self._get_resource_type(data_type)
        if not resource_type:
            return False

        # Check if the resource type is explicitly pseudonymized
        if resource_type in consent.get("pseudonymized_resources", []):
            return True

        # Check if the resource type is explicitly denied
        if resource_type in consent.get("denied_resources", []):
            return False

        # If not explicitly pseudonymized or denied, check if the data type is pseudonymized
        # This is a simplified check; a more robust solution would involve
        # a more complex permission model.
        return False # Assuming all data types are not pseudonymized unless explicitly pseudonymized

    def _is_emergency_override_allowed(self, consent: Dict, data_type: str) -> bool:
        """Check if emergency access override is allowed for a specific data type"""
        resource_type = self._get_resource_type(data_type)
        if not resource_type:
            return False

        # Check if the resource type is explicitly allowed for emergency override
        if resource_type in consent.get("emergency_override_allowed_resources", []):
            return True

        # Check if the resource type is explicitly denied
        if resource_type in consent.get("denied_resources", []):
            return False

        # If not explicitly allowed or denied, check if the data type is allowed for emergency override
        # This is a simplified check; a more robust solution would involve
        # a more complex permission model.
        return False # Assuming all data types are not allowed for emergency override unless explicitly allowed

