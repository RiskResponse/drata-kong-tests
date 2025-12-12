#!/bin/bash
#
# Run Drata Kong Tests locally
#
# Usage:
#   ./scripts/run-local.sh                    # Run tests
#   ./scripts/run-local.sh --dry-run          # Dry run (no Drata push)
#   ./scripts/run-local.sh --verbose          # Verbose output

set -euo pipefail

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables from .env if it exists
if [[ -f .env ]]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
fi

# Check required environment variables
required_vars=(
    "KONNECT_TOKEN"
    "DATAPLANE_URL"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "Error: Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Create a .env file from .env.example and fill in the values."
    exit 1
fi

# Default to dry-run if no Drata key
if [[ -z "${DRATA_API_KEY:-}" ]]; then
    echo "Warning: DRATA_API_KEY not set. Running in dry-run mode."
    set -- "$@" --dry-run
fi

# Run the tests
echo "Running Drata Kong Tests..."
echo ""

python -m src.main "$@"

