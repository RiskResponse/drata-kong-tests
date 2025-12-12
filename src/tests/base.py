"""
Base test class and evidence schema for Drata Kong Tests.

All tests inherit from BaseTest and produce standardized Evidence objects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class TestResult(Enum):
    """Test result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"


@dataclass
class EvidenceArtifact:
    """A single piece of evidence captured during a test."""
    type: str  # e.g., "http_response", "config_snapshot", "screenshot"
    description: str
    data: Any


@dataclass
class Evidence:
    """
    Standardized evidence schema for Drata.
    
    This structure is designed to map directly to Drata's evidence requirements
    and SOC 2 Common Criteria.
    """
    test_id: str
    test_name: str
    timestamp: str
    result: str  # PASS, FAIL, ERROR, SKIP
    control_mapping: List[str]  # e.g., ["CC6.1", "CC7.2"]
    duration_ms: int
    details: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class BaseTest(ABC):
    """
    Abstract base class for all compliance tests.
    
    Subclasses must implement:
    - test_id: Unique identifier (e.g., "RT-001")
    - test_name: Human-readable name
    - control_mapping: List of SOC 2 controls this test validates
    - run(): Execute the test and return Evidence
    """

    @property
    @abstractmethod
    def test_id(self) -> str:
        """Unique test identifier (e.g., RT-001, CF-001)."""
        pass

    @property
    @abstractmethod
    def test_name(self) -> str:
        """Human-readable test name."""
        pass

    @property
    @abstractmethod
    def control_mapping(self) -> List[str]:
        """SOC 2 controls this test validates (e.g., ['CC6.1', 'CC7.2'])."""
        pass

    @abstractmethod
    def execute(self) -> tuple[TestResult, Dict[str, Any], List[EvidenceArtifact]]:
        """
        Execute the test logic.
        
        Returns:
            Tuple of (result, details_dict, artifacts_list)
        """
        pass

    def run(self) -> Evidence:
        """
        Run the test and produce standardized Evidence.
        
        This method handles timing, error handling, and evidence formatting.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        start_time = time.time()
        
        try:
            result, details, artifacts = self.execute()
            duration_ms = int((time.time() - start_time) * 1000)
            
            return Evidence(
                test_id=self.test_id,
                test_name=self.test_name,
                timestamp=timestamp,
                result=result.value,
                control_mapping=self.control_mapping,
                duration_ms=duration_ms,
                details=details,
                artifacts=[asdict(a) for a in artifacts],
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            return Evidence(
                test_id=self.test_id,
                test_name=self.test_name,
                timestamp=timestamp,
                result=TestResult.ERROR.value,
                control_mapping=self.control_mapping,
                duration_ms=duration_ms,
                details={},
                artifacts=[],
                error_message=str(e),
            )

