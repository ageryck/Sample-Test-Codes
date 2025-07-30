"""
Consent Validation Engine Package
FHIR R4B Compliant Consent Management System
"""

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

__version__ = "2.0.0"
__all__ = [
    'ConsentStatus',
    'ConsentDecisionType', 
    'SensitivityLevel',
    'ConsentRequest',
    'ConsentDecision',
    'DataPermissions',
    'ConsentValidationEngine',
    'ConsentTestResources',
    'get_data_sensitivity_level',
    'create_fhir_consent_from_decision',
    'generate_audit_event'
]