# AWS BedrockAgentCore Deployment Summary

Complete reference for deploying your Python coding agent to AWS BedrockAgentCore.

## Project Context

**Location**: `/Users/freedom/ai/aws-coding-agent`
**Agent Type**: Python coding assistant with GitHub OAuth integration
**AWS Account**: 670326884047
**Region**: ap-southeast-2
**Profile**: mingfang

## What Was Created

### Documentation
1. **docs/DEPLOYMENT.md** - Complete deployment guide with all steps
2. **docs/QUICK_START.md** - 5-minute quick start guide
3. **scripts/deploy.sh** - Automated deployment script
4. **scripts/test-runtime.sh** - Runtime testing script
5. **Makefile** - Updated with deployment commands

### Key Features
- ✅ Automated IAM role creation
- ✅ GitHub OAuth provider setup
- ✅ Agent runtime deployment
- ✅ Automated testing
- ✅ CloudWatch logs integration

## Quick Start (5 Minutes)

### 1. Configure .env
```bash
cd /Users/freedom/ai/aws-coding-agent
cp .env.example .env
nano .env  # Add your GitHub OAuth credentials
```

### 2. Deploy Everything
```bash
make deploy
```

### 3. Update GitHub OAuth Callback
Copy the callback URL from deployment output and add it to your GitHub OAuth app.

### 4. Test
```bash
make test-runtime
make logs
```

## Available Commands

### Development
```bash
make dev              # Start local server with hot reload
make start            # Start production server locally
make test             # Run pytest suite
make test-cov         # Run tests with coverage report
make lint             # Check code quality with ruff
make format           # Format code with ruff
```

### Setup & Deployment
```bash
make setup-github     # Create OAuth provider only
make deploy           # Full deployment (IAM + OAuth + Runtime)
make deploy-fast      # Redeploy (skip IAM and OAuth)
```

### Testing & Monitoring
```bash
make test-runtime     # Test deployed runtime with sample requests
make logs             # Tail CloudWatch logs in real-time
make health           # Check local server health
```

## AWS Resources Created

### IAM Resources
- **Role**: `AgentCoreRuntimeRole`
  - ARN: `arn:aws:iam::670326884047:role/AgentCoreRuntimeRole`
  - Purpose: Execution role for agent runtime
  - Permissions: Bedrock model invocation, CloudWatch logs, OAuth provider access

- **Policy**: `AgentCoreRuntimePolicy`
  - ARN: `arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy`
  - Attached to: AgentCoreRuntimeRole

### AgentCore Resources
- **OAuth Provider**: `github-provider`
  - Vendor: GithubOauth2
  - Region: ap-southeast-2
  - Callback URL: Managed by AgentCore Identity service

- **Agent Runtime**: `coding-agent-production`
  - Entrypoint: `src.runtime`
  - Python Version: 3.11
  - Model: anthropic.claude-sonnet-4.5
  - Environment: LOG_LEVEL, MODEL_ID, GITHUB_PROVIDER_NAME, OAUTH_WORKLOAD_NAME

## Configuration Files

### .env (Required)
```bash
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=9e32c1...
MODEL_ID=anthropic.claude-sonnet-4.5
LOG_LEVEL=INFO
GITHUB_PROVIDER_NAME=github-provider
OAUTH_WORKLOAD_NAME=coding-agent-workload
```

### .bedrock_agentcore.yaml (Auto-generated)
```yaml
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

resources:
  memory: 2048
  cpu: 1024
```

## Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Prerequisites Check                                       │
│    • AWS CLI installed                                       │
│    • Python 3.11+ available                                  │
│    • uv package manager                                      │
│    • .env configured                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Create IAM Role & Policy                                  │
│    • AgentCoreRuntimeRole                                    │
│    • Trust policy for bedrock-agentcore.amazonaws.com        │
│    • Permissions for Bedrock, CloudWatch, OAuth              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Create OAuth Provider                                     │
│    • Run: make setup-github                                  │
│    • Creates github-provider in AgentCore Identity           │
│    • Returns callback URL for GitHub OAuth app               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Update GitHub OAuth App                                   │
│    • Add callback URL to GitHub OAuth app settings           │
│    • https://github.com/settings/developers                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Deploy Agent Runtime                                      │
│    • Package application code                                │
│    • Create runtime: coding-agent-production                 │
│    • Configure environment variables                         │
│    • Link OAuth provider                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Verify & Test                                             │
│    • Run: make test-runtime                                  │
│    • Check CloudWatch logs: make logs                        │
│    • Invoke runtime with sample requests                     │
└─────────────────────────────────────────────────────────────┘
```

## Testing Your Deployment

### Automated Tests
```bash
# Run all test scenarios
make test-runtime
```

Tests include:
1. Simple greeting (verify agent responds)
2. GitHub integration (list repositories)
3. Code explanation (test AI capabilities)

### Manual Testing
```bash
# Create test payload
cat > test.json <<'EOF'
{
  "inputText": "List my GitHub repositories",
  "sessionId": "manual-test-001"
}
EOF

