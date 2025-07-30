"""
Consent Management Platform - Test Runner and Utilities
Comprehensive testing framework for consent validation engine
"""

# Replace the problematic import line:
# from consent_validation_python import (...)

# With proper relative imports:
from consent_validation_engine import ConsentValidationEngine
from consent_request import ConsentRequest
from consent_decision import ConsentDecision
from consent_decision_type import ConsentDecisionType
from consent_test_resources import ConsentTestResources

# Import our consent validation engine
from consent_validation_python import (
    ConsentValidationEngine, ConsentRequest, ConsentDecision, 
    ConsentDecisionType, ConsentTestResources
)

@dataclass
class TestResult:
    """Test execution result"""
    test_id: str
    test_name: str
    expected_outcome: str
    actual_outcome: str
    passed: bool
    execution_time_ms: float
    error_message: str = ""
    additional_info: Dict[str, Any] = None

@dataclass
class PerformanceMetrics:
    """Performance test metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    concurrent_users: int

class ConsentValidationTestRunner:
    """Comprehensive test runner for consent validation engine"""
    
    def __init__(self):
        self.engine = ConsentValidationEngine()
        self.test_results: List[TestResult] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
    def load_test_scenarios(self, test_file_path: str = None) -> List[Dict]:
        """Load test scenarios from JSON file or use embedded scenarios"""
        if test_file_path:
            with open(test_file_path, 'r') as f:
                return json.load(f)
        else:
            # Use embedded test scenarios from consent_test_resources
            return self._get_embedded_test_scenarios()
    
    def _get_embedded_test_scenarios(self) -> List[Dict]:
        """Get embedded test scenarios"""
        return [
            {
                "scenario_id": "SC001",
                "name": "Standard Treatment Consent",
                "expected_outcome": "APPROVED",
                "consent_request": {
                    "request_id": "req-sc001",
                    "patient_id": "CR123456789",
                    "requester_id": "dr-smith-001",
                    "requester_organization": "knh-hospital",
                    "requester_role": "physician",
                    "data_types": ["Patient.demographics", "Observation.vital-signs"],
                    "purpose": "TREAT",
                    "time_range": {
                        "start": "2025-01-15T00:00:00Z",
                        "end": "2025-04-15T00:00:00Z"
                    },
                    "emergency_context": False
                }
            },
            {
                "scenario_id": "SC004",
                "name": "Research Data Access",
                "expected_outcome": "APPROVED",
                "consent_request": {
                    "request_id": "req-sc004",
                    "patient_id": "CR123456789",
                    "requester_id": "researcher-004",
                    "requester_organization": "research-institute",
                    "requester_role": "researcher",
                    "data_types": ["Observation.laboratory", "Condition.diagnosis"],
                    "purpose": "HRESCH",
                    "time_range": {
                        "start": "2025-01-20T00:00:00Z",
                        "end": "2030-01-20T00:00:00Z"
                    },
                    "emergency_context": False
                }
            },
            {
                "scenario_id": "SC006",
                "name": "Prescription Access",
                "expected_outcome": "APPROVED",
                "consent_request": {
                    "request_id": "req-sc006",
                    "patient_id": "CR123456790",
                    "requester_id": "pharmacist-006",
                    "requester_organization": "mtrh",
                    "requester_role": "pharmacist",
                    "data_types": ["MedicationDispense"],
                    "purpose": "TREAT",
                    "time_range": {
                        "start": "2025-01-20T00:00:00Z",
                        "end": "2025-01-20T00:00:00Z"
                    },
                    "emergency_context": False
                }
            },
            {
                "scenario_id": "SC004",
                "name": "Invalid Patient Identity",
                "expected_outcome": "DENIED",
                "consent_request": {
                    "request_id": "req-sc005",
                    "patient_id": "CR123-p@sdf",
                    "requester_id": "dr-test-004",
                    "requester_organization": "knh-hospital",
                    "requester_role": "physician",
                    "data_types": ["Patient.demographics"],
                    "purpose": "TREAT",
                    "time_range": {
                        "start": "2025-01-01T00:00:00Z",
                        "end": "2025-12-31T00:00:00Z"
                    },
                    "emergency_context": False
                }
            }
        ]
    
    def run_functional_tests(self) -> Dict[str, Any]:
        """Run functional test suite"""
        print("=" * 80)
        print("RUNNING FUNCTIONAL TEST SUITE")
        print("=" * 80)
        
        test_scenarios = self._get_embedded_test_scenarios()
        active_consents = ConsentTestResources.create_sample_active_consents()
        
        results = []
        passed_tests = 0
        total_tests = len(test_scenarios)
        
        for scenario in test_scenarios:
            start_time = time.time()
            
            # Create consent request from scenario
            request_data = scenario["consent_request"]
            request = ConsentRequest(
                request_id=request_data["request_id"],
                patient_id=request_data["patient_id"],
                requester_id=request_data["requester_id"],
                requester_organization=request_data["requester_organization"],
                requester_role=request_data["requester_role"],
                data_types=request_data["data_types"],
                purpose=request_data["purpose"],
                time_range=request_data["time_range"],
                emergency_context=request_data.get("emergency_context", False)
            )
            
            # Execute validation
            try:
                decision = self.engine.validate_consent_request(request, active_consents)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Check if result matches expectation
                expected = scenario["expected_outcome"]
                actual = decision.decision.value.upper()
                passed = expected == actual
                
                if passed:
                    passed_tests += 1
                
                result = TestResult(
                    test_id=scenario["scenario_id"],
                    test_name=scenario["name"],
                    expected_outcome=expected,
                    actual_outcome=actual,
                    passed=passed,
                    execution_time_ms=execution_time,
                    additional_info={
                        "reason": decision.reason,
                        "access_token": decision.access_token is not None,
                        "restrictions": len(decision.restrictions) if decision.restrictions else 0,
                        "audit_info": decision.audit_info
                    }
                )
                
                print(f"✓ {scenario['scenario_id']}: {scenario['name']}")
                print(f"  Expected: {expected}, Actual: {actual}, Time: {execution_time:.1f}ms")
                if not passed:
                    print(f"  ❌ FAILED: {decision.reason}")
                else:
                    print(f"  ✅ PASSED: {decision.reason}")
                print()
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                result = TestResult(
                    test_id=scenario["scenario_id"],
                    test_name=scenario["name"],
                    expected_outcome=expected,
                    actual_outcome="ERROR",
                    passed=False,
                    execution_time_ms=execution_time,
                    error_message=str(e)
                )
                print(f"❌ {scenario['scenario_id']}: ERROR - {str(e)}")
                print()
            
            results.append(result)
            self.test_results.append(result)
        
        # Summary
        print(f"FUNCTIONAL TEST SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        print()
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "results": results
        }
    
    async def run_performance_tests(self, concurrent_users: int = 100, 
                                   total_requests: int = 1000) -> PerformanceMetrics:
        """Run performance test suite"""
        print("=" * 80)
        print(f"RUNNING PERFORMANCE TEST SUITE")
        print(f"Concurrent Users: {concurrent_users}, Total Requests: {total_requests}")
        print("=" * 80)
        
        active_consents = ConsentTestResources.create_sample_active_consents()
        test_requests = ConsentTestResources.create_sample_consent_requests()
        
        # Prepare test data
        test_scenarios = []
        for i in range(total_requests):
            # Cycle through available test requests
            base_request = test_requests[i % len(test_requests)]
            # Create unique request ID
            request = ConsentRequest(
                request_id=f"{base_request.request_id}-perf-{i}",
                patient_id=base_request.patient_id,
                requester_id=base_request.requester_id,
                requester_organization=base_request.requester_organization,
                requester_role=base_request.requester_role,
                data_types=base_request.data_types,
                purpose=base_request.purpose,
                time_range=base_request.time_range,
                emergency_context=base_request.emergency_context
            )
            test_scenarios.append(request)
        
        # Execute concurrent tests
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        async def validate_request(request: ConsentRequest) -> Tuple[float, bool]:
            """Validate a single request and return response time and success status"""
            req_start = time.time()
            try:
                decision = self.engine.validate_consent_request(request, active_consents)
                req_time = (time.time() - req_start) * 1000
                return req_time, True
            except Exception:
                req_time = (time.time() - req_start) * 1000
                return req_time, False
        
        # Run concurrent validation requests
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def bounded_validate(request: ConsentRequest):
            async with semaphore:
                return await validate_request(request)
        
        # Execute all requests concurrently
        tasks = [bounded_validate(req) for req in test_scenarios]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Process results
        for response_time, success in results:
            response_times.append(response_time)
            if success:
                successful_requests += 1
            else:
                failed_requests += 1
        
        # Calculate metrics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        response_times_sorted = sorted(response_times)
        p95_response_time = response_times_sorted[int(0.95 * len(response_times_sorted))]
        p99_response_time = response_times_sorted[int(0.99 * len(response_times_sorted))]
        requests_per_second = total_requests / total_time
        
        metrics = PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time_ms=avg_response_time,
            median_response_time_ms=median_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            concurrent_users=concurrent_users
        )
        
        self.performance_metrics.append(metrics)
        
        # Print results
        print(f"Performance Test Results:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  Success Rate: {(successful_requests / total_requests) * 100:.1f}%")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Requests/Second: {requests_per_second:.1f}")
        print(f"  Average Response Time: {avg_response_time:.1f}ms")
        print(f"  Median Response Time: {median_response_time:.1f}ms")
        print(f"  95th Percentile: {p95_response_time:.1f}ms")
        print(f"  99th Percentile: {p99_response_time:.1f}ms")
        print()
        
        return metrics
    
    def run_edge_case_tests(self) -> Dict[str, Any]:
        """Run edge case and boundary condition tests"""
        print("=" * 80)
        print("RUNNING EDGE CASE TEST SUITE")
        print("=" * 80)
        
        active_consents = ConsentTestResources.create_sample_active_consents()
        edge_cases = self._create_edge_case_scenarios()
        
        results = []
        passed_tests = 0
        
        for case in edge_cases:
            start_time = time.time()
            request = case["request"]
            expected_behavior = case["expected_behavior"]
            
            try:
                decision = self.engine.validate_consent_request(request, active_consents)
                execution_time = (time.time() - start_time) * 1000
                
                # Validate expected behavior
                passed = self._validate_edge_case_behavior(decision, expected_behavior)
                if passed:
                    passed_tests += 1
                
                result = {
                    "case_id": case["case_id"],
                    "description": case["description"],
                    "passed": passed,
                    "execution_time_ms": execution_time,
                    "decision": decision.decision.value,
                    "reason": decision.reason
                }
                
                print(f"{'✅' if passed else '❌'} {case['case_id']}: {case['description']}")
                print(f"  Result: {decision.decision.value} - {decision.reason}")
                print(f"  Time: {execution_time:.1f}ms")
                print()
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                result = {
                    "case_id": case["case_id"],
                    "description": case["description"],
                    "passed": False,
                    "execution_time_ms": execution_time,
                    "error": str(e)
                }
                print(f"❌ {case['case_id']}: ERROR - {str(e)}")
                print()
            
            results.append(result)
        
        print(f"EDGE CASE TEST SUMMARY:")
        print(f"Total Cases: {len(edge_cases)}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(edge_cases) - passed_tests}")
        print()
        
        return {
            "total_cases": len(edge_cases),
            "passed_cases": passed_tests,
            "failed_cases": len(edge_cases) - passed_tests,
            "results": results
        }
    
    def _create_edge_case_scenarios(self) -> List[Dict]:
        """Create edge case test scenarios"""
        return [
            {
                "case_id": "EDGE001",
                "description": "Null patient ID",
                "request": ConsentRequest(
                    request_id="edge-001",
                    patient_id="",
                    requester_id="dr-test",
                    requester_organization="test-org",
                    requester_role="physician",
                    data_types=["Patient.demographics"],
                    purpose="TREAT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "expected_behavior": {"decision": "DENIED", "reason_contains": "Invalid patient"}
            },
            {
                "case_id": "EDGE002",
                "description": "Empty data types list",
                "request": ConsentRequest(
                    request_id="edge-002",
                    patient_id="CR123456789",
                    requester_id="dr-test",
                    requester_organization="test-org",
                    requester_role="physician",
                    data_types=[],
                    purpose="TREAT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "expected_behavior": {"decision": "DENIED", "reason_contains": "No valid consent"}
            },
            {
                "case_id": "EDGE003",
                "description": "Invalid date format in time range",
                "request": ConsentRequest(
                    request_id="edge-003",
                    patient_id="CR123456789",
                    requester_id="dr-test",
                    requester_organization="test-org",
                    requester_role="physician",
                    data_types=["Patient.demographics"],
                    purpose="TREAT",
                    time_range={"start": "invalid-date", "end": "2025-12-31T00:00:00Z"}
                ),
                "expected_behavior": {"decision": "DENIED", "reason_contains": "temporal"}
            },
            {
                "case_id": "EDGE004",
                "description": "Very long request ID",
                "request": ConsentRequest(
                    request_id="a" * 1000,  # 1000 character request ID
                    patient_id="CR123456789",
                    requester_id="dr-test",
                    requester_organization="test-org",
                    requester_role="physician",
                    data_types=["Patient.demographics"],
                    purpose="TREAT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "expected_behavior": {"decision": "APPROVED", "no_error": True}
            },
            {
                "case_id": "EDGE005",
                "description": "Unknown purpose code",
                "request": ConsentRequest(
                    request_id="edge-005",
                    patient_id="CR123456789",
                    requester_id="dr-test",
                    requester_organization="test-org",
                    requester_role="physician",
                    data_types=["Patient.demographics"],
                    purpose="UNKNOWN_PURPOSE",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "expected_behavior": {"decision": "DENIED", "reason_contains": "purpose"}
            }
        ]
    
    def _validate_edge_case_behavior(self, decision: ConsentDecision, expected: Dict) -> bool:
        """Validate edge case behavior against expectations"""
        if "decision" in expected:
            if decision.decision.value.upper() != expected["decision"]:
                return False
        
        if "reason_contains" in expected:
            if expected["reason_contains"].lower() not in decision.reason.lower():
                return False
        
        if "no_error" in expected and expected["no_error"]:
            if decision.decision == ConsentDecisionType.DENIED and "error" in decision.reason.lower():
                return False
        
        return True
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-focused tests"""
        print("=" * 80)
        print("RUNNING SECURITY TEST SUITE")
        print("=" * 80)
        
        active_consents = ConsentTestResources.create_sample_active_consents()
        security_tests = self._create_security_test_scenarios()
        
        results = []
        passed_tests = 0
        
        for test in security_tests:
            start_time = time.time()
            request = test["request"]
            security_expectation = test["security_expectation"]
            
            try:
                decision = self.engine.validate_consent_request(request, active_consents)
                execution_time = (time.time() - start_time) * 1000
                
                # Validate security behavior
                passed = self._validate_security_behavior(decision, security_expectation)
                if passed:
                    passed_tests += 1
                
                result = {
                    "test_id": test["test_id"],
                    "description": test["description"],
                    "passed": passed,
                    "execution_time_ms": execution_time,
                    "security_validated": passed
                }
                
                print(f"{'✅' if passed else '❌'} {test['test_id']}: {test['description']}")
                print(f"  Security Check: {'PASSED' if passed else 'FAILED'}")
                print()
                
            except Exception as e:
                result = {
                    "test_id": test["test_id"],
                    "description": test["description"],
                    "passed": False,
                    "error": str(e)
                }
                print(f"❌ {test['test_id']}: ERROR - {str(e)}")
                print()
            
            results.append(result)
        
        print(f"SECURITY TEST SUMMARY:")
        print(f"Total Tests: {len(security_tests)}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(security_tests) - passed_tests}")
        print()
        
        return {
            "total_tests": len(security_tests),
            "passed_tests": passed_tests,
            "failed_tests": len(security_tests) - passed_tests,
            "results": results
        }
    
    def _create_security_test_scenarios(self) -> List[Dict]:
        """Create security test scenarios"""
        return [
            {
                "test_id": "SEC001",
                "description": "Unauthorized cross-organization access attempt",
                "request": ConsentRequest(
                    request_id="sec-001",
                    patient_id="CR123456789",
                    requester_id="malicious-user",
                    requester_organization="unauthorized-org",
                    requester_role="physician",
                    data_types=["Patient.demographics", "Observation.laboratory"],
                    purpose="TREAT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "security_expectation": {
                    "should_deny": True,
                    "audit_logged": True,
                    "reason_contains": "relationship"
                }
            },
            {
                "test_id": "SEC002",
                "description": "Attempt to access mental health data without proper certification",
                "request": ConsentRequest(
                    request_id="sec-002",
                    patient_id="CR123456789",
                    requester_id="general-physician",
                    requester_organization="general-hospital",
                    requester_role="physician",
                    data_types=["Condition.mental-health"],
                    purpose="TREAT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "security_expectation": {
                    "should_deny": True,
                    "high_sensitivity_protection": True
                }
            },
            {
                "test_id": "SEC003",
                "description": "Marketing access with patient opt-out",
                "request": ConsentRequest(
                    request_id="sec-003",
                    patient_id="CR123456789",
                    requester_id="marketing-dept",
                    requester_organization="knh-hospital",
                    requester_role="marketing",
                    data_types=["Patient.demographics"],
                    purpose="HMARKT",
                    time_range={"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"}
                ),
                "security_expectation": {
                    "should_deny": True,
                    "privacy_preference_enforced": True
                }
            }
        ]
    
    def _validate_security_behavior(self, decision: ConsentDecision, expectation: Dict) -> bool:
        """Validate security behavior against expectations"""
        if expectation.get("should_deny", False):
            if decision.decision != ConsentDecisionType.DENIED:
                return False
        
        if expectation.get("audit_logged", False):
            if not decision.audit_info:
                return False
        
        if "reason_contains" in expectation:
            if expectation["reason_contains"].lower() not in decision.reason.lower():
                return False
        
        return True
    
    def generate_test_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "test_execution_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_test_results": len(self.test_results),
                "total_performance_metrics": len(self.performance_metrics)
            },
            "functional_tests": {
                "total_executed": len([r for r in self.test_results if r.test_id.startswith("SC")]),
                "passed": len([r for r in self.test_results if r.test_id.startswith("SC") and r.passed]),
                "failed": len([r for r in self.test_results if r.test_id.startswith("SC") and not r.passed]),
                "average_execution_time_ms": statistics.mean([r.execution_time_ms for r in self.test_results if r.test_id.startswith("SC")]) if self.test_results else 0
            },
            "performance_summary": {
                "metrics": [vars(m) for m in self.performance_metrics]
            },
            "detailed_results": [vars(r) for r in self.test_results],
            "recommendations": self._generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Test report saved to: {output_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze functional test results
        failed_tests = [r for r in self.test_results if not r.passed]
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failing functional tests")
        
        # Analyze performance results
        if self.performance_metrics:
            latest_metrics = self.performance_metrics[-1]
            if latest_metrics.average_response_time_ms > 500:
                recommendations.append("Consider optimizing response times - average exceeds 500ms")
            if latest_metrics.p95_response_time_ms > 1000:
                recommendations.append("Investigate performance bottlenecks - 95th percentile exceeds 1s")
        
        # Security recommendations
        recommendations.append("Implement additional security monitoring for suspicious access patterns")
        recommendations.append("Consider implementing rate limiting per organization")
        
        return recommendations


# Integration and Utility Functions
def create_mock_consent_database():
    """Create mock consent database for testing"""
    return {
        "consents": ConsentTestResources.create_sample_active_consents(),
        "patients": {
            "CR123456789": {
                "id": "CR123456789",
                "name": "John Doe",
                "managingOrganization": "moh-kenya",
                "preferences": {
                    "marketing_opt_out": True,
                    "data_masking": "standard"
                }
            }
        },
        "organizations": {
            "knh-hospital": {"name": "Kenyatta National Hospital", "type": "hospital"},
            "moh-kenya": {"name": "Ministry of Health Kenya", "type": "government"},
            "research-institute": {"name": "Research Institute", "type": "research"}
        }
    }

def run_comprehensive_test_suite():
    """Run the complete test suite"""
    print("🚀 STARTING COMPREHENSIVE CONSENT VALIDATION TEST SUITE")
    print("=" * 80)
    
    runner = ConsentValidationTestRunner()
    
    # Run functional tests
    functional_results = runner.run_functional_tests()
    
    # Run performance tests
    performance_results = asyncio.run(runner.run_performance_tests(
        concurrent_users=50, 
        total_requests=500
    ))
    
    # Run edge case tests
    edge_case_results = runner.run_edge_case_tests()
    
    # Run security tests
    security_results = runner.run_security_tests()
    
    # Generate comprehensive report
    report = runner.generate_test_report("consent_validation_test_report.json")
    
    # Print final summary
    print("=" * 80)
    print("🎯 COMPREHENSIVE TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"Functional Tests: {functional_results['passed_tests']}/{functional_results['total_tests']} passed")
    print(f"Performance: {performance_results.requests_per_second:.1f} req/s, {performance_results.average_response_time_ms:.1f}ms avg")
    print(f"Edge Cases: {edge_case_results['passed_cases']}/{edge_case_results['total_cases']} passed")
    print(f"Security Tests: {security_results['passed_tests']}/{security_results['total_tests']} passed")
    print()
    print("📊 Detailed report saved to: consent_validation_test_report.json")
    print("✅ Test suite execution completed!")
    
    return report

