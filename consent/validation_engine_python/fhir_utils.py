from typing import Dict
from datetime import datetime
from consent_request import ConsentRequest
from consent_decision import ConsentDecision
from consent_decision_type import ConsentDecisionType
from utils import get_current_utc


def create_fhir_consent_from_decision(request: ConsentRequest, decision: ConsentDecision) -> Dict:
    """Create a FHIR Consent resource from validation decision"""
    if decision.decision != ConsentDecisionType.APPROVED:
        return {}

    current_time = get_current_utc()
    consent_id = f"consent-{request.request_id}-{current_time.strftime('%Y%m%d%H%M%S')}"

    consent = {
        "resourceType": "Consent",
        "id": consent_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": current_time.isoformat()
        },
        "status": "active",
        "scope": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                "code": "patient-privacy"
            }]
        },
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/consentcategorycodes",
                "code": "idscl"
            }]
        }],
        "patient": {
            "reference": f"Patient/{request.patient_id}"
        },
        "dateTime": current_time.isoformat(),
        "performer": [{
            "reference": f"Patient/{request.patient_id}"
        }],
        "provision": {
            "type": "permit",
            "dataPeriod": {
                "start": request.time_range.get("start"),
                "end": request.time_range.get("end")
            },
            "purpose": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                "code": request.purpose
            }],
            "actor": [{
                "role": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "CST"
                    }]
                },
                "reference": {
                    "reference": f"Organization/{request.requester_organization}"
                }
            }]
        }
    }

    # Add data classes
    if decision.permissions and decision.permissions.get("allowed"):
        consent["provision"]["class"] = []
        for data_type in decision.permissions["allowed"]:
            consent["provision"]["class"].append({
                "system": "http://hl7.org/fhir/resource-types",
                "code": data_type.split(".")[0] if "." in data_type else data_type,
                "display": data_type
            })

    # Add restrictions if any
    if decision.restrictions:
        consent["provision"]["securityLabel"] = []
        for restriction in decision.restrictions:
            consent["provision"]["securityLabel"].append({
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": restriction.replace("_", ""),
                "display": restriction.replace("_", " ").title()
            })

    return consent


def generate_audit_event(request: ConsentRequest, decision: ConsentDecision) -> Dict:
    """Generate FHIR AuditEvent for consent decision"""
    outcome_code = "0" if decision.decision == ConsentDecisionType.APPROVED else "4"
    action_code = "C" if decision.decision == ConsentDecisionType.APPROVED else "R"
    current_time = get_current_utc()

    return {
        "resourceType": "AuditEvent",
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": "110110",
            "display": "Patient Record"
        },
        "subtype": [{
            "system": "http://terminology.hl7.org/CodeSystem/iso-21089-lifecycle",
            "code": "access",
            "display": "Access/View Record Lifecycle Event"
        }],
        "action": action_code,
        "recorded": current_time.isoformat(),
        "outcome": outcome_code,
        "outcomeDesc": decision.reason,
        "agent": [{
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/extra-security-role-type",
                    "code": "humanuser",
                    "display": "Human User"
                }]
            },
            "who": {
                "reference": f"Practitioner/{request.requester_id}"
            },
            "requestor": True,
            "role": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": request.requester_role.upper(),
                    "display": request.requester_role.title()
                }]
            }],
            "network": {
                "address": request.requester_organization,
                "type": "5"
            }
        }],
        "source": {
            "site": "Consent Management Platform",
            "observer": {
                "reference": "Device/cmp-validation-engine"
            },
            "type": [{
                "system": "http://terminology.hl7.org/CodeSystem/security-source-type",
                "code": "4",
                "display": "Application Server"
            }]
        },
        "entity": [{
            "what": {
                "reference": f"Patient/{request.patient_id}"
            },
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                "code": "1",
                "display": "Person"
            },
            "role": {
                "system": "http://terminology.hl7.org/CodeSystem/object-role",
                "code": "1",
                "display": "Patient"
            }
        }],
        "purposeOfEvent": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                "code": request.purpose,
                "display": request.purpose
            }]
        }]
    }
