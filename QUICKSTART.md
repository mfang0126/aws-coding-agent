# 🚀 Quick Start Guide - Running Locally

Get your AWS Coding Agent running locally in 5 minutes!

## Prerequisites

- **Python 3.11+** installed
- **AWS CLI** configured
- **AWS SSO** access (with Bedrock permissions)
- **GitHub OAuth App** (optional, for GitHub features)

---

## 1. Clone & Setup

```bash
# Navigate to project
cd aws-coding-agent

# Install dependencies
make install

# Or manually:
uv pip install -e ".[dev]"
```

---

## 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env  # or vim, code, etc.
```

**Required Configuration:**

```bash
# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang              # Your AWS profile name

# Model Configuration
MODEL_ID=au.anthropic.claude-sonnet-4-5-20250929-v1:0

# GitHub OAuth (optional - for GitHub features)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Local Development (optional - uncomment for local token)
# GITHUB_TOKEN=github_pat_xxxxx   # Your GitHub Personal Access Token
```

---

## 3. Login to AWS

```bash
# Login via AWS SSO
make aws-login

# Or manually:
aws sso login --profile mingfang

# Verify credentials
make aws-status
```

**Expected Output:**
```
AWS Identity Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Account: 670326884047
UserId: AROAZYEUYQ3H5UGFWQY4J:dev.tech
Arn: arn:aws:sts::670326884047:assumed-role/...
```

---

## 4. Start Development Server

```bash
# Start with hot reload
make dev

# Server will start on http://localhost:8000
```

**Expected Output:**
```
✓ AWS credentials are valid
Starting development server on 0.0.0.0:8000...
💡 Hot reload enabled - changes auto-restart server
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

---

## 5. Test the Agent

### Test 1: Health Check

```bash
# In another terminal
make health

# Or:
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
    "status": "healthy",
    "service": "coding-agent",
    "version": "1.0.0"
}
```

### Test 2: Chat with Agent

```bash
# Create test request
cat > /tmp/test.json << 'EOF'
{
  "message": "Hello! What can you help me with?",
  "session_id": "test-123"
}
EOF

# Send chat request
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d @/tmp/test.json \
  --no-buffer
```

**Expected Response (streaming):**
```
data: {"type": "token", "content": "Hello! I can help with:"}
data: {"type": "token", "content": "\n- General coding questions"}
data: {"type": "token", "content": "\n- GitHub operations"}
data: {"type": "done"}
```

---

## 6. Using the Agent

### Chat via cURL

```bash
# Simple question
echo '{"message":"Explain async/await in Python","session_id":"demo"}' | \
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d @- \
  --no-buffer
```

### GitHub Operations (requires GitHub OAuth/Token)

```bash
# List your repositories
echo '{"message":"List my GitHub repositories","session_id":"demo"}' | \
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d @- \
  --no-buffer

# Get repo info
echo '{"message":"Show me info about owner/repo","session_id":"demo"}' | \
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d @- \
  --no-buffer

# Create an issue
echo '{"message":"Create an issue in owner/repo with title \"Bug fix needed\"","session_id":"demo"}' | \
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d @- \
  --no-buffer
```

---

## 7. Common Commands

```bash
# Start development server
make dev

# Check AWS credentials
make aws-check

# View help
make help

# Stop server
# Press Ctrl+C in the terminal running make dev

# Clean cache files
make clean
```

---

## Troubleshooting

### Issue: "AWS credentials expired"

```bash
# Solution: Re-login to AWS SSO
make aws-login
```

### Issue: "Agent not configured"

```bash
# Solution: Check .env file
cat .env

# Ensure AWS_REGION and MODEL_ID are set
```

### Issue: "GitHub authentication failed"

**Option 1: Use Local Token (Easier for Development)**
```bash
# 1. Get Personal Access Token from GitHub
#    https://github.com/settings/tokens
#    Required scopes: repo, read:user

# 2. Add to .env
echo "GITHUB_TOKEN=github_pat_xxxxx" >> .env

# 3. Restart server
# Ctrl+C then make dev
```

**Option 2: Use OAuth (Production Mode)**
```bash
# 1. Create GitHub OAuth App
#    https://github.com/settings/developers

# 2. Add credentials to .env
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret

# 3. Setup OAuth provider
make setup-github

# 4. Restart server
```

### Issue: "Port 8000 already in use"

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
PORT=8001 make dev
```

### Issue: "ModuleNotFoundError"

```bash
# Reinstall dependencies
make install

# Or:
uv pip install -e ".[dev]"
```

---

## Development Tips

### Hot Reload

The server automatically reloads when you change code:

```bash
# Edit any file in src/
vim src/agent/create_agent.py

# Server automatically restarts
# ✓ Changes detected, reloading...
```

### Structured Logs

The agent uses structured logging:

```bash
# Watch logs in real-time
tail -f logs/agent.log

# Or check server terminal for:
# {"event": "agent_created", "status": "success"}
# {"event": "chat_request", "session_id": "test-123"}
```

### Custom Configuration

Override any config via environment variables:

```bash
# Use different model
MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0 make dev

# Use different AWS profile
AWS_PROFILE=my-other-profile make dev

# Different port
PORT=9000 make dev
```

---

## What's Next?

### 🚀 Deploy to AWS

```bash
# First time deployment
make init-deploy

# Regular updates
make deploy

# View logs
make logs
```

### 📚 Learn More

- [Architecture Documentation](docs/DEPLOYMENT_SUMMARY.md)
- [Commands Reference](docs/COMMANDS_REFERENCE.md)
- [Development Guide](docs/AGENT_DEVELOPMENT_GUIDE.md)
- [Cheat Sheet](docs/CHEATSHEET.md)

### 🛠️ Extend the Agent

- Add new tools in `src/tools/`
- Modify system prompt in `src/constants/prompts.py`
- Add new endpoints in `src/main.py`

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Login to AWS | `make aws-login` |
| Start server | `make dev` |
| Check health | `make health` |
| Run tests | `make test` |
| Format code | `make format` |
| Deploy to AWS | `make deploy` |
| View logs | `make logs` |
| Get help | `make help` |

---

## Support

**Issues?**
- Check the [Troubleshooting](#troubleshooting) section
- Review logs in your terminal
- Verify `.env` configuration

**Need Help?**
- Review documentation in `docs/`
- Check GitHub issues

---

## Success Checklist

- ✅ AWS SSO login successful
- ✅ `.env` file configured
- ✅ Server starts without errors
- ✅ Health endpoint returns `healthy`
- ✅ Chat endpoint streams responses
- ✅ Agent responds to messages

**You're ready to code! 🎉**
