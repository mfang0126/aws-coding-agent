#!/bin/bash
# Automated deployment script for AWS BedrockAgentCore coding agent
# Usage: ./scripts/deploy.sh [--skip-provider] [--skip-role]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_NAME="coding-agent"
RUNTIME_NAME="coding-agent-production"
ROLE_NAME="AgentCoreRuntimeRole"
POLICY_NAME="AgentCoreRuntimePolicy"
PROVIDER_NAME="github-provider"
WORKLOAD_NAME="coding-agent-workload"

# Parse command line arguments
SKIP_PROVIDER=false
SKIP_ROLE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-provider)
      SKIP_PROVIDER=true
      shift
      ;;
    --skip-role)
      SKIP_ROLE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--skip-provider] [--skip-role] [--dry-run]"
      exit 1
      ;;
  esac
done

# Helper functions
print_step() {
  echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ${NC}  $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

check_prerequisites() {
  print_step "Checking prerequisites..."

  # Check AWS CLI
  if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it first."
    exit 1
  fi
  print_success "AWS CLI installed"

  # Check Python
  if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
  fi
  print_success "Python installed"

  # Check uv
  if ! command -v uv &> /dev/null; then
    print_error "uv not found. Please install: pip install uv"
    exit 1
  fi
  print_success "uv package manager installed"

  # Check .env file
  if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_error ".env file not found. Please copy .env.example and configure it."
    exit 1
  fi
  print_success ".env file found"

  # Load environment variables
  source "$PROJECT_ROOT/.env"

  # Verify required variables
  if [ -z "$AWS_REGION" ] || [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    print_error "Missing required environment variables in .env"
    print_info "Required: AWS_REGION, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET"
    exit 1
  fi
  print_success "Environment variables configured"

  # Check AWS credentials
  if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or expired"
    print_info "Run: aws sso login --profile ${AWS_PROFILE:-default}"
    exit 1
  fi

  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  print_success "AWS credentials valid (Account: $ACCOUNT_ID)"

  echo ""
}

create_iam_role() {
  if [ "$SKIP_ROLE" = true ]; then
    print_warning "Skipping IAM role creation (--skip-role flag)"
    return
  fi

  print_step "Creating IAM role and policies..."

  # Check if role exists
  if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    print_warning "IAM role $ROLE_NAME already exists, skipping creation"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    print_info "Using existing role: $ROLE_ARN"
    echo ""
    return
  fi

  # Create trust policy
  cat > /tmp/trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  # Create role
  print_info "Creating IAM role: $ROLE_NAME"
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --description "Execution role for AgentCore coding agent runtime" \
    > /dev/null

  print_success "IAM role created"

  # Create permissions policy
  cat > /tmp/runtime-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:${AWS_REGION}::foundation-model/anthropic.claude-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock/agentcore/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore-control:GetOAuth2CredentialProvider"
      ],
      "Resource": "*"
    }
  ]
}
EOF

  # Create policy
  print_info "Creating IAM policy: $POLICY_NAME"
  POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file:///tmp/runtime-policy.json \
    --query 'Policy.Arn' \
    --output text)

  print_success "IAM policy created: $POLICY_ARN"

  # Attach policy to role
  print_info "Attaching policy to role"
  aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

  print_success "Policy attached to role"

  # Get role ARN
  ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
  print_info "Role ARN: $ROLE_ARN"

  # Wait for role propagation
  print_info "Waiting for IAM role propagation (10 seconds)..."
  sleep 10

  echo ""
}

create_oauth_provider() {
  if [ "$SKIP_PROVIDER" = true ]; then
    print_warning "Skipping OAuth provider creation (--skip-provider flag)"
    return
  fi

  print_step "Creating GitHub OAuth provider..."

  # Run setup script
  cd "$PROJECT_ROOT"
  export AWS_PROFILE=${AWS_PROFILE:-default}
  export AWS_REGION=${AWS_REGION}

  if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN: Would create OAuth provider"
  else
    print_info "Running OAuth provider setup..."
    uv run python -m src.auth.setup_provider
  fi

  echo ""
}

