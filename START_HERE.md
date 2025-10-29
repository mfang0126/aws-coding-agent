# 🚀 START HERE - New Session Quickstart

**Last Updated:** 2025-10-29
**Project:** AWS Coding Agent with GitHub OAuth Integration
**Status:** Planning Complete → Ready for Implementation

---

## 📖 What We Have

You have **complete implementation documentation** ready to use:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **`draft.md`** | Full architecture specification | Reference for design decisions |
| **`claudedocs/quick-start-guide.md`** | 5-day implementation plan | **START HERE** - Your daily roadmap |
| **`claudedocs/implementation-workflow.md`** | Detailed phase-by-phase guide | Deep dive into each task |
| **`claudedocs/dependency-graph.md`** | Visual dependencies & timelines | Planning & scheduling |
| **`claudedocs/incremental-testing-strategy.md`** | Test after each phase | Validation & quality gates |

---

## 🎯 Starting a New Session - Choose Your Path

### Path 1: I'm Starting Fresh (Day 1) ⭐ RECOMMENDED

```bash
# 1. Read the quick-start guide
cat claudedocs/quick-start-guide.md

# 2. Start Day 1 tasks
# Follow: "Day 1: Foundation + OAuth (6-8 hours)"
# Location: claudedocs/quick-start-guide.md

# 3. Reference detailed steps as needed
# Open: claudedocs/implementation-workflow.md → Phase 1 & 2
```

**What you'll do today:**
- Setup project structure (1 hour)
- Create GitHub OAuth App (30 min)
- Setup OAuth provider in AWS (1-2 hours)
- **Critical:** Register callback URL in GitHub

**End of day deliverable:** OAuth provider working ✓

---

### Path 2: I'm Continuing from a Previous Session

```bash
# 1. Check where you left off
cat claudedocs/implementation-workflow.md | grep "Phase [0-9]:"

# 2. Review your last phase completion
# Example: "I finished Phase 3 yesterday"
cat claudedocs/incremental-testing-strategy.md | grep -A 20 "Phase 3:"

# 3. Run tests to verify previous work still works
pytest tests/test_config.py tests/test_auth.py tests/test_agent_creation.py -v

# 4. Continue with next phase
# Open: claudedocs/quick-start-guide.md → Next day
```

---

### Path 3: I Want to Understand Before Building

```bash
# Read in this order:
1. draft.md (architecture overview - 10 min)
2. claudedocs/dependency-graph.md (visual flow - 5 min)
3. claudedocs/quick-start-guide.md (implementation roadmap - 10 min)

# Then proceed to Path 1
```

---

## 🛠️ Prerequisites Checklist

Before starting implementation, ensure you have:

