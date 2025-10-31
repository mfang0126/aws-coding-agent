# AWS BedrockAgentCore Deployment Guide

Complete step-by-step guide to deploy the Python coding agent to AWS BedrockAgentCore with GitHub OAuth integration.

## Prerequisites

### Required Tools
```bash
# Verify installations
aws --version        # AWS CLI v2
python --version     # Python 3.11+
uv --version         # uv package manager
```

### AWS Setup
- **Account**: 670326884047
- **Region**: ap-southeast-2
- **Profile**: mingfang
- **Permissions**: AdministratorAccess (already confirmed)

### Required AWS Permissions
Your IAM role needs these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore-control:*",
        "bedrock-agentcore:*",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 1: Environment Configuration

### 1.1 Create .env File
```bash
cd /Users/freedom/ai/aws-coding-agent

# Create .env from template
cp .env.example .env
```

### 1.2 Configure GitHub OAuth App
1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in details:
   - **Application name**: AWS Coding Agent
   - **Homepage URL**: https://github.com/yourusername/aws-coding-agent
   - **Authorization callback URL**: (placeholder for now, will update after gateway creation)
   - **Description**: AI coding assistant with GitHub integration

4. Click "Register application"
5. Copy the **Client ID** and generate a **Client Secret**

### 1.3 Update .env File
```bash
# Edit .env
cat > .env <<'EOF'
# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang

# GitHub OAuth (from GitHub OAuth App)
GITHUB_CLIENT_ID=Ov23li...your_actual_client_id
GITHUB_CLIENT_SECRET=9e32c1...your_actual_client_secret

# Agent Configuration
MODEL_ID=anthropic.claude-sonnet-4.5
LOG_LEVEL=INFO

# OAuth Provider (default names)
GITHUB_PROVIDER_NAME=github-provider
OAUTH_WORKLOAD_NAME=coding-agent-workload
EOF
```

## Step 2: Create AgentCore IAM Role

The agent runtime needs an IAM role with permissions to invoke Bedrock models and access CloudWatch logs.

### 2.1 Create IAM Role
```bash
export AWS_PROFILE=mingfang
export AWS_REGION=ap-southeast-2

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

# Create the role
aws iam create-role \
  --role-name AgentCoreRuntimeRole \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --description "Execution role for AgentCore coding agent runtime"
```

### 2.2 Attach Permissions
```bash
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

# Create and attach the policy
aws iam create-policy \
  --policy-name AgentCoreRuntimePolicy \
  --policy-document file:///tmp/runtime-policy.json

# Attach policy to role
aws iam attach-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

# Verify role creation
aws iam get-role --role-name AgentCoreRuntimeRole --query 'Role.Arn' --output text
```

Expected output: `arn:aws:iam::670326884047:role/AgentCoreRuntimeRole`

## Step 3: Create GitHub OAuth Provider

This creates the OAuth2 credential provider in AgentCore Identity service.

### 3.1 Install Dependencies
```bash
cd /Users/freedom/ai/aws-coding-agent
uv sync
```

### 3.2 Run Provider Setup
```bash
# Set AWS profile
export AWS_PROFILE=mingfang
export AWS_REGION=ap-southeast-2

# Create OAuth provider
make setup-github
```

Expected output:
```
============================================================
✅ Created OAuth provider: arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:oauth2-credential-provider/github-provider
   Provider name: github-provider
   Vendor: GithubOauth2

============================================================
🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:
   https://bedrock-agentcore-identity.ap-southeast-2.amazonaws.com/oauth/callback

📝 Steps to register:
   1. Go to https://github.com/settings/developers
   2. Select your OAuth App
   3. Add the callback URL above to 'Authorization callback URL'
   4. Save changes
============================================================
```

### 3.3 Update GitHub OAuth App Callback URL
1. Go to https://github.com/settings/developers
2. Select your OAuth App
3. Update **Authorization callback URL** with the URL from the output above
4. Click "Update application"

### 3.4 Verify Provider
```bash
# List providers
aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2 \
  | jq -r '.credentialProviders[] | select(.name=="github-provider")'
```

## Step 4: Create Gateway (Optional)

If you need an HTTP gateway to access your agent:

### 4.1 Create Gateway
```bash
# Create MCP gateway
aws bedrock-agentcore-control create-gateway \
  --region ap-southeast-2 \
  --name coding-agent-gateway \
  --protocol-type MCP \
  --role-arn arn:aws:iam::670326884047:role/AgentCoreRuntimeRole \
  > /tmp/gateway.json

# Extract gateway details
jq -r '{gatewayId: .gatewayId, gatewayArn: .gatewayArn, gatewayUrl: .gatewayUrl, status: .gatewayStatus}' /tmp/gateway.json
```

Save the **gatewayUrl** for later use.

### 4.2 Create Gateway Target (Optional)
If you want to expose the agent via the gateway:

