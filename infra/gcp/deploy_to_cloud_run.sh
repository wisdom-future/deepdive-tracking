#!/bin/bash
#
# Deploy DeepDive Tracking application to Google Cloud Run
#
# Usage:
#   ./scripts/deploy_to_cloud_run.sh [OPTIONS]
#
# Options:
#   --help              Show this help message
#   --dry-run           Print commands without executing
#   --skip-build        Skip Docker build and use existing image
#   --project-id ID     GCP project ID (default: deepdive-engine)
#   --region REGION     GCP region (default: asia-east1)
#   --service-name NAME Cloud Run service name (default: deepdive-tracking)
#
# Environment Variables:
#   GCP_PROJECT_ID              Google Cloud project ID
#   GCP_REGION                  GCP region for deployment
#   CLOUD_RUN_SERVICE_NAME      Cloud Run service name
#

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="${GCP_PROJECT_ID:-deepdive-engine}"
REGION="${GCP_REGION:-asia-east1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-deepdive-tracking}"
DRY_RUN=false
SKIP_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            grep "^#" "$0" | sed 's/^#[[:space:]]*//g'
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}$(printf '=%.0s' {1..70})${NC}"
    echo -e "${BLUE}${1}${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..70})${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

run_command() {
    local description="$1"
    shift
    local command=("$@")

    print_info "$description"
    echo "Command: ${command[*]}"

    if [[ "$DRY_RUN" == true ]]; then
        echo "(DRY-RUN MODE: Not executing)"
        return 0
    fi

    if "${command[@]}"; then
        print_success "$description completed"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

# Main deployment workflow
main() {
    print_header "🚀 DEEPDIVE TRACKING - CLOUD RUN DEPLOYMENT"
    echo "Project ID:   $PROJECT_ID"
    echo "Region:       $REGION"
    echo "Service:      $SERVICE_NAME"
    echo "Mode:         $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'NORMAL')"

    # Step 1: Verify GCP Setup
    print_header "🔍 Verifying GCP Setup"

    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK"
        return 1
    fi
    print_success "gcloud CLI is installed"

    # Set GCP project
    if [[ "$DRY_RUN" == false ]]; then
        print_info "Setting GCP project to $PROJECT_ID"
        gcloud config set project "$PROJECT_ID" --quiet
    fi
    print_success "GCP project configured: $PROJECT_ID"

    # Step 2: Verify Cloud Run API
    print_header "✓ Cloud Run API Status"

    if [[ "$DRY_RUN" == false ]]; then
        if ! gcloud services list --enabled --filter="name:run.googleapis.com" --format=value 2>/dev/null | grep -q "run.googleapis.com"; then
            print_warning "Cloud Run API is not enabled. Enabling..."
            if ! gcloud services enable run.googleapis.com --quiet; then
                print_error "Failed to enable Cloud Run API"
                return 1
            fi
        fi
    fi
    print_success "Cloud Run API is enabled"

    # Step 3: Deploy to Cloud Run
    print_header "🚀 Deploying to Cloud Run"

    local deploy_cmd=(
        "gcloud" "run" "deploy" "$SERVICE_NAME"
        "--source" "."
        "--platform" "managed"
        "--region" "$REGION"
        "--memory" "1Gi"
        "--cpu" "1"
        "--timeout" "900"
        "--allow-unauthenticated"
        "--set-env-vars" "DATABASE_URL=postgresql://deepdive_user:deepdive_password@/deepdive_db"
        "--set-env-vars" "CLOUDSQL_USER=deepdive_user"
        "--set-env-vars" "CLOUDSQL_PASSWORD=deepdive_password"
        "--set-env-vars" "CLOUDSQL_DATABASE=deepdive_db"
        "--set-env-vars" "REDIS_URL=redis://10.240.18.115:6379/0"
        "--set-env-vars" "CELERY_BROKER_URL=redis://10.240.18.115:6379/1"
        "--set-env-vars" "CELERY_RESULT_BACKEND=redis://10.240.18.115:6379/2"
        "--set-env-vars" "APP_ENV=production"
        "--set-env-vars" "DEBUG=False"
        "--set-env-vars" "LOG_LEVEL=INFO"
        "--set-env-vars" "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
        "--service-account" "726493701291-compute@developer.gserviceaccount.com"
    )

    if [[ "$SKIP_BUILD" == true ]]; then
        deploy_cmd+=("--image" "gcr.io/${PROJECT_ID}/${SERVICE_NAME}")
    fi

    if ! run_command "Deploy $SERVICE_NAME to Cloud Run" "${deploy_cmd[@]}"; then
        print_error "Cloud Run deployment failed"
        return 1
    fi

    # Step 4: Verify Deployment
    print_header "🔍 Verifying Deployment"

    if [[ "$DRY_RUN" == false ]]; then
        local service_url
        service_url=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)' 2>/dev/null || echo "")

        if [[ -n "$service_url" ]]; then
            print_success "Service deployed successfully!"
            print_info "Service URL: $service_url"
        else
            print_warning "Cannot verify service deployment"
        fi
    else
        print_info "Service URL (DRY-RUN): https://${SERVICE_NAME}-XXXXX.${REGION}.run.app"
    fi

    # Print next steps
    print_header "✓ DEPLOYMENT COMPLETED SUCCESSFULLY"
    echo ""
    echo "Next steps:"
    echo "1. Initialize database tables:"
    echo "   python scripts/init_publish_priorities.py"
    echo ""
    echo "2. Test the deployment:"
    echo "   python scripts/run_priority_publishing_test.py 3 --dry-run"
    echo ""
    echo "3. View deployment status:"
    echo "   gcloud run services describe $SERVICE_NAME --region $REGION"
    echo ""
    echo "4. View service logs:"
    echo "   gcloud run services describe $SERVICE_NAME --region $REGION"
    echo ""

    return 0
}

# Run main function
if main; then
    exit 0
else
    exit 1
fi
