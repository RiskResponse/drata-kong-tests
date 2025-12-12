"""
Kong Konnect and Dataplane API clients.

Provides methods for:
- Konnect Admin API (configuration audits)
- Dataplane HTTP requests (runtime tests)
"""

import requests
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class KongConsumer:
    """Represents a Kong consumer."""
    id: str
    username: str
    custom_id: Optional[str]
    created_at: int


@dataclass
class KongPlugin:
    """Represents a Kong plugin."""
    id: str
    name: str
    enabled: bool
    config: Dict[str, Any]
    consumer_id: Optional[str] = None
    service_id: Optional[str] = None
    route_id: Optional[str] = None


class KonnectClient:
    """Client for Kong Konnect Admin API."""

    def __init__(self, token: str, api_base: str, control_plane_name: str):
        self.token = token
        self.api_base = api_base
        self.control_plane_name = control_plane_name
        self.control_plane_id: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def _get_control_plane_id(self) -> str:
        """Get or cache the control plane ID."""
        if self.control_plane_id:
            return self.control_plane_id

        response = self.session.get(f"{self.api_base}/v2/control-planes")
        response.raise_for_status()
        
        data = response.json()
        for cp in data.get("data", []):
            if cp.get("name") == self.control_plane_name:
                self.control_plane_id = cp["id"]
                return self.control_plane_id
        
        raise ValueError(f"Control plane '{self.control_plane_name}' not found")

    def _admin_url(self, path: str) -> str:
        """Build admin API URL for the control plane."""
        cp_id = self._get_control_plane_id()
        return f"{self.api_base}/v2/control-planes/{cp_id}/core-entities{path}"

    def get_consumers(self) -> List[KongConsumer]:
        """Get all consumers from the control plane."""
        response = self.session.get(self._admin_url("/consumers"))
        response.raise_for_status()
        
        consumers = []
        for item in response.json().get("data", []):
            consumers.append(KongConsumer(
                id=item["id"],
                username=item.get("username", ""),
                custom_id=item.get("custom_id"),
                created_at=item.get("created_at", 0),
            ))
        return consumers

    def get_plugins(self, plugin_name: Optional[str] = None) -> List[KongPlugin]:
        """Get all plugins, optionally filtered by name."""
        response = self.session.get(self._admin_url("/plugins"))
        response.raise_for_status()
        
        plugins = []
        for item in response.json().get("data", []):
            if plugin_name and item.get("name") != plugin_name:
                continue
            plugins.append(KongPlugin(
                id=item["id"],
                name=item["name"],
                enabled=item.get("enabled", True),
                config=item.get("config", {}),
                consumer_id=item.get("consumer", {}).get("id") if item.get("consumer") else None,
                service_id=item.get("service", {}).get("id") if item.get("service") else None,
                route_id=item.get("route", {}).get("id") if item.get("route") else None,
            ))
        return plugins

    def get_services(self) -> List[Dict[str, Any]]:
        """Get all services from the control plane."""
        response = self.session.get(self._admin_url("/services"))
        response.raise_for_status()
        return response.json().get("data", [])

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all routes from the control plane."""
        response = self.session.get(self._admin_url("/routes"))
        response.raise_for_status()
        return response.json().get("data", [])


class DataplaneClient:
    """Client for Kong Dataplane HTTP requests."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """Make a request to the dataplane."""
        url = f"{self.base_url}{path}"
        
        req_headers = headers or {}
        if api_key:
            req_headers["X-API-Key"] = api_key
        
        return self.session.request(
            method=method,
            url=url,
            headers=req_headers,
            timeout=self.timeout,
            **kwargs
        )

    def get(self, path: str, api_key: Optional[str] = None, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self.request("GET", path, api_key=api_key, **kwargs)

    def health_check(self, api_key: str) -> tuple[bool, int, Dict[str, Any]]:
        """
        Check health endpoint.
        
        Returns: (is_healthy, status_code, response_json)
        """
        try:
            response = self.get("/api/health", api_key=api_key)
            try:
                json_data = response.json()
            except:
                json_data = {}
            return response.status_code == 200, response.status_code, json_data
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_rate_limit(self, api_key: str, path: str, num_requests: int) -> List[int]:
        """
        Send multiple requests to test rate limiting.
        
        Returns: List of HTTP status codes for each request.
        """
        results = []
        for _ in range(num_requests):
            try:
                response = self.get(path, api_key=api_key)
                results.append(response.status_code)
            except Exception:
                results.append(0)
        return results

    def get_whoami(self, api_key: str) -> tuple[int, Dict[str, Any]]:
        """
        Get whoami endpoint to check consumer identity.
        
        Returns: (status_code, response_json)
        """
        try:
            response = self.get("/api/whoami", api_key=api_key)
            try:
                json_data = response.json()
            except:
                json_data = {}
            return response.status_code, json_data
        except Exception as e:
            return 0, {"error": str(e)}