```bash
# Get gateway ID
GATEWAY_ID=$(jq -r '.gatewayId' /tmp/gateway.json)

# Create target pointing to your runtime (after runtime is created)
aws bedrock-agentcore-control create-gateway-target \
  --region ap-southeast-2 \
  --gateway-identifier "$GATEWAY_ID" \
  --name coding-agent-target \
  --target-configuration '{
    "agentRuntime": {
      "agentRuntimeArn": "AGENT_RUNTIME_ARN_FROM_STEP_5"
    }
  }'
```

## Step 5: Deploy Agent Runtime

### 5.1 Configure .bedrock_agentcore.yaml
```bash
# Copy template
cp .bedrock_agentcore.yaml.template .bedrock_agentcore.yaml

# Edit configuration
cat > .bedrock_agentcore.yaml <<'EOF'
agent_name: coding-agent
region: ap-southeast-2

runtime:
  entrypoint: src.runtime
  python_version: "3.11"
  role_arn: arn:aws:iam::670326884047:role/AgentCoreRuntimeRole

oauth_configuration:
  workload_name: coding-agent-workload
  credential_providers:
    - github-provider

environment_variables:
  LOG_LEVEL: INFO
  MODEL_ID: anthropic.claude-sonnet-4.5
  GITHUB_PROVIDER_NAME: github-provider
  OAUTH_WORKLOAD_NAME: coding-agent-workload

# Optional: Resource configuration
resources:
  memory: 2048
  cpu: 1024
EOF
```

### 5.2 Install AgentCore Toolkit (if not already installed)
```bash
uv pip install bedrock-agentcore-starter-toolkit
```

### 5.3 Deploy Runtime Using Toolkit
```bash
# Configure agent
agentcore configure \
  -e src.runtime \
  -n coding-agent \
  --protocol MCP \
  --region ap-southeast-2

# Create runtime
agentcore runtime create \
  -a coding-agent \
  --runtime-name coding-agent-production \
  --role-arn arn:aws:iam::670326884047:role/AgentCoreRuntimeRole
```

### 5.4 Alternative: Deploy Using AWS CLI Directly

If toolkit doesn't work, use AWS CLI:

```bash
# Package your code
zip -r agent.zip src/ pyproject.toml -x "*.pyc" -x "*__pycache__*"

# Create runtime (note: exact API may vary, check latest docs)
aws bedrock-agentcore-control create-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-name coding-agent-production \
  --agent-definition-config '{
    "pythonConfig": {
      "entrypoint": "src.runtime",
      "pythonVersion": "3.11",
      "packageLocation": "s3://your-bucket/agent.zip"
    }
  }' \
  --role-arn arn:aws:iam::670326884047:role/AgentCoreRuntimeRole \
  --environment-variables '{
    "LOG_LEVEL": "INFO",
    "MODEL_ID": "anthropic.claude-sonnet-4.5",
    "GITHUB_PROVIDER_NAME": "github-provider",
    "OAUTH_WORKLOAD_NAME": "coding-agent-workload"
  }' \
  > /tmp/runtime.json

# Save runtime ARN
jq -r '.agentRuntimeArn' /tmp/runtime.json
```

### 5.5 Verify Runtime Creation
```bash
# List runtimes
aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production")'
```

## Step 6: Test the Deployment

### 6.1 Create Test Payload
```bash
cat > /tmp/test-request.json <<'EOF'
{
  "inputText": "List my GitHub repositories",
  "sessionId": "test-session-001"
}
EOF
```

### 6.2 Invoke Runtime Directly
```bash
# Get runtime ARN from previous step
RUNTIME_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:agent-runtime/coding-agent-production"

# Invoke agent
aws bedrock-agentcore invoke-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-arn "$RUNTIME_ARN" \
  --payload fileb:///tmp/test-request.json \
  /tmp/response.json

# View response
jq -r '.' /tmp/response.json
```

### 6.3 Test via Gateway (if created)
```bash
GATEWAY_URL="https://your-gateway-id.agentcore.ap-southeast-2.amazonaws.com"

curl -X POST "$GATEWAY_URL/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @/tmp/test-request.json
```

## Step 7: Monitor and Debug

### 7.1 View CloudWatch Logs
```bash
# Find log group
aws logs describe-log-groups \
  --region ap-southeast-2 \
  --log-group-name-prefix /aws/bedrock/agentcore

# Tail logs
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --follow
```

### 7.2 Check Runtime Status
```bash
# Get runtime details
aws bedrock-agentcore-control get-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production \
  | jq -r '{name: .agentRuntimeName, status: .status, arn: .agentRuntimeArn}'
```

### 7.3 View Gateway Status
```bash
# Get gateway details
aws bedrock-agentcore-control get-gateway \
  --region ap-southeast-2 \
  --gateway-identifier "$GATEWAY_ID" \
  | jq -r '{url: .gatewayUrl, status: .gatewayStatus, protocol: .protocolType}'
```

## Troubleshooting Common Issues

### Issue 1: "UnrecognizedClientException"
**Problem**: Region or credentials mismatch

**Solution**:
```bash
# Verify AWS configuration
aws configure list
aws sts get-caller-identity

# Ensure environment variables are set
export AWS_PROFILE=mingfang
export AWS_REGION=ap-southeast-2
```

