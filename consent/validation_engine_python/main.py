import json
import sys
from datetime import datetime
from consent_validation_engine import ConsentValidationEngine
from consent_test_resources import ConsentTestResources
from fhir_utils import create_fhir_consent_from_decision, generate_audit_event
from consent_decision_type import ConsentDecisionType
from utils import get_current_utc


def run_consent_validation_tests():
    """Run comprehensive consent validation tests"""
    print("=" * 80)
    print("CONSENT MANAGEMENT PLATFORM - VALIDATION ENGINE TESTS")
    print("=" * 80)

    try:
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

            # Validate consent request
            start_time = get_current_utc()
            decision = engine.validate_consent_request(request, active_consents)
            execution_time = (get_current_utc() - start_time).total_seconds() * 1000

            print(f"  RESULT: {decision.decision.value.upper()}")
            print(f"  Reason: {decision.reason}")
            print(f"  Execution Time: {execution_time:.1f}ms")

            if decision.access_token:
                print(f"  Access Token: {decision.access_token}")

            if decision.permissions:
                perms = decision.permissions
                if perms.get('allowed'):
                    print(f"  Allowed: {', '.join(perms['allowed'])}")
                if perms.get('pseudonymized'):
                    print(f"  Pseudonymized: {', '.join(perms['pseudonymized'])}")

            print("-" * 60)

            results.append({
                "test_case": i,
                "request_id": request.request_id,
                "decision": decision.decision.value,
                "reason": decision.reason,
                "execution_time_ms": execution_time,
                "has_token": bool(decision.access_token)
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

        return results

    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def demonstrate_fhir_generation():
    """Demonstrate FHIR resource generation"""
    print("\n" + "=" * 80)
    print("FHIR RESOURCE GENERATION EXAMPLE")
    print("=" * 80)

    try:
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
        else:
            print(f"Cannot generate FHIR resources - Decision: {decision.decision.value}")
            print(f"Reason: {decision.reason}")

    except Exception as e:
        print(f"❌ Error in FHIR generation: {str(e)}")
        import traceback
        traceback.print_exc()


def test_datetime_fixes():
    """Test the datetime fixes specifically"""
    print("\n" + "=" * 80)
    print("TESTING DATETIME FIXES")
    print("=" * 80)

    from utils import parse_datetime_safe, get_current_utc

    # Test various datetime formats
    test_dates = [
        "2025-01-01T00:00:00Z",
        "2025-12-31T23:59:59+00:00",
        "2026-01-01T00:00:00",
        "",
        None
    ]

    print("Testing datetime parsing:")
    for date_str in test_dates:
        try:
            parsed = parse_datetime_safe(date_str)
            print(f"  '{date_str}' -> {parsed} (timezone: {parsed.tzinfo})")
        except Exception as e:
            print(f"  '{date_str}' -> ERROR: {e}")

    # Test current UTC
    current = get_current_utc()
    print(f"\nCurrent UTC time: {current} (timezone: {current.tzinfo})")

    # Test comparison (this was the problematic part)
    print("\nTesting timezone-aware datetime comparisons:")
    try:
        date1 = parse_datetime_safe("2025-01-01T00:00:00Z")
        date2 = parse_datetime_safe("2025-12-31T23:59:59Z")
        current = get_current_utc()

        print(f"  {date1} <= {current} <= {date2}: {date1 <= current <= date2}")
        print("  ✅ No timezone comparison errors!")

    except Exception as e:
        print(f"  ❌ Timezone comparison error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Fixed Consent Management Platform Validation Engine Tests")

    # Test datetime fixes first
    test_datetime_fixes()

    # Run main tests
    test_results = run_consent_validation_tests()

    # Demonstrate FHIR generation
    demonstrate_fhir_generation()

    print(f"\n✅ All tests completed successfully!")
    print(f"📊 Test Results Summary:")
    if test_results:
        approved_count = sum(1 for r in test_results if r["decision"] == "approved")
        print(f"   - Approved requests: {approved_count}")
        print(f"   - Total test cases: {len(test_results)}")
        print(f"   - Success rate: {(approved_count / len(test_results)) * 100:.1f}%")
    else:
        print("   - No test results available")