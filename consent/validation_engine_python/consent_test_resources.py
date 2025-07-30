from typing import List, Dict
from consent_request import ConsentRequest


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
                "patient": {
                    "reference": "Patient/CR123456789"
                },
                "dateTime": "2025-01-01T00:00:00Z",
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
                    }],
                    "purpose": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "TREAT"
                    }],
                    "actor": [{
                        "role": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                                "code": "CST",
                                "display": "Custodian"
                            }]
                        },
                        "reference": {
                            "reference": "Organization/knh-hospital"
                        }
                    }]
                }
            },
            {
                "resourceType": "Consent",
                "id": "consent-002-research",
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
                    }]
                }
            },
            {
                "resourceType": "Consent",
                "id": "consent-003-pharma",
                "status": "active",
                "scope": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                        "code": "treatment"
                    }]
                },
                "patient": {
                    "reference": "Patient/CR123456790"
                },
                "dateTime": "2025-01-19T00:00:00Z",
                "provision": {
                    "type": "permit",
                    "dataPeriod": {
                        "start": "2025-01-19T00:00:00Z",
                        "end": "2026-01-21T00:00:00Z"
                    },
                    "class": [{
                        "system": "http://hl7.org/fhir/resource-types",
                        "code": "Observation",
                        "display": "Clinical Observations"
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
                            "reference": "Organization/mtrh"
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
                requester_id="researcher-001",
                requester_organization="research-institute",
                requester_role="researcher",
                data_types=["Observation.laboratory"],
                purpose="HRESCH",
                time_range={
                    "start": "2025-01-20T00:00:00Z",
                    "end": "2030-01-20T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-006",
                patient_id="CR123456790",
                requester_id="pharmacist-006",
                requester_organization="mtrh",
                requester_role="pharmacist",
                data_types=["MedicationDispense"], 
                purpose="TREAT",
                time_range={
                    "start": "2025-07-20T00:00:00Z",
                    "end": "2025-12-20T00:00:00Z"
                }
            ),
            ConsentRequest(
                request_id="req-004",
                patient_id="CR12-dgd434",
                requester_id="dr-test-004",
                requester_organization="test-org",
                requester_role="physician",
                data_types=["Patient.demographics"],
                purpose="TREAT",
                time_range={
                    "start": "2025-01-01T00:00:00Z",
                    "end": "2025-12-31T00:00:00Z"
                }
            )
        ]