"""
Configuration management for Drata Kong Tests.

Loads configuration from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class KongConfig:
    """Kong Konnect and Dataplane configuration."""
    konnect_token: str
    konnect_region: str
    control_plane_name: str
    dataplane_url: str
    free_trial_key: str
    pro_key: str

    @classmethod
    def from_env(cls) -> "KongConfig":
        return cls(
            konnect_token=os.environ["KONNECT_TOKEN"],
            konnect_region=os.getenv("KONNECT_REGION", "us"),
            control_plane_name=os.getenv("CONTROL_PLANE_NAME", "kong-hybrid-rate-limit-demo"),
            dataplane_url=os.environ["DATAPLANE_URL"],
            free_trial_key=os.getenv("FREE_TRIAL_KEY", "free-trial-key"),
            pro_key=os.getenv("PRO_KEY", "pro-key"),
        )

    @property
    def konnect_api_base(self) -> str:
        """Return the Konnect API base URL for the configured region."""
        region_map = {
            "us": "https://us.api.konghq.com",
            "eu": "https://eu.api.konghq.com",
            "au": "https://au.api.konghq.com",
        }
        return region_map.get(self.konnect_region, region_map["us"])


@dataclass
class DrataConfig:
    """Drata API configuration."""
    api_key: str
    api_base: str

    @classmethod
    def from_env(cls) -> "DrataConfig":
        return cls(
            api_key=os.environ["DRATA_API_KEY"],
            api_base=os.getenv("DRATA_API_BASE", "https://public-api.drata.com"),
        )


@dataclass
class GCPConfig:
    """GCP configuration."""
    project_id: str
    region: str

    @classmethod
    def from_env(cls) -> "GCPConfig":
        return cls(
            project_id=os.getenv("GCP_PROJECT_ID", "drata-kong-tests"),
            region=os.getenv("GCP_REGION", "us-east1"),
        )


@dataclass
class Config:
    """Main configuration container."""
    kong: KongConfig
    drata: DrataConfig
    gcp: GCPConfig
    dry_run: bool
    verbose: bool

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            kong=KongConfig.from_env(),
            drata=DrataConfig.from_env(),
            gcp=GCPConfig.from_env(),
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            verbose=os.getenv("VERBOSE", "false").lower() == "true",
        )


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config.from_env()

