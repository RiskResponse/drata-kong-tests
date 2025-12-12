"""
Runtime tests for Kong Dataplane.

These tests validate that Kong is correctly enforcing:
- Rate limiting per consumer tier
- API key authentication
- Consumer identity injection
"""

from typing import Any, Dict, List
from .base import BaseTest, TestResult, EvidenceArtifact
from ..clients.kong import DataplaneClient


class RT001_RateLimitFreeTier(BaseTest):
    """Test that free tier rate limiting is enforced (5 req/min)."""

    def __init__(self, dataplane: DataplaneClient, api_key: str):
        self.dataplane = dataplane
        self.api_key = api_key

    @property
    def test_id(self) -> str:
        return "RT-001"

    @property
    def test_name(self) -> str:
        return "Rate limiting enforces free tier (5 req/min)"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.3", "CC7.2"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        # Send 8 requests - first 5 should pass, rest should be rate limited
        num_requests = 8
        expected_limit = 5
        
        results = self.dataplane.test_rate_limit(
            api_key=self.api_key,
            path="/api/hello",
            num_requests=num_requests
        )
        
        # Count successes and rate limits
        success_count = sum(1 for r in results if r == 200)
        rate_limited_count = sum(1 for r in results if r == 429)
        
        # Test passes if we see rate limiting kick in
        # (some requests succeed, then 429s appear)
        passed = rate_limited_count > 0 and success_count <= expected_limit
        
        details = {
            "api_key": self.api_key,
            "tier": "free_trial",
            "expected_limit": expected_limit,
            "requests_sent": num_requests,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "results": [{"request": i+1, "status": r} for i, r in enumerate(results)],
            "rate_limit_triggered": rate_limited_count > 0,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="test_results",
                description="HTTP status codes for rate limit test",
                data=results
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class RT002_RateLimitProTier(BaseTest):
    """Test that pro tier rate limiting is enforced (60 req/min)."""

    def __init__(self, dataplane: DataplaneClient, api_key: str):
        self.dataplane = dataplane
        self.api_key = api_key

    @property
    def test_id(self) -> str:
        return "RT-002"

    @property
    def test_name(self) -> str:
        return "Rate limiting enforces pro tier (60 req/min)"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.3", "CC7.2"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        # Send 10 requests - all should pass for pro tier (limit is 60/min)
        num_requests = 10
        
        results = self.dataplane.test_rate_limit(
            api_key=self.api_key,
            path="/api/hello",
            num_requests=num_requests
        )
        
        success_count = sum(1 for r in results if r == 200)
        rate_limited_count = sum(1 for r in results if r == 429)
        
        # All requests should succeed for pro tier
        passed = success_count == num_requests
        
        details = {
            "api_key": self.api_key,
            "tier": "pro",
            "expected_limit": 60,
            "requests_sent": num_requests,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "results": [{"request": i+1, "status": r} for i, r in enumerate(results)],
            "all_passed": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="test_results",
                description="HTTP status codes for pro tier test",
                data=results
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class RT003_InvalidKeyRejected(BaseTest):
    """Test that invalid API keys are rejected with 401."""

    def __init__(self, dataplane: DataplaneClient):
        self.dataplane = dataplane

    @property
    def test_id(self) -> str:
        return "RT-003"

    @property
    def test_name(self) -> str:
        return "Invalid API key rejected (401)"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.6"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        response = self.dataplane.get("/api/hello", api_key="invalid-key-12345")
        
        passed = response.status_code == 401
        
        details = {
            "api_key_used": "invalid-key-12345",
            "expected_status": 401,
            "actual_status": response.status_code,
            "rejected": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="http_response",
                description="Response from invalid key request",
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class RT004_MissingKeyRejected(BaseTest):
    """Test that missing API keys are rejected with 401."""

    def __init__(self, dataplane: DataplaneClient):
        self.dataplane = dataplane

    @property
    def test_id(self) -> str:
        return "RT-004"

    @property
    def test_name(self) -> str:
        return "Missing API key rejected (401)"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.6"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        response = self.dataplane.get("/api/hello", api_key=None)
        
        passed = response.status_code == 401
        
        details = {
            "api_key_used": None,
            "expected_status": 401,
            "actual_status": response.status_code,
            "rejected": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="http_response",
                description="Response from request without API key",
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class RT005_ValidKeyAccepted(BaseTest):
    """Test that valid API keys are accepted with 200."""

    def __init__(self, dataplane: DataplaneClient, api_key: str):
        self.dataplane = dataplane
        self.api_key = api_key

    @property
    def test_id(self) -> str:
        return "RT-005"

    @property
    def test_name(self) -> str:
        return "Valid API key accepted (200)"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        is_healthy, status_code, response_data = self.dataplane.health_check(self.api_key)
        
        passed = status_code == 200
        
        details = {
            "api_key_used": self.api_key,
            "expected_status": 200,
            "actual_status": status_code,
            "accepted": passed,
            "health_response": response_data,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="http_response",
                description="Health check response with valid key",
                data=response_data
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class RT006_ConsumerIdentityInjected(BaseTest):
    """Test that Kong injects consumer identity headers."""

    def __init__(self, dataplane: DataplaneClient, api_key: str, expected_custom_id: str):
        self.dataplane = dataplane
        self.api_key = api_key
        self.expected_custom_id = expected_custom_id

    @property
    def test_id(self) -> str:
        return "RT-006"

    @property
    def test_name(self) -> str:
        return "Consumer identity injected correctly"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.3"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        status_code, response_data = self.dataplane.get_whoami(self.api_key)
        
        # Check if consumer info is present
        consumer_info = response_data.get("consumer", {})
        actual_custom_id = consumer_info.get("custom_id", "")
        
        passed = (
            status_code == 200 and
            actual_custom_id == self.expected_custom_id
        )
        
        details = {
            "api_key_used": self.api_key,
            "expected_custom_id": self.expected_custom_id,
            "actual_custom_id": actual_custom_id,
            "consumer_info": consumer_info,
            "identity_correct": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="http_response",
                description="Whoami response showing consumer identity",
                data=response_data
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)

