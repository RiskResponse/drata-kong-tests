"""
Drata API client for pushing compliance evidence.

This client handles:
- Authentication with Drata API
- Evidence submission
- Control mapping

Note: Drata's exact API endpoints may need adjustment based on their
current documentation. This implementation follows the general pattern
described in their developer docs.
"""

import requests
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class DrataEvidencePayload:
    """Evidence payload for Drata API submission."""
    test_id: str
    test_name: str
    result: str  # PASS, FAIL, ERROR
    timestamp: str
    control_ids: List[str]
    details: Dict[str, Any]
    artifacts: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "externalId": self.test_id,
            "name": self.test_name,
            "status": "PASSING" if self.result == "PASS" else "FAILING",
            "lastTestedAt": self.timestamp,
            "controlIds": self.control_ids,
            "evidence": {
                "details": self.details,
                "artifacts": self.artifacts,
            },
        }


class DrataClient:
    """
    Client for Drata's API.
    
    This client is designed to push evidence to Drata. The exact endpoints
    may need to be adjusted based on Drata's current API documentation.
    
    Common Drata API patterns:
    - Base URL: https://public-api.drata.com
    - Auth: Bearer token in Authorization header
    - Rate limit: 500 req/min
    """

    def __init__(self, api_key: str, api_base: str = "https://public-api.drata.com"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _request(
        self, 
        method: str, 
        path: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """Make a request to the Drata API."""
        url = f"{self.api_base}{path}"
        return self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            timeout=30,
        )

    def health_check(self) -> bool:
        """Check if we can connect to Drata API."""
        try:
            # Try to get monitors or a simple endpoint
            response = self._request("GET", "/public/monitors")
            return response.status_code in [200, 401, 403]  # 401/403 means auth issue but API is reachable
        except Exception:
            return False

    def get_controls(self) -> List[Dict[str, Any]]:
        """Get list of controls from Drata."""
        response = self._request("GET", "/public/controls")
        response.raise_for_status()
        return response.json().get("data", [])

    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get list of monitors from Drata."""
        response = self._request("GET", "/public/monitors")
        response.raise_for_status()
        return response.json().get("data", [])

    def submit_external_evidence(
        self,
        monitor_id: str,
        evidence: DrataEvidencePayload
    ) -> Dict[str, Any]:
        """
        Submit external evidence to a Drata monitor.
        
        Note: This endpoint pattern may need adjustment based on 
        Drata's current API documentation.
        """
        payload = evidence.to_dict()
        response = self._request(
            "POST",
            f"/public/monitors/{monitor_id}/evidence",
            data=payload
        )
        response.raise_for_status()
        return response.json()

    def update_monitor_status(
        self,
        monitor_id: str,
        status: str,  # "PASSING", "FAILING", "NOT_TESTED"
        evidence_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Update a monitor's status in Drata.
        
        This is an alternative pattern where we update the monitor
        directly rather than submitting evidence.
        """
        payload = {
            "status": status,
        }
        if evidence_data:
            payload["evidence"] = evidence_data
            
        response = self._request(
            "PATCH",
            f"/public/monitors/{monitor_id}",
            data=payload
        )
        response.raise_for_status()
        return response.json()


class DrataMockClient:
    """
    Mock Drata client for dry-run mode.
    
    Logs what would be sent to Drata without making actual API calls.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.submitted_evidence: List[Dict] = []

    def health_check(self) -> bool:
        return True

    def submit_external_evidence(
        self,
        monitor_id: str,
        evidence: DrataEvidencePayload
    ) -> Dict[str, Any]:
        """Mock evidence submission."""
        payload = evidence.to_dict()
        self.submitted_evidence.append({
            "monitor_id": monitor_id,
            "payload": payload,
        })
        
        if self.verbose:
            print(f"[DRY-RUN] Would submit to monitor {monitor_id}:")
            print(json.dumps(payload, indent=2, default=str))
        
        return {"status": "mock", "id": f"mock-{len(self.submitted_evidence)}"}

