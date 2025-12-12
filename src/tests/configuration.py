"""
Configuration audit tests for Kong Konnect.

These tests validate that Kong is correctly configured with:
- Authentication plugins
- Rate limiting plugins
- Consumer coverage
"""

from typing import Any, Dict, List
from .base import BaseTest, TestResult, EvidenceArtifact
from ..clients.kong import KonnectClient


class CF001_AuthPluginEnabled(BaseTest):
    """Test that key-auth plugin is enabled on the service."""

    def __init__(self, konnect: KonnectClient):
        self.konnect = konnect

    @property
    def test_id(self) -> str:
        return "CF-001"

    @property
    def test_name(self) -> str:
        return "Key authentication plugin enabled"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC8.1"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        plugins = self.konnect.get_plugins(plugin_name="key-auth")
        
        # Check if at least one key-auth plugin exists and is enabled
        enabled_plugins = [p for p in plugins if p.enabled]
        passed = len(enabled_plugins) > 0
        
        details = {
            "plugin_name": "key-auth",
            "total_found": len(plugins),
            "enabled_count": len(enabled_plugins),
            "plugin_configs": [
                {
                    "id": p.id,
                    "enabled": p.enabled,
                    "service_id": p.service_id,
                    "route_id": p.route_id,
                }
                for p in plugins
            ],
            "auth_enforced": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="config_snapshot",
                description="Key-auth plugin configuration",
                data=details["plugin_configs"]
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class CF002_RateLimitPluginEnabled(BaseTest):
    """Test that rate-limiting plugin is enabled per consumer."""

    def __init__(self, konnect: KonnectClient):
        self.konnect = konnect

    @property
    def test_id(self) -> str:
        return "CF-002"

    @property
    def test_name(self) -> str:
        return "Rate limiting plugin enabled per consumer"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.1", "CC6.3", "CC8.1"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        plugins = self.konnect.get_plugins(plugin_name="rate-limiting")
        
        # Check for consumer-scoped rate limiting plugins
        consumer_plugins = [p for p in plugins if p.consumer_id and p.enabled]
        
        passed = len(consumer_plugins) > 0
        
        details = {
            "plugin_name": "rate-limiting",
            "total_found": len(plugins),
            "consumer_scoped_count": len(consumer_plugins),
            "plugin_configs": [
                {
                    "id": p.id,
                    "enabled": p.enabled,
                    "consumer_id": p.consumer_id,
                    "config": {
                        "minute": p.config.get("minute"),
                        "hour": p.config.get("hour"),
                        "policy": p.config.get("policy"),
                    },
                }
                for p in plugins
            ],
            "rate_limiting_configured": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="config_snapshot",
                description="Rate limiting plugin configuration",
                data=details["plugin_configs"]
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)


class CF003_AllConsumersHaveLimits(BaseTest):
    """Test that all consumers have rate limiting configured."""

    def __init__(self, konnect: KonnectClient):
        self.konnect = konnect

    @property
    def test_id(self) -> str:
        return "CF-003"

    @property
    def test_name(self) -> str:
        return "All consumers have rate limits configured"

    @property
    def control_mapping(self) -> List[str]:
        return ["CC6.2", "CC6.3"]

    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        consumers = self.konnect.get_consumers()
        rate_limit_plugins = self.konnect.get_plugins(plugin_name="rate-limiting")
        
        # Get consumer IDs that have rate limiting
        consumers_with_limits = {
            p.consumer_id for p in rate_limit_plugins 
            if p.consumer_id and p.enabled
        }
        
        # Check each consumer
        consumer_coverage = []
        missing_limits = []
        
        for consumer in consumers:
            has_limit = consumer.id in consumers_with_limits
            consumer_coverage.append({
                "id": consumer.id,
                "username": consumer.username,
                "custom_id": consumer.custom_id,
                "has_rate_limit": has_limit,
            })
            if not has_limit:
                missing_limits.append(consumer.username)
        
        # Pass if all consumers have rate limits
        total_consumers = len(consumers)
        covered_consumers = sum(1 for c in consumer_coverage if c["has_rate_limit"])
        coverage_percent = (covered_consumers / total_consumers * 100) if total_consumers > 0 else 0
        
        passed = len(missing_limits) == 0 and total_consumers > 0
        
        details = {
            "total_consumers": total_consumers,
            "consumers_with_limits": covered_consumers,
            "coverage_percent": round(coverage_percent, 1),
            "missing_limits": missing_limits,
            "consumer_coverage": consumer_coverage,
            "full_coverage": passed,
        }
        
        artifacts = [
            EvidenceArtifact(
                type="config_snapshot",
                description="Consumer rate limit coverage",
                data=consumer_coverage
            )
        ]
        
        return (TestResult.PASS if passed else TestResult.FAIL, details, artifacts)

