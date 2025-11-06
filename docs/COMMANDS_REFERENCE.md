# Commands Reference Card

Quick copy-paste commands for AWS BedrockAgentCore deployment.

## Prerequisites Setup

### 1. Verify Tools
```bash
aws --version        # AWS CLI v2 required
python --version     # Python 3.11+ required
uv --version         # uv package manager required
```

### 2. Set AWS Credentials
```bash
export AWS_PROFILE=mingfang
export AWS_REGION=ap-southeast-2

# Verify credentials
aws sts get-caller-identity
```

### 3. Configure Environment
```bash
cd /Users/freedom/ai/aws-coding-agent

# Create .env
cp .env.example .env

# Edit with your GitHub OAuth credentials
nano .env
```

## One-Command Deployment

```bash
# Deploy everything automatically
make deploy
```

## Step-by-Step Manual Commands

### Step 1: Create IAM Role
```bash
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
aws iam create-role \
  --role-name AgentCoreRuntimeRole \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --description "Execution role for AgentCore coding agent runtime"

# Create permissions policy
cat > /tmp/runtime-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-southeast-2:670326884047:log-group:/aws/bedrock/agentcore/*"
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
aws iam create-policy \
  --policy-name AgentCoreRuntimePolicy \
  --policy-document file:///tmp/runtime-policy.json

# Attach policy to role
aws iam attach-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

# Verify
aws iam get-role --role-name AgentCoreRuntimeRole --query 'Role.Arn' --output text
```

### Step 2: Create OAuth Provider
```bash
# Run setup script
make setup-github

# Or manually with Python
cd /Users/freedom/ai/aws-coding-agent
export AWS_PROFILE=mingfang AWS_REGION=ap-southeast-2
uv run python -m src.auth.setup_provider
```

### Step 3: Update GitHub OAuth App
```bash
# Get callback URL from setup-github output
# Example: https://bedrock-agentcore-identity.ap-southeast-2.amazonaws.com/oauth/callback

# Open GitHub OAuth app settings
open https://github.com/settings/developers

# Add callback URL to your OAuth app
# Save changes
```

### Step 4: Deploy Runtime
```bash
# Option A: Using AgentCore toolkit (recommended)
cd /Users/freedom/ai/aws-coding-agent
agentcore configure \
  -e src.runtime \
  -n coding-agent \
  --protocol MCP \
  --region ap-southeast-2

agentcore runtime create \
  -a coding-agent \
  --runtime-name coding-agent-production \
  --role-arn arn:aws:iam::670326884047:role/AgentCoreRuntimeRole

# Option B: Using AWS CLI directly
# (See docs/DEPLOYMENT.md for AWS CLI approach)
```

## Testing Commands

### Run Automated Tests
```bash
make test-runtime
```

### Manual Runtime Invocation
```bash
# Create test payload
cat > /tmp/test.json <<'EOF'
{
  "inputText": "List my GitHub repositories",
  "sessionId": "test-001"
}
EOF

# Get runtime ARN
RUNTIME_ARN=$(aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production") | .agentRuntimeArn')

echo "Runtime ARN: $RUNTIME_ARN"

# Invoke runtime
aws bedrock-agentcore invoke-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-arn "$RUNTIME_ARN" \
  --payload fileb:///tmp/test.json \
  /tmp/output.json

# View response
cat /tmp/output.json | jq
```

## Monitoring Commands

### View CloudWatch Logs
```bash
# Tail logs in real-time
make logs

# Or use AWS CLI
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --follow --format short

# View last 30 minutes
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --since 30m
```

### Check Resource Status
```bash
# Check runtime status
aws bedrock-agentcore-control get-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production \
  | jq -r '{name: .agentRuntimeName, status: .status, arn: .agentRuntimeArn}'

# List all runtimes
aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | {name: .agentRuntimeName, status: .status}'

# List OAuth providers
aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2 \
  | jq -r '.credentialProviders[] | {name: .name, arn: .credentialProviderArn}'

# Check IAM role
aws iam get-role --role-name AgentCoreRuntimeRole \
  | jq -r '{name: .Role.RoleName, arn: .Role.Arn}'
```

## Debugging Commands

### Check AWS Credentials
```bash
# Verify current identity
aws sts get-caller-identity

# Check AWS configuration
aws configure list

# Re-authenticate
aws sso login --profile mingfang
```

### Verify Environment
```bash
# Check .env file
cat /Users/freedom/ai/aws-coding-agent/.env

# Verify environment variables are loaded
cd /Users/freedom/ai/aws-coding-agent
source .env
echo "Region: $AWS_REGION"
echo "Profile: $AWS_PROFILE"
echo "Client ID: ${GITHUB_CLIENT_ID:0:10}..."  # First 10 chars only
```

### Test Local Agent
```bash
# Test runtime import
cd /Users/freedom/ai/aws-coding-agent
python3 -c "from src.runtime import agent; print(agent)"

# Start local server
make dev

# Test local health endpoint
curl -s http://localhost:8000/health | python -m json.tool
```

### View Error Logs
```bash
# Filter for ERROR level logs
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --since 1h \
  --filter-pattern "ERROR"

# View logs from specific time
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --since "2025-10-30T10:00:00Z" \
  --format short
```

