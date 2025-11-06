# Quick Start Guide - AWS Coding Agent Implementation

**Based on:** `draft.md` architecture
**Full Workflow:** `claudedocs/implementation-workflow.md`
**Dependencies:** `claudedocs/dependency-graph.md`

---

## TL;DR - 5-Day Implementation Plan

### Day 1: Foundation + OAuth (6-8 hours)
```bash
# 1. Setup project
uv init coding-agent-mvp && cd coding-agent-mvp
uv add strands-agents fastapi uvicorn pydantic pydantic-settings PyGithub boto3 structlog

# 2. Create structure
mkdir -p src/{config,prompts,models,auth,agent,tools,chat,utils}

# 3. Create GitHub OAuth App
# → https://github.com/settings/developers
# → Note Client ID and Secret

# 4. Setup OAuth provider
python -m src.auth.setup_provider
# → CRITICAL: Register callback URL in GitHub OAuth App

# Deliverable: OAuth provider working ✓
```

### Day 2: Core Agent + Auth (6-8 hours)
```bash
# 1. Implement prompts (src/prompts/)
# 2. Implement models (src/models/)
# 3. Implement auth module (src/auth/github_auth.py)
# 4. Create agent factory (src/agent/create_agent.py)

# Test agent creation
python -c "from src.agent.create_agent import create_coding_agent; agent = create_coding_agent(); print('Agent ready!')"

# Deliverable: Agent can be created ✓
```

### Day 3: GitHub Integration (6-8 hours)
```bash
# 1. Implement GitHub tools (src/tools/)
#    - list_repos, get_repo_info, create_issue, list_issues, create_pr
# 2. Add @requires_access_token to each tool
# 3. Test with OAuth flow

# Test tools
python -m pytest tests/integration/test_github_tools.py

# Deliverable: GitHub tools working ✓
```

### Day 4: Streaming Chat (6-8 hours)
```bash
# 1. Implement stream handler (src/chat/stream_handler.py)
# 2. Implement session management (src/chat/session.py)
# 3. Create FastAPI app (src/main.py)
# 4. Test locally

# Run locally
uvicorn src.main:app --reload
# Test: curl -X POST http://localhost:8000/chat/stream -H "Content-Type: application/json" -d '{"message":"Hello","session_id":"test"}'

# Deliverable: Streaming chat working ✓
```

### Day 5: Testing + Deployment (6-8 hours)
```bash
# 1. Run all tests
pytest tests/ --cov=src --cov-report=term-missing

# 2. Build Docker image
docker build -t coding-agent:v1 .

# 3. Configure AgentCore
agentcore configure -e src/agent/runtime.py --region ap-southeast-2 --non-interactive

# 4. Deploy
agentcore launch -a coding-agent

# 5. Test live
curl -X POST https://<agent-url>/chat/stream ...

# Deliverable: Production deployment ✓
```

---

## Critical Success Factors

### ⚠️ MUST DO (or everything breaks)

1. **Register OAuth Callback URL**
   - After running `setup_provider.py`, you get a callback URL
   - **MUST** add this to GitHub OAuth App settings
   - Location: https://github.com/settings/developers → Your App → Authorization callback URL
   - **Failure = OAuth flow will not work**

2. **Use USER_FEDERATION (not CLIENT_CREDENTIALS)**
   ```python
   @requires_access_token(
       auth_flow='USER_FEDERATION',  # ← This is critical
       provider_name='github-provider',
       scopes=['repo', 'read:user']
   )
   ```

3. **No Region Parameter in List/Delete**
   ```python
   # ✅ Correct
   client = boto3.client('bedrock-agentcore-control', region_name=region)
   client.list_oauth2_credential_providers()

   # ❌ Wrong (causes "region not set" error)
   client.list_oauth2_credential_providers(region=region)
   ```

4. **Separate Prompts from Code**
   - All long text → `src/prompts/`
   - No hardcoded prompts in agent/tools files
   - Use template functions, not string formatting in business logic

5. **Functions Over Classes**
   - Use functions for logic
   - Use Pydantic models for data
   - Only import classes (Agent, BedrockModel)
   - Don't create custom classes unless absolutely necessary

---

## Phase Summary

| Phase | Time | Key Deliverable | Critical Items |
|-------|------|-----------------|----------------|
| **1. Foundation** | 3h | Project structure | Config, logging |
| **2. OAuth** | 5h | OAuth provider | Callback URL registration ⚠️ |
| **3. Agent** | 4h | Agent factory | Separated prompts |
| **4. GitHub** | 5h | 5 GitHub tools | @requires_access_token on all |
| **5. Streaming** | 6h | FastAPI + SSE | OAuth URL streaming |
| **6. Testing** | 8h | >80% coverage | E2E OAuth flow |
| **7. Deployment** | 5h | Live agent | AgentCore config |

**Total:** 28-36 hours sequential | 18-26 hours parallel

---

## Fastest Path to MVP

### Minimum Viable Implementation (18 hours)

**Skip for MVP:**
- Documentation (Phase 2.4)
- Comprehensive testing (reduce Phase 6 to essentials)
- Production hardening

**Focus on:**
1. Foundation (2h)
2. OAuth setup (3h)
3. Basic agent (2h)
4. 2-3 GitHub tools only (3h)
5. Simple streaming (4h)
6. Basic E2E test (2h)
7. Deployment (2h)

**Result:** Working agent in ~18 hours, but needs hardening before production

---

## Verification Checklist

### After Phase 2 (OAuth)
```bash
# Verify provider exists
aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2

# Should show:
# - name: "github-provider"
# - vendor: "GithubOauth2"
# - callbackUrl: "https://..."

# ✓ Check: Callback URL is registered in GitHub OAuth App
```

