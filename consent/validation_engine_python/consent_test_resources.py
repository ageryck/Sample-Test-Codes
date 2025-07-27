from typing import List, Dict
from .consent_request import ConsentRequest

class ConsentTestResources:
    """Sample test resources for consent validation testing"""
    @staticmethod
    def create_sample_active_consents() -> List[Dict]:
        return [
            {
                "resourceType": "Consent",
                "id": "consent-001-demographics",
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
                    "reference": "Patient/CR123456789"
                },
                "dateTime": "2025-01-01T00:00:00Z",
                "performer": [{
                    "reference": "Patient/CR123456789"
                }],
                "provision": {
                    "type": "permit",
                    "dataPeriod": {
                        "start": "2025-01-01T00:00:00Z",
                        "end": "2026-01-01T00:00:00Z"
                    },
                    "class": [{
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Patient",
                        "display": "Patient Demographics"
                    }, {
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Observation.vital-signs",
                        "display": "Vital Signs"
                    }],
                    "purpose": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "ETREAT"
                    }],
                    "actor": [{
                        "role": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                                "code": "ER",
                                "display": "Emergency Room"
                            }]
                        }
                    }],
                    "securityLabel": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "EMRGONLY",
                        "display": "Emergency Only"
                    }]
                }
            },
            {
                "resourceType": "Consent",
                "id": "consent-004-mental-health",
                "status": "active",
                "scope": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                        "code": "patient-privacy"
                    }]
                },
                "patient": {
                    "reference": "Patient/CR123456789"
                },
                "dateTime": "2025-01-10T00:00:00Z",
                "provision": {
                    "type": "permit",
                    "dataPeriod": {
                        "start": "2025-01-10T00:00:00Z",
                        "end": "2025-04-10T00:00:00Z"
                    },
                    "class": [{
                        "system": "http://snomed.info/sct",
                        "code": "74732009",
                        "display": "Mental disorder"
                    }, {
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Condition.mental-health",
                        "display": "Mental Health Conditions"
                    }],
                    "purpose": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "TREAT"
                    }],
                    "actor": [{
                        "role": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "CST",
                                "display": "Custodian"
                            }]
                        },
                        "reference": {
                            "reference": "Organization/mental-health-certified"
                        }
                    }],
                    "securityLabel": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                        "code": "R",
                        "display": "Restricted"
                    }]
                }
            },
            {
                "resourceType": "Consent",
                "id": "consent-005-research",
                "status": "active",
                "scope": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                        "code": "research"
                    }]
                },
                "patient": {
                    "reference": "Patient/CR123456789"
                },
                "dateTime": "2025-01-20T00:00:00Z",
                "provision": {
                    "type": "permit",
                    "dataPeriod": {
                        "start": "2025-01-20T00:00:00Z",
                        "end": "2030-01-20T00:00:00Z"
                    },
                    "class": [{
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Observation",
                        "display": "Clinical Observations"
                    }, {
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Condition",
                        "display": "Clinical Conditions"
                    }, {
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Observation.laboratory",
                        "display": "Laboratory Results"
                    }],
                    "purpose": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "HRESCH"
                    }],
                    "actor": [{
                        "role": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "CST"
                            }]
                        },
                        "reference": {
                            "reference": "Organization/research-institute"
                        }
                    }],
                    "provision": [{
                        "type": "deny",
                        "class": [{
                            "system": "http://hl7.org/fhir/resource-types",
                            "code": "Patient.identifier",
                            "display": "Patient Identifiers"
                        }]
                    }]
                }
            },
            {
                "resourceType": "Consent",
                "id": "consent-006-medication",
                "status": "active",
                "scope": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                        "code": "patient-privacy"
                    }]
                },
                "patient": {
                    "reference": "Patient/CR123456789"
                },
                "dateTime": "2025-01-05T00:00:00Z",
                "provision": {
                    "type": "permit",
                    "dataPeriod": {
                        "start": "2025-01-05T00:00:00Z",
                        "end": "2025-12-31T00:00:00Z"
                    },
                    "class": [{
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "MedicationRequest",
                        "display": "Medication Prescriptions"
                    }, {
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "MedicationDispense",
                        "display": "Dispensed Medications"
                    }],
                    "purpose": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "TREAT"
                    }],
                    "actor": [{
                        "role": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "CST"
                            }]
                        },
                        "reference": {
                            "reference": "Organization/knh-hospital"
                        }
                    }]
                }
            }
        ]

    @staticmethod
    def create_sample_consent_requests() -> List[ConsentRequest]:
        return [
            ConsentRequest(
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
            ),
            ConsentRequest(
                request_id="req-002",
                patient_id="CR123456789",
                requester_id="dr-smith-001",
                requester_organization="knh-hospital",
                requester_role="physician",
                data_types=["Observation.laboratory"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-15T00:00:00Z",
                    "end": "2025-04-15T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-003",
                patient_id="CR123456789",
                requester_id="dr-emergency-002",
                requester_organization="knh-hospital",
                requester_role="physician",
                data_types=["AllergyIntolerance"],
                purpose="ETREAT",
                time_range={
                    "start": "2025-01-25T14:30:00Z",
                    "end": "2025-01-25T18:30:00Z"
                },
                emergency_context=True
            ),
            ConsentRequest(
                request_id="req-004",
                patient_id="CR123456789",
                requester_id="dr-geneticist-004",
                requester_organization="external-lab",
                requester_role="physician",
                data_types=["Observation.genetic"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-15T00:00:00Z",
                    "end": "2025-04-15T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-005",
                patient_id="CR123456789",
                requester_id="researcher-004",
                requester_organization="research-institute",
                requester_role="researcher",
                data_types=["Observation.laboratory", "Condition.diagnosis"],
                purpose="HRESCH",
                time_range={
                    "start": "2025-01-20T00:00:00Z",
                    "end": "2030-01-20T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-006",
                patient_id="CR123456789",
                requester_id="billing-admin-006",
                requester_organization="knh-hospital",
                requester_role="billing",
                data_types=["Patient.demographics", "Encounter.financial"],
                purpose="HPAYMT",
                time_range={
                    "start": "2025-01-01T00:00:00Z",
                    "end": "2025-06-30T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-007",
                patient_id="CR123456789",
                requester_id="psychiatrist-007",
                requester_organization="mental-health-certified",
                requester_role="physician",
                data_types=["Condition.mental-health"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-10T00:00:00Z",
                    "end": "2025-04-10T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-008",
                patient_id="CR123456789",
                requester_id="dr-late-008",
                requester_organization="knh-hospital",
                requester_role="physician",
                data_types=["Observation.laboratory"],
                purpose="TREAT",
                time_range={
                    "start": "2025-05-01T00:00:00Z",
                    "end": "2025-05-31T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-009",
                patient_id="CR123456789",
                requester_id="pharmacist-008",
                requester_organization="knh-hospital",
                requester_role="pharmacist",
                data_types=["MedicationRequest", "AllergyIntolerance"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-01T00:00:00Z",
                    "end": "2025-12-31T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-010",
                patient_id="INVALID-ID",
                requester_id="dr-test-010",
                requester_organization="knh-hospital",
                requester_role="physician",
                data_types=["Patient.demographics"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-01T00:00:00Z",
                    "end": "2025-12-31T00:00:00Z"
                }
            )
        ] 