## Update & Redeploy Commands

### Update Code and Redeploy
```bash
cd /Users/freedom/ai/aws-coding-agent

# Pull latest changes
git pull

# Run tests locally
make test

# Redeploy (skip provider and role creation)
make deploy-fast

# Or update runtime manually
agentcore runtime update \
  --runtime-name coding-agent-production
```

### Update OAuth Provider
```bash
# Delete existing provider
aws bedrock-agentcore-control delete-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider

# Wait a few seconds
sleep 5

# Recreate provider
make setup-github
```

### Update IAM Permissions
```bash
# Update policy document
cat > /tmp/updated-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    ... your updated policy ...
  ]
}
EOF

# Create new policy version
aws iam create-policy-version \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy \
  --policy-document file:///tmp/updated-policy.json \
  --set-as-default
```

## Cleanup Commands

### Remove All Resources
```bash
# WARNING: This deletes everything!

# Delete runtime
aws bedrock-agentcore-control delete-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production

# Delete OAuth provider
aws bedrock-agentcore-control delete-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider

# Detach IAM policy
aws iam detach-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

# Delete IAM policy
aws iam delete-policy \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

# Delete IAM role
aws iam delete-role --role-name AgentCoreRuntimeRole

# Delete CloudWatch log group
aws logs delete-log-group \
  --log-group-name /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2
```

### Partial Cleanup
```bash
# Delete only runtime (keep IAM and OAuth)
aws bedrock-agentcore-control delete-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production

# Delete only OAuth provider (keep IAM and runtime)
aws bedrock-agentcore-control delete-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider
```

## Utility Commands

### List All AgentCore Resources
```bash
# Gateways
aws bedrock-agentcore-control list-gateways \
  --region ap-southeast-2 \
  | jq -r '.gateways[] | {id: .gatewayId, url: .gatewayUrl, status: .gatewayStatus}'

# Runtimes
aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | {name: .agentRuntimeName, arn: .agentRuntimeArn, status: .status}'

# OAuth Providers
aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2 \
  | jq -r '.credentialProviders[] | {name: .name, arn: .credentialProviderArn}'

# Memories
aws bedrock-agentcore-control list-agent-memories \
  --region ap-southeast-2 \
  | jq -r '.agentMemories[] | {name: .memoryName, id: .memoryId}'
```

### Export Configuration
```bash
# Export runtime ARN
export RUNTIME_ARN=$(aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production") | .agentRuntimeArn')

echo "RUNTIME_ARN=$RUNTIME_ARN"

# Export OAuth provider ARN
export PROVIDER_ARN=$(aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2 \
  | jq -r '.credentialProviders[] | select(.name=="github-provider") | .credentialProviderArn')

echo "PROVIDER_ARN=$PROVIDER_ARN"
```

### Set Log Retention
```bash
# Set 7-day retention
aws logs put-retention-policy \
  --log-group-name /aws/bedrock/agentcore/coding-agent-production \
  --retention-in-days 7 \
  --region ap-southeast-2

# Remove retention (keep forever)
aws logs delete-retention-policy \
  --log-group-name /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2
```

## Make Commands Summary

```bash
# Development
make dev              # Start local development server
make start            # Start production server locally
make test             # Run pytest tests
make test-cov         # Run tests with coverage
make lint             # Check code quality
make format           # Format code

# Setup & Deployment
make setup-github     # Create OAuth provider only
make deploy           # Full deployment (IAM + OAuth + Runtime)
make deploy-fast      # Redeploy (skip provider and role)

# Testing & Monitoring
make test-runtime     # Test deployed runtime
make logs             # Tail CloudWatch logs
make health           # Check local server health
```

## Environment Variables

```bash
# Required in .env
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=9e32c1...
MODEL_ID=anthropic.claude-sonnet-4.5
LOG_LEVEL=INFO
GITHUB_PROVIDER_NAME=github-provider
OAUTH_WORKLOAD_NAME=coding-agent-workload

# Runtime environment (auto-configured)
LOG_LEVEL                  # INFO, DEBUG, WARNING, ERROR
MODEL_ID                   # anthropic.claude-sonnet-4.5
GITHUB_PROVIDER_NAME       # github-provider
OAUTH_WORKLOAD_NAME        # coding-agent-workload
```

## Quick Troubleshooting

```bash
# Check if AWS credentials are valid
aws sts get-caller-identity || aws sso login --profile mingfang

# Check if IAM role exists
aws iam get-role --role-name AgentCoreRuntimeRole 2>/dev/null && echo "✓ Role exists" || echo "✗ Role missing"

# Check if OAuth provider exists
aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2 | grep -q github-provider && echo "✓ Provider exists" || echo "✗ Provider missing"

# Check if runtime exists
aws bedrock-agentcore-control list-agent-runtimes --region ap-southeast-2 | grep -q coding-agent-production && echo "✓ Runtime exists" || echo "✗ Runtime missing"

# View recent errors
aws logs tail /aws/bedrock/agentcore/coding-agent-production --region ap-southeast-2 --since 30m --filter-pattern "ERROR" 2>/dev/null || echo "No logs found"
```

---

**Tip**: Save this file as a reference and keep it open in a terminal window while deploying!
