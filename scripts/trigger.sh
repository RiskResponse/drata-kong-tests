#!/bin/bash
#
# Manually trigger the Drata Kong Tests Cloud Run Job
#
# Usage:
#   ./scripts/trigger.sh
#   ./scripts/trigger.sh --wait    # Wait for completion

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-drata-kong-tests}"
REGION="${GCP_REGION:-us-east1}"
JOB_NAME="${JOB_NAME:-drata-kong-tests}"

echo "Triggering $JOB_NAME..."

# Trigger the job
EXECUTION_NAME=$(gcloud run jobs execute "$JOB_NAME" \
    --region "$REGION" \
    --format="value(metadata.name)" \
    2>&1 | grep -o 'Execution .* has started' | awk '{print $2}' || true)

if [[ -z "$EXECUTION_NAME" ]]; then
    # Fallback: just run the command
    gcloud run jobs execute "$JOB_NAME" --region "$REGION"
    echo ""
    echo "Job triggered. View status with:"
    echo "  gcloud run jobs executions list --job $JOB_NAME --region $REGION"
else
    echo "Execution started: $EXECUTION_NAME"
    
    if [[ "${1:-}" == "--wait" ]]; then
        echo "Waiting for completion..."
        
        while true; do
            STATUS=$(gcloud run jobs executions describe "$EXECUTION_NAME" \
                --job "$JOB_NAME" \
                --region "$REGION" \
                --format="value(status.completionTime)" 2>/dev/null || echo "")
            
            if [[ -n "$STATUS" ]]; then
                echo "Completed at: $STATUS"
                break
            fi
            
            echo "Still running..."
            sleep 10
        done
        
        # Show logs
        echo ""
        echo "Logs:"
        gcloud run jobs executions logs "$EXECUTION_NAME" \
            --job "$JOB_NAME" \
            --region "$REGION" \
            --limit 50
    fi
fi