# Get runtime ARN
RUNTIME_ARN=$(aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production") | .agentRuntimeArn')

# Invoke runtime
aws bedrock-agentcore invoke-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-arn "$RUNTIME_ARN" \
  --payload fileb://test.json \
  output.json

# View response
cat output.json | jq
```

## Monitoring & Debugging

### CloudWatch Logs
```bash
# Tail logs in real-time
make logs

# Or use AWS CLI directly
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 \
  --follow --format short
```

### Check Runtime Status
```bash
aws bedrock-agentcore-control get-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-identifier coding-agent-production \
  | jq -r '{name: .agentRuntimeName, status: .status, arn: .agentRuntimeArn}'
```

### List All Resources
```bash
# List agent runtimes
aws bedrock-agentcore-control list-agent-runtimes --region ap-southeast-2

# List OAuth providers
aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2

# List gateways (if created)
aws bedrock-agentcore-control list-gateways --region ap-southeast-2
```

## Troubleshooting Guide

### Issue: AWS Credentials Error
```bash
# Verify credentials
aws sts get-caller-identity

# Re-authenticate if needed
aws sso login --profile mingfang
```

### Issue: OAuth Provider Creation Failed
```bash
# Check GitHub credentials in .env
grep GITHUB .env

# Verify they match your GitHub OAuth app
# Go to https://github.com/settings/developers
```

### Issue: Runtime Deployment Failed
```bash
# Check IAM role exists
aws iam get-role --role-name AgentCoreRuntimeRole

# Verify role has correct permissions
aws iam list-attached-role-policies --role-name AgentCoreRuntimeRole

# Check CloudWatch logs for errors
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 --since 30m
```

### Issue: GitHub Bad Credentials at Runtime
```bash
# Verify OAuth provider exists
aws bedrock-agentcore-control get-oauth2-credential-provider \
  --region ap-southeast-2 \
  --name github-provider

# Check GitHub OAuth app callback URL
# Should match: https://bedrock-agentcore-identity.ap-southeast-2.amazonaws.com/oauth/callback

# Test OAuth provider separately
make setup-github
```

### Issue: Tests Fail
```bash
# Check runtime is active
aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production")'

# View detailed error logs
aws logs tail /aws/bedrock/agentcore/coding-agent-production \
  --region ap-southeast-2 --since 1h | grep ERROR
```

## Security Best Practices

### Development
- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Use minimal GitHub token scopes for testing
- ✅ Rotate test tokens regularly

### Production
- ✅ Store secrets in AWS Secrets Manager
- ✅ Use IAM roles instead of access keys
- ✅ Enable CloudWatch alarms for errors
- ✅ Monitor OAuth token usage
- ✅ Implement rate limiting
- ✅ Regular security audits

### Recommended: Migrate to Secrets Manager
```bash
# Store GitHub OAuth credentials
aws secretsmanager create-secret \
  --name coding-agent/github-oauth \
  --secret-string '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }' \
  --region ap-southeast-2

# Update src/config.py to fetch from Secrets Manager
# See docs/DEPLOYMENT.md for code examples
```

## Next Steps

### Integration Options
1. **API Gateway** - HTTP access to agent
2. **Lambda** - Serverless triggers
3. **EventBridge** - Scheduled tasks
4. **Step Functions** - Multi-agent workflows

### Enhancements
1. Add more GitHub tools (PR reviews, issue management)
2. Implement session persistence
3. Add code generation capabilities
4. Create custom dashboards
5. Set up automated testing pipeline

## Cost Optimization

### Expected Costs
- **Bedrock Model Invocation**: Pay per token
- **CloudWatch Logs**: ~$0.50/GB ingested
- **AgentCore Runtime**: No additional charge (Bedrock costs only)
- **OAuth Provider**: No additional charge

### Optimization Tips
- Set appropriate log retention (default: indefinite)
- Monitor token usage in CloudWatch
- Use request/response caching
- Implement rate limiting

```bash
# Set log retention to 7 days
aws logs put-retention-policy \
  --log-group-name /aws/bedrock/agentcore/coding-agent-production \
  --retention-in-days 7 \
  --region ap-southeast-2
```

## Cleanup (If Needed)

**For complete cleanup instructions, see [CLEANUP.md](CLEANUP.md)**

### Quick Cleanup

```bash
# One command to remove all resources
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --delete-ecr-repo --force
```

This removes:
- AgentCore agent runtime and endpoint
- ECR Docker images and repository
- CodeBuild project
- IAM execution roles
- Agent configuration files

### Additional Cleanup

```bash
# Delete S3 bucket (manual)
AWS_PROFILE=mingfang aws s3 rb s3://bedrock-agentcore-codebuild-sources-670326884047-ap-southeast-2 --force

# Delete OAuth provider (optional - can be reused)
AWS_PROFILE=mingfang aws bedrock-agentcore delete-oauth2-credential-provider \
  --name github-provider \
  --region ap-southeast-2
```

**See [CLEANUP.md](CLEANUP.md) for detailed step-by-step cleanup guide.**

## Resources

### Documentation
- [Complete Deployment Guide](DEPLOYMENT.md)
- [Quick Start (5 min)](QUICK_START.md)
- [Cleanup Guide](CLEANUP.md)
- [Authentication Guide](AUTHENTICATION.md)
- [Commands Reference](COMMANDS_REFERENCE.md)

### AWS Resources
- [BedrockAgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [GitHub OAuth Setup](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

### Support
- **GitHub Issues**: File issues in your repository
- **AWS Support**: Use AWS Support Console for account-specific issues
- **Community**: AWS Developer Forums

## Summary

You now have:
- ✅ Complete deployment documentation
- ✅ Automated deployment scripts
- ✅ Testing and monitoring tools
- ✅ Troubleshooting guides
- ✅ Security best practices

**Time to Deploy**: 5-10 minutes with automation
**Difficulty**: Easy (automated) / Medium (manual)

---

**Ready to deploy?** Run `make deploy` from `/Users/freedom/ai/aws-coding-agent`
