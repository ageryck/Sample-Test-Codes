import json
from consent_validation_engine import ConsentValidationEngine
from consent_test_resources import ConsentTestResources
from fhir_utils import create_fhir_consent_from_decision, generate_audit_event

def run_consent_validation_tests():
    # ... (copy the full function body from the original file)
    pass

def demonstrate_token_validation():
    # ... (copy the full function body from the original file)
    pass

if __name__ == "__main__":
    print("🚀 Starting Consent Management Platform Validation Engine Tests")
    test_results = run_consent_validation_tests()
    demonstrate_token_validation()
    print("\n" + "=" * 80)
    print("FHIR RESOURCE GENERATION EXAMPLE")
    print("=" * 80)
    engine = ConsentValidationEngine()
    test_request = ConsentTestResources.create_sample_consent_requests()[0]
    active_consents = ConsentTestResources.create_sample_active_consents()
    decision = engine.validate_consent_request(test_request, active_consents)
    if decision.decision == "approved":
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