configure_agentcore_yaml() {
  print_step "Configuring .bedrock_agentcore.yaml..."

  # Get role ARN
  ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

  if [ -z "$ROLE_ARN" ]; then
    print_error "IAM role not found. Run without --skip-role first."
    exit 1
  fi

  # Create configuration
  cat > "$PROJECT_ROOT/.bedrock_agentcore.yaml" <<EOF
agent_name: ${AGENT_NAME}
region: ${AWS_REGION}

runtime:
  entrypoint: src.agent.runtime
  python_version: "3.11"
  role_arn: ${ROLE_ARN}

oauth_configuration:
  workload_name: ${WORKLOAD_NAME}
  credential_providers:
    - ${PROVIDER_NAME}

environment_variables:
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  MODEL_ID: ${MODEL_ID:-anthropic.claude-sonnet-4.5}
  GITHUB_PROVIDER_NAME: ${PROVIDER_NAME}
  OAUTH_WORKLOAD_NAME: ${WORKLOAD_NAME}

# Resource configuration
resources:
  memory: 2048
  cpu: 1024
EOF

  print_success "Configuration file created"
  print_info "Location: $PROJECT_ROOT/.bedrock_agentcore.yaml"
  echo ""
}

deploy_runtime() {
  print_step "Deploying agent runtime..."

  cd "$PROJECT_ROOT"

  # Check if toolkit is available
  if command -v agentcore &> /dev/null; then
    print_info "Using AgentCore toolkit for deployment"

    if [ "$DRY_RUN" = true ]; then
      print_info "DRY RUN: Would configure and deploy runtime"
    else
      # Configure agent
      print_info "Configuring agent..."
      agentcore configure \
        -e src.agent.runtime \
        -n "$AGENT_NAME" \
        --protocol MCP \
        --region "$AWS_REGION"

      # Create runtime
      print_info "Creating runtime: $RUNTIME_NAME"
      ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

      agentcore runtime create \
        -a "$AGENT_NAME" \
        --runtime-name "$RUNTIME_NAME" \
        --role-arn "$ROLE_ARN"
    fi
  else
    print_warning "AgentCore toolkit not found"
    print_info "Install: uv pip install bedrock-agentcore-starter-toolkit"
    print_info "Or deploy manually using AWS CLI (see DEPLOYMENT.md)"
  fi

  echo ""
}

verify_deployment() {
  print_step "Verifying deployment..."

  # Check OAuth provider
  if aws bedrock-agentcore-control list-oauth2-credential-providers \
     --region "$AWS_REGION" 2>/dev/null | grep -q "$PROVIDER_NAME"; then
    print_success "OAuth provider exists: $PROVIDER_NAME"
  else
    print_warning "OAuth provider not found: $PROVIDER_NAME"
  fi

  # Check IAM role
  if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    print_success "IAM role exists: $ROLE_NAME"
  else
    print_warning "IAM role not found: $ROLE_NAME"
  fi

  # Check runtime
  if aws bedrock-agentcore-control list-agent-runtimes \
     --region "$AWS_REGION" 2>/dev/null | grep -q "$RUNTIME_NAME"; then
    print_success "Agent runtime deployed: $RUNTIME_NAME"

    # Get runtime ARN
    RUNTIME_ARN=$(aws bedrock-agentcore-control list-agent-runtimes \
      --region "$AWS_REGION" \
      | jq -r ".agentRuntimes[] | select(.agentRuntimeName==\"$RUNTIME_NAME\") | .agentRuntimeArn")

    print_info "Runtime ARN: $RUNTIME_ARN"
  else
    print_warning "Agent runtime not found: $RUNTIME_NAME"
    print_info "You may need to deploy manually (see DEPLOYMENT.md)"
  fi

  echo ""
}

show_next_steps() {
  print_step "Deployment Summary"
  echo ""
  echo "Resources created:"
  echo "  • IAM Role: $ROLE_NAME"
  echo "  • OAuth Provider: $PROVIDER_NAME"
  echo "  • Agent Runtime: $RUNTIME_NAME"
  echo ""
  echo "Next steps:"
  echo "  1. Update GitHub OAuth app callback URL (check setup output above)"
  echo "  2. Test the agent:"
  echo "     aws bedrock-agentcore invoke-agent-runtime \\"
  echo "       --region $AWS_REGION \\"
  echo "       --agent-runtime-arn <RUNTIME_ARN> \\"
  echo "       --payload fileb://test-request.json \\"
  echo "       output.json"
  echo ""
  echo "  3. View logs:"
  echo "     aws logs tail /aws/bedrock/agentcore/$RUNTIME_NAME \\"
  echo "       --region $AWS_REGION --follow"
  echo ""
  echo "Documentation: docs/DEPLOYMENT.md"
  echo ""
}

# Main execution
main() {
  echo ""
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║  AWS BedrockAgentCore Deployment Script                   ║"
  echo "║  Coding Agent with GitHub OAuth Integration                ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""

  check_prerequisites
  create_iam_role
  create_oauth_provider
  configure_agentcore_yaml
  deploy_runtime
  verify_deployment
  show_next_steps

  print_success "Deployment complete!"
  echo ""
}

# Run main function
main
