# Quick Start: Deploy to AWS BedrockAgentCore

Fast track to deploying your coding agent to production.

## Prerequisites Checklist

- [ ] AWS CLI installed and configured
- [ ] Python 3.11+ installed
- [ ] `uv` package manager installed
- [ ] GitHub OAuth App created
- [ ] `.env` file configured

## 5-Minute Deployment

### Step 1: Configure Environment (2 min)
```bash
cd /Users/freedom/ai/aws-coding-agent

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

Required values in `.env`:
```bash
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang
GITHUB_CLIENT_ID=Ov23li...     # From GitHub OAuth app
GITHUB_CLIENT_SECRET=9e32c1...  # From GitHub OAuth app
```

### Step 2: Deploy Everything (2 min)
```bash
# Automated deployment
make deploy
```

This will:
- ✅ Create IAM role with necessary permissions
- ✅ Set up GitHub OAuth provider
- ✅ Configure agent runtime
- ✅ Deploy to AWS BedrockAgentCore

### Step 3: Update GitHub OAuth Callback (1 min)

After deployment, you'll see:
```
🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:
   https://bedrock-agentcore-identity.ap-southeast-2.amazonaws.com/oauth/callback
```

1. Go to https://github.com/settings/developers
2. Select your OAuth App
3. Add callback URL from output
4. Save changes

### Step 4: Test Deployment
```bash
# Run automated tests
make test-runtime

# View live logs
make logs
```

## Manual Step-by-Step

If automated deployment fails, follow these manual steps:

### 1. Create IAM Role
```bash
export AWS_PROFILE=mingfang
export AWS_REGION=ap-southeast-2

# Create role
aws iam create-role \
  --role-name AgentCoreRuntimeRole \
  --assume-role-policy-document file://scripts/trust-policy.json

# Attach permissions
aws iam attach-role-policy \
  --role-name AgentCoreRuntimeRole \
  --policy-arn arn:aws:iam::670326884047:policy/AgentCoreRuntimePolicy
```

### 2. Create OAuth Provider
```bash
make setup-github
```

### 3. Deploy Runtime
```bash
# Using AgentCore toolkit
agentcore runtime create \
  -a coding-agent \
  --runtime-name coding-agent-production \
  --role-arn arn:aws:iam::670326884047:role/AgentCoreRuntimeRole
```

## Common Commands

```bash
# Development
make dev              # Start local development server
make test             # Run tests
make lint             # Check code quality

# Deployment
make deploy           # Full deployment
make deploy-fast      # Skip provider/role creation
make setup-github     # OAuth provider only

# Testing & Monitoring
make test-runtime     # Test deployed runtime
make logs             # View CloudWatch logs
make health           # Check local server health
```

## Verification Checklist

After deployment, verify:

- [ ] IAM role exists: `aws iam get-role --role-name AgentCoreRuntimeRole`
- [ ] OAuth provider exists: `aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2`
- [ ] Runtime deployed: `aws bedrock-agentcore-control list-agent-runtimes --region ap-southeast-2`
- [ ] GitHub callback URL registered in OAuth app
- [ ] Tests pass: `make test-runtime`

## Troubleshooting

### "AWS credentials not configured"
```bash
aws sso login --profile mingfang
```

### "OAuth provider creation failed"
Check your `.env` file has correct `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`:
```bash
grep GITHUB .env
```

### "Runtime deployment failed"
Check IAM role exists and has correct permissions:
```bash
aws iam get-role --role-name AgentCoreRuntimeRole
```

### "Tests fail with authentication error"
Update GitHub OAuth app callback URL with value from `make setup-github` output.

## Next Steps

1. **Test locally first**: `make dev` → test with local token
2. **Deploy to production**: `make deploy`
3. **Monitor logs**: `make logs`
4. **Iterate**: Make changes → redeploy → test

## Resources

- **Full Guide**: [docs/DEPLOYMENT.md](./DEPLOYMENT.md)
- **Authentication**: [docs/AUTHENTICATION.md](./AUTHENTICATION.md)
- **Commands**: [docs/COMMANDS.md](./COMMANDS.md)

## Support

Common errors and solutions:

| Error | Solution |
|-------|----------|
| UnrecognizedClientException | Check AWS credentials: `aws sts get-caller-identity` |
| AccessDenied | Verify IAM permissions for bedrock-agentcore-control |
| Bad credentials (GitHub) | Check GitHub OAuth app credentials in .env |
| Module not found | Install dependencies: `uv sync` |

## Quick Test

Test your deployed agent:
```bash
# Create test payload
cat > test.json <<'EOF'
{
  "inputText": "Hello! List my GitHub repositories",
  "sessionId": "test-001"
}
EOF

# Invoke runtime
aws bedrock-agentcore invoke-agent-runtime \
  --region ap-southeast-2 \
  --agent-runtime-arn <YOUR_RUNTIME_ARN> \
  --payload fileb://test.json \
  output.json

# View response
cat output.json | jq
```

Find your runtime ARN:
```bash
aws bedrock-agentcore-control list-agent-runtimes \
  --region ap-southeast-2 \
  | jq -r '.agentRuntimes[] | .agentRuntimeArn'
```

---

**Estimated Time**: 5-10 minutes for full deployment
**Difficulty**: Easy (automated) / Medium (manual)
