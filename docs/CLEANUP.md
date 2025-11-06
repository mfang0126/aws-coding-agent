# AWS Coding Agent - Cleanup Guide

Complete guide for removing all deployed AWS resources.

## Table of Contents

1. [Quick Cleanup](#quick-cleanup)
2. [Step-by-Step Cleanup](#step-by-step-cleanup)
3. [Verification](#verification)
4. [Manual Cleanup (Fallback)](#manual-cleanup-fallback)

---

## Quick Cleanup

### One-Command Cleanup

```bash
# Destroy all AgentCore resources (recommended)
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --delete-ecr-repo --force
```

This removes:
- ✓ AgentCore agent runtime and endpoint
- ✓ ECR Docker images (all versions)
- ✓ ECR repository
- ✓ CodeBuild project
- ✓ IAM execution roles
- ✓ Agent configuration files

**Time**: ~2-3 minutes

---

## Step-by-Step Cleanup

### 1. Check Current Deployment Status

```bash
# View what's currently deployed
AWS_PROFILE=mingfang agentcore status
```

**Example Output**:
```
Agent Status: coding_agent
Ready - Agent deployed and endpoint available

Agent Details:
Agent Name: coding_agent
Agent ARN: arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/coding_agent-xxx
Endpoint: DEFAULT (READY)
Region: ap-southeast-2 | Account: 670326884047
```

### 2. Preview What Will Be Destroyed (Dry Run)

```bash
# See what will be deleted without actually deleting
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --dry-run
```

**Example Output**:
```
🔍 Dry run: Preview of resources that would be destroyed

Resources That Would Be Destroyed:
  ✓ AgentCore agent: arn:aws:bedrock-agentcore:...
  ✓ ECR images: 10 images
  ✓ CodeBuild project: bedrock-agentcore-coding_agent-builder
  ✓ IAM execution role: AmazonBedrockAgentCoreSDKRuntime-...
```

### 3. Destroy All Resources

```bash
# Destroy with confirmation prompt
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --delete-ecr-repo

# OR destroy without confirmation (use carefully!)
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --delete-ecr-repo --force
```

**What Gets Removed**:
1. **AgentCore Runtime**: Agent endpoint and execution environment
2. **ECR Images**: All Docker images (tagged and untagged)
3. **ECR Repository**: The entire container registry
4. **CodeBuild Project**: Build automation resources
5. **IAM Roles**: Execution and build roles (if not used by other agents)
6. **Local Configuration**: `.bedrock_agentcore.yaml` and `.bedrock_agentcore/` directory

### 4. Clean Up S3 Bucket (Manual)

The CodeBuild source bucket needs manual cleanup:

```bash
# Delete the S3 bucket
AWS_PROFILE=mingfang aws s3 rb s3://bedrock-agentcore-codebuild-sources-ACCOUNT-REGION --force
```

**Example**:
```bash
AWS_PROFILE=mingfang aws s3 rb s3://bedrock-agentcore-codebuild-sources-670326884047-ap-southeast-2 --force
```

### 5. Remove OAuth Provider (Optional)

The OAuth provider can be reused for future deployments. Delete only if you're sure you won't need it:

```bash
# List existing providers
AWS_PROFILE=mingfang aws bedrock-agentcore list-oauth2-credential-providers \
  --region ap-southeast-2

# Delete provider (CAREFUL!)
AWS_PROFILE=mingfang aws bedrock-agentcore delete-oauth2-credential-provider \
  --name github-provider \
  --region ap-southeast-2
```

**⚠️ Warning**: Only delete the OAuth provider if:
- You won't deploy this agent again
- No other agents use this provider
- You don't need the GitHub OAuth setup

---

## Verification

### Check All Resources Removed

```bash
# 1. Check AgentCore status (should show no agents)
AWS_PROFILE=mingfang agentcore status

# 2. Check for remaining ECR repositories
AWS_PROFILE=mingfang aws ecr describe-repositories --region ap-southeast-2 | grep bedrock-agentcore

# 3. Check for remaining S3 buckets
AWS_PROFILE=mingfang aws s3 ls | grep bedrock-agentcore

# 4. Check local configuration
ls -la .bedrock_agentcore* 2>/dev/null

# 5. Check git status (claudedocs should be gitignored)
git ls-files | grep claudedocs
```

**Expected Results**:
- ✅ No agent status returned
- ✅ No ECR repositories found
- ✅ No S3 buckets found (or only source bucket if not deleted)
- ✅ No `.bedrock_agentcore` files
- ✅ No claudedocs files tracked in git

### Verify IAM Roles Removed

```bash
# Check if roles still exist
AWS_PROFILE=mingfang aws iam get-role --role-name AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-* 2>&1

# Should return: "An error occurred (NoSuchEntity): The role with name ... cannot be found"
```

---

## Manual Cleanup (Fallback)

If `agentcore destroy` fails, use these manual commands:

### 1. Delete Agent Runtime

```bash
AWS_PROFILE=mingfang aws bedrock-agentcore delete-agent-runtime \
  --agent-runtime-identifier coding_agent-sQJDwfGL8y \
  --region ap-southeast-2
```

### 2. Delete ECR Images and Repository

```bash
# List images
AWS_PROFILE=mingfang aws ecr list-images \
  --repository-name bedrock-agentcore-coding_agent \
  --region ap-southeast-2

# Delete all images
AWS_PROFILE=mingfang aws ecr batch-delete-image \
  --repository-name bedrock-agentcore-coding_agent \
  --image-ids "$(aws ecr list-images --repository-name bedrock-agentcore-coding_agent --region ap-southeast-2 --query 'imageIds[*]' --output json)" \
  --region ap-southeast-2

# Delete repository
AWS_PROFILE=mingfang aws ecr delete-repository \
  --repository-name bedrock-agentcore-coding_agent \
  --region ap-southeast-2 \
  --force
```

### 3. Delete CodeBuild Project

```bash
AWS_PROFILE=mingfang aws codebuild delete-project \
  --name bedrock-agentcore-coding_agent-builder \
  --region ap-southeast-2
```

### 4. Delete IAM Roles

```bash
# List inline policies
AWS_PROFILE=mingfang aws iam list-role-policies \
  --role-name AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-834d8c1cb6

# Delete inline policies (if any)
AWS_PROFILE=mingfang aws iam delete-role-policy \
  --role-name AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-834d8c1cb6 \
  --policy-name PolicyName

# Delete role
AWS_PROFILE=mingfang aws iam delete-role \
  --role-name AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-834d8c1cb6
```

### 5. Delete CloudWatch Log Groups

```bash
# List log groups
AWS_PROFILE=mingfang aws logs describe-log-groups \
  --log-group-name-prefix /aws/bedrock-agentcore/runtimes/coding_agent \
  --region ap-southeast-2

# Delete log group
AWS_PROFILE=mingfang aws logs delete-log-group \
  --log-group-name /aws/bedrock-agentcore/runtimes/coding_agent-sQJDwfGL8y-DEFAULT \
  --region ap-southeast-2
```

---

## Common Issues

### Issue: "Agent not found"

**Cause**: Agent already deleted or wrong agent name

**Solution**:
```bash
# List all agents
AWS_PROFILE=mingfang agentcore configure list

# Check status without agent name
AWS_PROFILE=mingfang agentcore status
```

### Issue: "Access Denied"

**Cause**: Insufficient IAM permissions

**Solution**:
- Ensure you're using the correct AWS profile
- Verify your IAM user/role has permissions for:
  - `bedrock-agentcore:*`
  - `iam:DeleteRole`
  - `ecr:*`
  - `codebuild:DeleteProject`
  - `s3:DeleteBucket`

### Issue: "Resource in use"

**Cause**: Active sessions or dependencies

**Solution**:
```bash
# Stop any active sessions first
AWS_PROFILE=mingfang agentcore stop-session --agent coding_agent

# Wait 1-2 minutes, then retry destroy
```

### Issue: "ECR repository not empty"

**Cause**: Images still exist in repository

**Solution**:
```bash
# Force delete with images
AWS_PROFILE=mingfang agentcore destroy --agent coding_agent --delete-ecr-repo --force
```

---

## Cost Impact

### Resources That Incur Costs

After cleanup, these costs stop immediately:
- ✅ **AgentCore Runtime**: ~$X/hour (stops)
- ✅ **ECR Storage**: ~$0.10/GB/month (stops after image deletion)
- ✅ **CloudWatch Logs**: ~$0.50/GB ingested + $0.03/GB storage (stops after log deletion)
- ✅ **CodeBuild**: Pay per build minute (no ongoing cost, but good to clean up)

### Resources With No Ongoing Cost

These don't cost money but good to clean up for hygiene:
- IAM roles and policies (no cost)
- OAuth providers (no cost)
- S3 bucket (only costs if storing data)

---

## Next Steps

After cleanup:

### If You Want to Redeploy

```bash
# 1. Configure agent
AWS_PROFILE=mingfang agentcore configure \
  --entrypoint src/runtime.py \
  --name coding_agent \
  --region ap-southeast-2

# 2. Deploy
AWS_PROFILE=mingfang agentcore launch
```

### If You're Done

- ✅ Resources deleted
- ✅ No ongoing costs
- ✅ Configuration files preserved locally
- ✅ Source code intact

---

## Summary Checklist

- [ ] Ran `agentcore destroy` successfully
- [ ] Deleted S3 bucket manually
- [ ] Verified no ECR repositories remain
- [ ] Verified no IAM roles remain
- [ ] Verified no local `.bedrock_agentcore` files
- [ ] Checked git status (no claudedocs tracked)
- [ ] (Optional) Deleted OAuth provider

**Total Cleanup Time**: 3-5 minutes

**Resources Removed**: 8+ AWS resources

**Cost Savings**: Immediate stop of all runtime costs

---

## References

- [AgentCore CLI Documentation](https://github.com/aws-samples/bedrock-agentcore-starter-toolkit)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [ECR Repository Cleanup](https://docs.aws.amazon.com/AmazonECR/latest/userguide/delete_repository.html)
- [Deployment Guide](DEPLOYMENT_SUMMARY.md)