### Development Environment
- [ ] Python 3.11+ installed (`python --version`)
- [ ] uv or Poetry installed (`uv --version` or `poetry --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Git installed (`git --version`)
- [ ] AWS CLI configured (`aws sts get-caller-identity`)
- [ ] AgentCore CLI installed (`pip install bedrock-agentcore-cli`)

### AWS Setup
- [ ] AWS account with Bedrock access
- [ ] IAM permissions for bedrock-agentcore-control
- [ ] Region set to ap-southeast-2 (or your preferred region)

### GitHub Setup
- [ ] GitHub account
- [ ] Developer access to create OAuth Apps
- [ ] Know your GitHub username

### Environment Files
```bash
# Create .env file
cp .env.example .env

# Edit .env with your values:
# - AWS_REGION
# - GITHUB_CLIENT_ID (get this in Phase 2)
# - GITHUB_CLIENT_SECRET (get this in Phase 2)
```

**Estimated setup time:** 30-60 minutes (one-time)

---

## 📅 Quick Reference: What Phase Am I On?

### Phase 1: Foundation ✓
**Completed when:**
- [ ] Project structure exists (`ls src/`)
- [ ] Config loads (`pytest tests/test_config.py`)
- [ ] Logging works (`pytest tests/test_logging.py`)

### Phase 2: OAuth Infrastructure ✓
**Completed when:**
- [ ] GitHub OAuth App created
- [ ] OAuth provider exists in AWS
- [ ] Callback URL registered in GitHub
- [ ] Auth tests pass (`pytest tests/test_auth.py`)

### Phase 3: Core Agent ✓
**Completed when:**
- [ ] Prompts separated from code
- [ ] Models validate data (`pytest tests/test_models.py`)
- [ ] Agent can be created (`python -c "from src.agent.create_agent import create_coding_agent; create_coding_agent()"`)

### Phase 4: GitHub Tools ✓
**Completed when:**
- [ ] All 5 tools implemented
- [ ] @requires_access_token on each tool
- [ ] Tool tests pass (`pytest tests/test_github_tools_*.py`)

### Phase 5: Streaming Chat ✓
**Completed when:**
- [ ] FastAPI app starts (`uvicorn src.main:app`)
- [ ] `/health` returns 200
- [ ] `/chat/stream` returns SSE events
- [ ] **Can deploy locally** 🎉

### Phase 6: Testing ✓
**Completed when:**
- [ ] Test coverage >80% (`pytest --cov=src --cov-fail-under=80`)
- [ ] E2E tests pass

### Phase 7: Deployment ✓
**Completed when:**
- [ ] Deployed to AgentCore (`agentcore launch`)
- [ ] Smoke tests pass
- [ ] Live OAuth tested

---

## 🎬 Quick Start Commands

### Absolute Fastest Start (0 to coding in 2 minutes)
```bash
# 1. Navigate to project
cd /Users/freedom/ai/aws-coding-agent

# 2. Create project structure
mkdir -p src/{config,prompts,models,auth,agent,tools,chat,utils} tests scripts docs

# 3. Initialize Python project
uv init --name coding-agent-mvp

# 4. Add dependencies
uv add strands-agents fastapi uvicorn pydantic pydantic-settings PyGithub boto3 structlog pytest pytest-asyncio pytest-cov

# 5. Open quick-start guide
cat claudedocs/quick-start-guide.md

# 6. Start with Phase 1
# Follow detailed steps in claudedocs/implementation-workflow.md
```

### Check Your Current Progress
```bash
# Run this anytime to see what's working
./tests/run_all_tests.sh

# Or phase by phase:
pytest tests/test_config.py -v          # Phase 1
pytest tests/test_auth.py -v            # Phase 2
pytest tests/test_agent_creation.py -v  # Phase 3
pytest tests/test_github_tools_*.py -v  # Phase 4
pytest tests/test_fastapi_endpoints.py -v  # Phase 5
```

---

## 🚨 Critical Success Factors (Don't Skip These!)

### 1. OAuth Callback URL Registration ⚠️
**When:** Phase 2, after running `setup_provider.py`
**Action:** The script outputs a callback URL - **MUST** add to GitHub OAuth App
**Where:** https://github.com/settings/developers → Your App → Authorization callback URL
**Why:** OAuth flow will fail silently without this

### 2. Provider Name Consistency
**Everywhere must use:** `github-provider` (exact name, case-sensitive)
- Provider creation: `--name "github-provider"`
- Agent config: `credential_providers: [github-provider]`
- Code decorator: `provider_name='github-provider'`

### 3. Use USER_FEDERATION
```python
@requires_access_token(
    auth_flow='USER_FEDERATION',  # ← Not CLIENT_CREDENTIALS
    provider_name='github-provider'
)
```

### 4. No Region Parameter in List/Delete
```python
# ✅ Correct
client = boto3.client('bedrock-agentcore-control', region_name=region)
client.list_oauth2_credential_providers()  # No region param

# ❌ Wrong
client.list_oauth2_credential_providers(region=region)
```

### 5. Separate Prompts from Code
All long text → `src/prompts/` (not in agent/tools files)

---

## 📞 Getting Help

### Something Not Working?

**Phase 2 (OAuth) Issues:**
```bash
# Run OAuth verification
./tests/integration/test_oauth_provider.sh

# Common issues in: claudedocs/implementation-workflow.md → "Troubleshooting"
```

**Phase 4 (GitHub Tools) Issues:**
```bash
# Check tool structure
pytest tests/test_github_tools_structure.py -v

# Verify decorators applied correctly
```

**Phase 5 (Streaming) Issues:**
```bash
# Test local deployment
./tests/integration/test_local_deployment.sh

# Check SSE formatting
pytest tests/test_streaming.py -v
```

### Documentation Map

```
Need architecture details?     → draft.md
Need step-by-step guide?      → claudedocs/implementation-workflow.md
Need quick daily plan?         → claudedocs/quick-start-guide.md
Need to know what's next?      → claudedocs/dependency-graph.md
Need to test your work?        → claudedocs/incremental-testing-strategy.md
```

---

## 📊 Expected Timeline

| Approach | Timeline | Best For |
|----------|----------|----------|
| **Focused (8h/day)** | 4-5 days | Full-time work |
| **Part-time (4h/day)** | 7-10 days | Side project |
| **Weekend sprint** | 2 weekends | Intensive build |
| **Casual (2h/day)** | 2-3 weeks | Learning pace |

---

## ✅ Starting Today? Do This:

### Recommended First Session (2-3 hours)

```bash
# 1. Verify prerequisites (15 min)
python --version  # 3.11+
aws sts get-caller-identity  # AWS configured
docker --version  # Docker installed

# 2. Read quick-start guide (15 min)
cat claudedocs/quick-start-guide.md | less

# 3. Setup project (1 hour)
mkdir -p src/{config,prompts,models,auth,agent,tools,chat,utils}
uv init --name coding-agent-mvp
uv add strands-agents fastapi uvicorn pydantic pydantic-settings PyGithub boto3 structlog

# 4. Implement Phase 1.2: Configuration (30 min)
# Follow: claudedocs/implementation-workflow.md → Phase 1.2
# Create: src/config.py

# 5. Test configuration (15 min)
# Create: tests/test_config.py
pytest tests/test_config.py -v

# 6. Commit your work
git add .
git commit -m "Phase 1: Foundation setup complete"
```

**End of session deliverable:** Configuration working ✓

---

## 🎯 Success Markers

You'll know you're on track when:

- **After 1 day:** OAuth provider exists in AWS ✓
- **After 2 days:** Agent can be created ✓
- **After 3 days:** GitHub tools work ✓
- **After 4 days:** Streaming chat runs locally ✓
- **After 5 days:** Deployed to production ✓

---

## 💡 Pro Tips

1. **Test immediately** - Don't accumulate technical debt
   ```bash
   # After implementing any module:
   pytest tests/test_your_module.py -v
   ```

2. **Commit frequently** - Easy rollback if needed
   ```bash
   git add . && git commit -m "Phase X.Y: [what you did]"
   ```

3. **Use the testing strategy** - Catch issues early
   ```bash
   # After each phase:
   cat claudedocs/incremental-testing-strategy.md | grep -A 30 "Phase [N]:"
   ```

4. **Follow the critical path** - OAuth → GitHub Tools → Streaming
   See: `claudedocs/dependency-graph.md`

5. **Don't skip quality gates** - Each phase has specific completion criteria

---

## 🚀 Ready to Start?

### Your Next Step:

```bash
# Open the quick-start guide
cat claudedocs/quick-start-guide.md

# Or in your preferred editor:
code claudedocs/quick-start-guide.md
# vim claudedocs/quick-start-guide.md
# nano claudedocs/quick-start-guide.md

# Then follow "Day 1: Foundation + OAuth"
```

---

## 📝 Session Notes Template

Create a `SESSION_NOTES.md` to track your progress:

```markdown
# Session Notes

## Session 1 - [Date]
- **Phase:** Phase 1 - Foundation
- **Time:** 3 hours
- **Completed:**
  - [x] Project structure
  - [x] Configuration
  - [x] Logging setup
- **Tests passing:** 6/6
- **Blockers:** None
- **Next session:** Phase 2 - OAuth setup

## Session 2 - [Date]
- **Phase:** Phase 2 - OAuth
- **Time:** 4 hours
- **Completed:**
  - [x] GitHub OAuth App created
  - [x] OAuth provider setup
  - [x] Callback URL registered
- **Tests passing:** 11/11
- **Blockers:** None
- **Next session:** Phase 3 - Agent development
```

---

**Remember:** You have complete, detailed documentation. Just start with the quick-start guide and reference the detailed workflow as needed. Good luck! 🎉