### After Phase 4 (GitHub Tools)
```python
# Test tool with mock
from src.tools.github_tools import list_github_repos

async def test():
    repos = await list_github_repos(access_token="test_token")
    print(f"Found {len(repos)} repos")

# ✓ Check: No import errors, decorator applied
```

### After Phase 5 (Streaming)
```bash
# Test locally
uvicorn src.main:app --reload

# In another terminal
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"test-123"}'

# ✓ Check: See streaming SSE events
# data: {"type":"token","content":"Hello"}
# data: {"type":"done"}
```

### After Phase 7 (Deployment)
```bash
# Check deployment status
agentcore status -a coding-agent

# Test live endpoint
curl -N -X POST https://<agent-url>/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"List my repositories","session_id":"user-1"}'

# ✓ Check: OAuth URL generated on first request
# ✓ Check: After auth, repositories listed
```

---

## Common Pitfalls & Solutions

### Pitfall 1: "Provider not found"
**Cause:** Name mismatch
**Fix:**
```bash
# Everywhere must use exact name "github-provider":
# 1. Provider creation: --name "github-provider"
# 2. Agent config: credential_providers: [github-provider]
# 3. Decorator: provider_name='github-provider'
```

### Pitfall 2: "OAuth callback error"
**Cause:** Callback URL not registered
**Fix:**
```bash
# Get callback URL
aws bedrock-agentcore-control get-oauth2-credential-provider \
  --name "github-provider" --region ap-southeast-2 | jq -r '.callbackUrl'

# Add to GitHub OAuth App settings
# https://github.com/settings/developers
```

### Pitfall 3: "Token not persisted"
**Cause:** Wrong auth flow
**Fix:**
```python
# Must be USER_FEDERATION
@requires_access_token(
    auth_flow='USER_FEDERATION',  # Not CLIENT_CREDENTIALS
    force_authentication=False     # Don't force re-auth
)
```

### Pitfall 4: "Streaming not working"
**Cause:** Wrong content type
**Fix:**
```python
# FastAPI
from fastapi.responses import StreamingResponse

return StreamingResponse(
    stream_agent_response(...),
    media_type="text/event-stream"  # ← Must be this
)
```

### Pitfall 5: "GitHub rate limit"
**Cause:** Too many API calls
**Fix:**
```python
from github import RateLimitExceededException
import asyncio

try:
    # API call
except RateLimitExceededException:
    logger.warning("Rate limited, waiting 60s")
    await asyncio.sleep(60)
    # Retry
```

---

## Resource Requirements

### AWS Permissions Needed
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore-control:CreateOAuth2CredentialProvider",
        "bedrock-agentcore-control:GetOAuth2CredentialProvider",
        "bedrock-agentcore-control:ListOAuth2CredentialProviders",
        "bedrock-agentcore-control:DeleteOAuth2CredentialProvider",
        "bedrock:InvokeModel",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Development Environment
```bash
# Required
- Python 3.11+
- uv or Poetry
- Docker
- AWS CLI
- git

# Install agentcore CLI
pip install bedrock-agentcore-cli

# Verify
agentcore --version
aws --version
docker --version
```

### GitHub Setup
```
1. Create OAuth App
   - Go to: https://github.com/settings/developers
   - Click: "New OAuth App"
   - Fill in details
   - Enable Device Flow

2. Test Repository
   - Create a test repo for validation
   - Grant OAuth app access to this repo
```

---

## Testing Strategy

### Unit Tests (2 hours)
- Config loading
- Template generation
- Model validation
- Utility functions

### Integration Tests (2 hours)
- OAuth provider creation
- Agent creation with tools
- GitHub tool execution (mocked)

### E2E Tests (4 hours)
- Complete OAuth flow
- Streaming chat session
- PR review workflow
- Error handling

### Manual Validation (1 hour)
- OAuth with real GitHub account
- List real repositories
- Create test issue
- Stream responses properly

---

## Next Steps After Deployment

### Week 1
- [ ] Monitor CloudWatch logs daily
- [ ] Test with 3-5 real users
- [ ] Document any edge cases
- [ ] Optimize based on usage

### Week 2
- [ ] Add monitoring dashboards
- [ ] Implement alerting
- [ ] Performance optimization
- [ ] Security review

### Month 1
- [ ] User feedback analysis
- [ ] Feature prioritization
- [ ] Scale testing
- [ ] Cost optimization

---

## Getting Help

### Documentation References
- Full workflow: `claudedocs/implementation-workflow.md`
- Dependencies: `claudedocs/dependency-graph.md`
- Architecture: `draft.md`

### AWS Resources
- AgentCore Docs: https://docs.aws.amazon.com/bedrock-agentcore/
- Strands SDK: https://github.com/aws-samples/strands-agents-sdk

### GitHub Resources
- OAuth Apps: https://docs.github.com/en/apps/oauth-apps
- Device Flow: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow

---

## Success Metrics

### Must Achieve (MVP)
- ✓ OAuth flow works (>90% success rate)
- ✓ GitHub tools functional (all 5 working)
- ✓ Streaming chat operational (<2s first token)
- ✓ Deployment successful (accessible via URL)

### Should Achieve (Production)
- Test coverage >80%
- Error rate <1%
- API response time <2s (p95)
- CloudWatch alerts configured

### Nice to Have (Future)
- Multi-region deployment
- Advanced PR analysis
- Team collaboration features
- Webhook integration

---

**Ready to start?** Begin with Day 1 tasks and follow the workflow document for detailed implementation steps.

**Questions?** Check troubleshooting sections in:
- `implementation-workflow.md` (comprehensive guide)
- `dependency-graph.md` (timeline and dependencies)
- `draft.md` (architecture reference)
