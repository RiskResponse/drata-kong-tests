# Drata Kong Tests - Project Status & TODO

*Last updated: December 12, 2025*

## Project Summary

Automated compliance tests for Kong Gateway that push evidence to Drata for SOC 2. Built as a Cloud Run Job triggered daily by Cloud Scheduler.

**Repos:**
- This repo: https://github.com/RiskResponse/drata-kong-tests
- Kong demo: https://github.com/RiskResponse/kong-rate-limiting-demo

**GCP Projects:**
- Kong demo: `hybrid-kong-demo2`
- This project: `drata-kong-tests`

---

## Current Status

### Completed ✅

- [x] Project scaffolding (Python, Dockerfile, requirements.txt)
- [x] Configuration management (src/config.py)
- [x] Base test class with evidence schema (src/tests/base.py)
- [x] Kong clients (Konnect Admin API + Dataplane)
- [x] Runtime tests (RT-001 to RT-006)
- [x] Configuration tests (CF-001 to CF-003)
- [x] Drata API client (with dry-run mock)
- [x] Main entry point (src/main.py)
- [x] Terraform for Cloud Run Job + Scheduler
- [x] Deployment scripts (deploy.sh, run-local.sh, trigger.sh)
- [x] README documentation
- [x] Local testing validated (9/9 tests passing)
- [x] Pushed to GitHub

### In Progress 🔄

- [ ] Drata API verification (need API key to confirm exact endpoints)

### TODO 📋

1. **Get Drata API key**
   - Log in to Drata → Settings → API Keys
   - Create key with appropriate scopes
   - Note exact endpoint patterns from developer docs

2. **Verify Drata API endpoints**
   - The current client uses assumed endpoints
   - May need to adjust based on actual API structure
   - Key endpoints to verify:
     - Evidence submission
     - Monitor updates
     - Control mapping

3. **Deploy to GCP**
   ```bash
   cd drata-kong-tests
   
   # Edit terraform.tfvars with your values
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit dataplane_url and other values
   
   # Deploy
   cd ..
   ./scripts/deploy.sh
   ```

4. **Add secrets to GCP**
   ```bash
   # Kong Konnect token
   echo -n 'kpat_xxx' | gcloud secrets versions add konnect-token --data-file=-
   
   # Drata API key
   echo -n 'drata_xxx' | gcloud secrets versions add drata-api-key --data-file=-
   ```

5. **Test Cloud Run Job**
   ```bash
   ./scripts/trigger.sh
   ```

6. **Map tests to Drata controls/monitors**
   - Create monitors in Drata for each test
   - Update test_id → monitor_id mapping in code

7. **Write article**
   - Document the approach
   - Show evidence appearing in Drata
   - Explain SOC 2 control mapping

---

## Test Catalog

| Test ID | Name | SOC 2 Controls | Status |
|---------|------|----------------|--------|
| RT-001 | Rate limit free tier (5/min) | CC6.1, CC6.3, CC7.2 | ✅ Passing |
| RT-002 | Rate limit pro tier (60/min) | CC6.1, CC6.3, CC7.2 | ✅ Passing |
| RT-003 | Invalid key rejected | CC6.1, CC6.6 | ✅ Passing |
| RT-004 | Missing key rejected | CC6.1, CC6.6 | ✅ Passing |
| RT-005 | Valid key accepted | CC6.1 | ✅ Passing |
| RT-006 | Consumer identity injected | CC6.1, CC6.3 | ✅ Passing |
| CF-001 | Auth plugin enabled | CC6.1, CC8.1 | ✅ Passing |
| CF-002 | Rate limit plugin enabled | CC6.1, CC6.3, CC8.1 | ✅ Passing |
| CF-003 | All consumers have limits | CC6.2, CC6.3 | ✅ Passing |

---

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, orchestrates tests |
| `src/tests/runtime.py` | RT-001 to RT-006 |
| `src/tests/configuration.py` | CF-001 to CF-003 |
| `src/clients/kong.py` | Konnect + Dataplane clients |
| `src/clients/drata.py` | Drata API client |
| `terraform/main.tf` | Cloud Run Job + Scheduler |
| `scripts/deploy.sh` | Full deployment |
| `scripts/run-local.sh` | Local testing |

---

## Environment Variables

```bash
# Required
KONNECT_TOKEN=kpat_xxx
DATAPLANE_URL=https://kong-dataplane-xxx.run.app
DRATA_API_KEY=xxx

# Optional (have defaults)
KONNECT_REGION=us
CONTROL_PLANE_NAME=kong-hybrid-rate-limit-demo
FREE_TRIAL_KEY=free-trial-key
PRO_KEY=pro-key
```

---

## Quick Commands

```bash
# Run tests locally (dry-run)
source venv/bin/activate
./scripts/run-local.sh --dry-run

# Deploy to GCP
./scripts/deploy.sh

# Manual trigger
./scripts/trigger.sh

# View logs
gcloud run jobs executions list --job drata-kong-tests --region us-east1
```

---

## Related Context

This project was created as part of a GRC engineering demo showing:
1. API rate limiting as a SOC 2 control
2. Kong hybrid deployment on GCP
3. Automated compliance evidence collection
4. Integration with Drata for continuous compliance

See the X thread and LinkedIn post for the full GRC engineering approach.

