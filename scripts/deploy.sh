#!/bin/bash
#
# Deploy Drata Kong Tests to GCP
#
# This script:
# 1. Builds and pushes Docker image
# 2. Creates secrets in Secret Manager (if not exist)
# 3. Deploys Cloud Run Job and Scheduler via Terraform
#
# Usage:
#   ./scripts/deploy.sh
#   ./scripts/deploy.sh --skip-build
#   ./scripts/deploy.sh --skip-terraform

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-drata-kong-tests}"
REGION="${GCP_REGION:-us-east1}"
JOB_NAME="${JOB_NAME:-drata-kong-tests}"

# Parse arguments
SKIP_BUILD=false
SKIP_TERRAFORM=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-build) SKIP_BUILD=true; shift ;;
        --skip-terraform) SKIP_TERRAFORM=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--skip-build] [--skip-terraform]"
            exit 0
            ;;
        *) log_error "Unknown argument: $1"; exit 1 ;;
    esac
done

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

log_info "Deploying Drata Kong Tests"
log_info "Project: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Job Name: $JOB_NAME"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
log_info "Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    --quiet

# Build and push Docker image
if [[ "$SKIP_BUILD" == "false" ]]; then
    log_info "Building Docker image..."
    gcloud auth configure-docker --quiet
    
    docker build --platform linux/amd64 -t "gcr.io/${PROJECT_ID}/${JOB_NAME}:latest" .
    
    log_info "Pushing Docker image..."
    docker push "gcr.io/${PROJECT_ID}/${JOB_NAME}:latest"
    
    log_success "Docker image pushed"
else
    log_warning "Skipping Docker build"
fi

# Create secrets if they don't exist
log_info "Checking secrets..."

create_secret_if_missing() {
    local secret_name=$1
    local description=$2
    
    if ! gcloud secrets describe "$secret_name" --quiet 2>/dev/null; then
        log_info "Creating secret: $secret_name"
        echo -n "placeholder" | gcloud secrets create "$secret_name" \
            --replication-policy="user-managed" \
            --locations="$REGION" \
            --data-file=-
        log_warning "Secret '$secret_name' created with placeholder. Update it with:"
        log_warning "  echo -n 'YOUR_VALUE' | gcloud secrets versions add $secret_name --data-file=-"
    else
        log_info "Secret '$secret_name' already exists"
    fi
}

create_secret_if_missing "konnect-token" "Kong Konnect API token"
create_secret_if_missing "drata-api-key" "Drata API key"

# Deploy with Terraform
if [[ "$SKIP_TERRAFORM" == "false" ]]; then
    log_info "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init -upgrade
    
    # Check if tfvars exists
    if [[ ! -f "terraform.tfvars" ]]; then
        log_warning "terraform.tfvars not found. Creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        log_warning "Please edit terraform/terraform.tfvars with your values"
    fi
    
    # Plan and apply
    terraform plan -out=tfplan
    terraform apply tfplan
    
    cd ..
    
    log_success "Terraform deployment complete"
else
    log_warning "Skipping Terraform deployment"
fi

echo ""
log_success "Deployment complete!"
echo ""
log_info "Next steps:"
log_info "1. Update secrets with real values:"
log_info "   echo -n 'kpat_xxx' | gcloud secrets versions add konnect-token --data-file=-"
log_info "   echo -n 'drata_xxx' | gcloud secrets versions add drata-api-key --data-file=-"
echo ""
log_info "2. Trigger a test run:"
log_info "   gcloud run jobs execute $JOB_NAME --region $REGION"
echo ""
log_info "3. View logs:"
log_info "   gcloud run jobs executions list --job $JOB_NAME --region $REGION"

