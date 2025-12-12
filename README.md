# Drata Kong Tests

Automated compliance tests for Kong Gateway that push evidence to Drata for SOC 2.

## What This Does

Runs daily tests against your Kong Gateway deployment and pushes evidence to Drata:

| Test ID | Test Name | SOC 2 Controls |
|---------|-----------|----------------|
| RT-001 | Rate limiting enforces free tier (5 req/min) | CC6.1, CC6.3, CC7.2 |
| RT-002 | Rate limiting enforces pro tier (60 req/min) | CC6.1, CC6.3, CC7.2 |
| RT-003 | Invalid API key rejected (401) | CC6.1, CC6.6 |
| RT-004 | Missing API key rejected (401) | CC6.1, CC6.6 |
| RT-005 | Valid API key accepted (200) | CC6.1 |
| RT-006 | Consumer identity injected correctly | CC6.1, CC6.3 |
| CF-001 | Key authentication plugin enabled | CC6.1, CC8.1 |
| CF-002 | Rate limiting plugin enabled per consumer | CC6.1, CC6.3, CC8.1 |
| CF-003 | All consumers have rate limits configured | CC6.2, CC6.3 |

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────┐
│ Cloud Scheduler │────▶│   Cloud Run Job     │────▶│  Drata API   │
│ (Daily 6am UTC) │     │   (Python tests)    │     │  (Evidence)  │
└─────────────────┘     └─────────┬───────────┘     └──────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Konnect  │ │ Kong DP  │ │ GCP APIs │
              │   API    │ │ (tests)  │ │          │
              └──────────┘ └──────────┘ └──────────┘
```

## Prerequisites

- GCP project with billing enabled
- Kong Gateway deployed (see [kong-rate-limiting-demo](https://github.com/RiskResponse/kong-rate-limiting-demo))
- Drata account with API access
- Terraform >= 1.0
- Python >= 3.11
- Docker

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/RiskResponse/drata-kong-tests.git
cd drata-kong-tests

# Copy and edit environment file
cp .env.example .env
# Edit .env with your values
```

### 2. Run locally (dry run)

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests without pushing to Drata
./scripts/run-local.sh --dry-run
```

### 3. Deploy to GCP

```bash
# Configure Terraform
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
cd ..

# Deploy
./scripts/deploy.sh
```

### 4. Add secrets

```bash
# Add Kong Konnect token
echo -n 'kpat_xxx' | gcloud secrets versions add konnect-token --data-file=-

# Add Drata API key
echo -n 'your_drata_key' | gcloud secrets versions add drata-api-key --data-file=-
```

### 5. Trigger a test run

```bash
./scripts/trigger.sh
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `KONNECT_TOKEN` | Yes | Kong Konnect API token |
| `KONNECT_REGION` | No | Konnect region (default: `us`) |
| `CONTROL_PLANE_NAME` | No | Control plane name (default: `kong-hybrid-rate-limit-demo`) |
| `DATAPLANE_URL` | Yes | Kong dataplane URL |
| `FREE_TRIAL_KEY` | No | Free trial API key (default: `free-trial-key`) |
| `PRO_KEY` | No | Pro tier API key (default: `pro-key`) |
| `DRATA_API_KEY` | Yes | Drata API key |
| `DRATA_API_BASE` | No | Drata API base URL |
| `DRY_RUN` | No | Skip Drata push (default: `false`) |
| `VERBOSE` | No | Verbose output (default: `false`) |

### Terraform Variables

See `terraform/terraform.tfvars.example` for all configurable options.

## Project Structure

```
drata-kong-tests/
├── README.md
├── requirements.txt
├── Dockerfile
├── .env.example
│
├── src/
│   ├── main.py                    # Entry point
│   ├── config.py                  # Configuration
│   ├── tests/
│   │   ├── base.py                # Base test class
│   │   ├── runtime.py             # RT-001 to RT-006
│   │   └── configuration.py       # CF-001 to CF-003
│   └── clients/
│       ├── kong.py                # Kong API clients
│       └── drata.py               # Drata API client
│
├── terraform/
│   ├── main.tf                    # Cloud Run Job + Scheduler
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
│
└── scripts/
    ├── deploy.sh                  # Deploy to GCP
    ├── run-local.sh               # Run locally
    └── trigger.sh                 # Manual trigger
```

## SOC 2 Control Mapping

| Control | Description | Tests |
|---------|-------------|-------|
| CC6.1 | Logical access security | RT-001 to RT-006, CF-001, CF-002 |
| CC6.2 | Access provisioning/removal | CF-003 |
| CC6.3 | Role-based access | RT-001, RT-002, RT-006, CF-002, CF-003 |
| CC6.6 | Authentication mechanisms | RT-003, RT-004 |
| CC7.2 | Monitoring for anomalies | RT-001, RT-002 |
| CC8.1 | Change management | CF-001, CF-002 |

## Evidence Format

Each test produces evidence in this format:

```json
{
  "test_id": "RT-001",
  "test_name": "Rate limiting enforces free tier (5 req/min)",
  "timestamp": "2025-12-12T06:00:00Z",
  "result": "PASS",
  "control_mapping": ["CC6.1", "CC6.3", "CC7.2"],
  "duration_ms": 1234,
  "details": {
    "tier": "free_trial",
    "expected_limit": 5,
    "success_count": 5,
    "rate_limited_count": 3
  },
  "artifacts": [...]
}
```

## Related Projects

- [kong-rate-limiting-demo](https://github.com/RiskResponse/kong-rate-limiting-demo) - Kong Gateway demo this tests against

## License

MIT