### Issue 2: "AccessDenied" on OAuth Provider Creation
**Problem**: Missing IAM permissions

**Solution**:
```bash
# Check your current IAM permissions
aws iam get-user --query 'User.Arn' --output text

# Verify you have bedrock-agentcore-control:* permissions
# If using SSO, ensure your session hasn't expired
aws sso login --profile mingfang
```

### Issue 3: "OAuth Provider Not Found" During Runtime Invocation
**Problem**: Runtime can't access the OAuth provider

**Solution**:
```bash
# Verify provider exists
aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2

# Check runtime role has permission to access provider
aws iam get-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-name AgentCoreRuntimePolicy
```

### Issue 4: "GitHub Bad Credentials"
**Problem**: OAuth flow fails or GitHub API returns 401

**Solution**:
```bash
# 1. Verify GitHub OAuth app configuration
# Go to https://github.com/settings/developers
# Check Client ID matches your .env

# 2. Verify callback URL is registered
# Should match the URL from setup-github output

# 3. Test OAuth provider directly
aws bedrock-agentcore-control get-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider
```

### Issue 5: Runtime Deployment Fails
**Problem**: Package upload or runtime creation errors

**Solution**:
```bash
# Check runtime logs
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --since 10m

# Verify entrypoint path
# Should be: src.runtime (matches file structure)

# Test locally first
cd /Users/freedom/ai/aws-coding-agent
python -c "from src.runtime import agent; print(agent)"
```

### Issue 6: "Module Not Found" in Runtime
**Problem**: Dependencies not installed correctly

**Solution**:
```bash
# Ensure all dependencies are in pyproject.toml
cat pyproject.toml

# Create a complete package with dependencies
pip install --target ./package -r <(python -m pip list --format=freeze)
zip -r agent-with-deps.zip package/ src/

# Redeploy runtime
```

## Security Best Practices

### Production Checklist
- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Use AWS Secrets Manager for GitHub OAuth credentials
- ✅ Rotate IAM role credentials regularly
- ✅ Enable CloudWatch logging for audit trails
- ✅ Use VPC endpoints for private access
- ✅ Implement rate limiting on gateway
- ✅ Monitor OAuth token usage
- ✅ Set up CloudWatch alarms for errors

### Secrets Management (Recommended for Production)
```bash
# Store GitHub credentials in Secrets Manager
aws secretsmanager create-secret \
  --name coding-agent/github-oauth \
  --secret-string '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }' \
  --region ap-southeast-2

# Update runtime to fetch from Secrets Manager
# Modify src/config.py to use boto3 to retrieve secrets
```

## Next Steps

### Integration Options
1. **API Gateway**: Expose agent via API Gateway for HTTP access
2. **Lambda Integration**: Trigger agent from Lambda functions
3. **EventBridge**: Schedule periodic agent tasks
4. **Step Functions**: Orchestrate multi-agent workflows

### Monitoring Setup
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name coding-agent-metrics \
  --dashboard-body file://cloudwatch-dashboard.json

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name coding-agent-errors \
  --alarm-description "Alert on runtime errors" \
  --metric-name Errors \
  --namespace AWS/BedrockAgentCore \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Quick Reference Commands

### Deploy New Version
```bash
cd /Users/freedom/ai/aws-coding-agent
export AWS_PROFILE=mingfang AWS_REGION=ap-southeast-2

# Update code
git pull

# Redeploy runtime
agentcore runtime update \
  --runtime-name coding-agent-production
```

### View Recent Logs
```bash
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --follow --format short
```

### List All Resources
```bash
# Gateways
aws bedrock-agentcore-control list-gateways --region ap-southeast-2

# Runtimes
aws bedrock-agentcore-control list-agent-runtimes --region ap-southeast-2

# OAuth Providers
aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2
```

### Cleanup (if needed)
```bash
# Delete runtime
aws bedrock-agentcore-control delete-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production

# Delete gateway
aws bedrock-agentcore-control delete-gateway \
  --region ap-southeast-2 \
  --gateway-identifier "$GATEWAY_ID"

# Delete OAuth provider
aws bedrock-agentcore-control delete-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider

# Delete IAM resources
aws iam detach-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

aws iam delete-policy \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy

aws iam delete-role --role-name AgentCoreRuntimeRole
```

## Support Resources

- **AWS Documentation**: https://docs.aws.amazon.com/bedrock/
- **AgentCore API Reference**: Check latest AWS CLI help
- **GitHub OAuth Setup**: https://docs.github.com/en/developers/apps/building-oauth-apps
- **Project Issues**: File issues in your repository

## Summary

You've successfully deployed a production-ready AI coding agent with:
- ✅ GitHub OAuth integration for secure user authentication
- ✅ AWS BedrockAgentCore runtime with Claude Sonnet 4.5
- ✅ Proper IAM roles and permissions
- ✅ CloudWatch logging and monitoring
- ✅ Optional HTTP gateway for external access

Next: Test the agent with real GitHub operations and iterate based on feedback!
