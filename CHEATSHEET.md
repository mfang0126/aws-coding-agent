# AWS Coding Agent - Cheat Sheet

## 🚀 Getting Started (5 Steps)

```bash
make aws-login              # 1. Login to AWS SSO
cp .env.example .env        # 2. Copy config (edit with your settings)
make install                # 3. Install dependencies
make dev                    # 4. Start server (http://localhost:8000)
make health                 # 5. Test it works
```

---

## 📋 Essential Commands

| Command | Description |
|---------|-------------|
| `make aws-login` | Login to AWS SSO |
| `make aws-check` | Verify AWS credentials |
| `make dev` | Start dev server (hot reload) |
| `make health` | Check if server is running |
| `make test` | Run tests |
| `make format` | Format code |
| `make lint` | Check code quality |
| `make clean` | Clean cache files |
| `make help` | Show all commands |

---

## 🔧 Configuration (.env)

```bash
# Required
AWS_REGION=ap-southeast-2
AWS_PROFILE=mingfang
MODEL_ID=au.anthropic.claude-sonnet-4-5-20250929-v1:0

# Optional - GitHub Features
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret

# OR for local dev (uncomment):
# GITHUB_TOKEN=github_pat_xxxxx
```

---

## 💬 Testing the Agent

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Request
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello!","session_id":"test"}' \
  --no-buffer
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| AWS credentials expired | `make aws-login` |
| Port 8000 in use | `PORT=8001 make dev` |
| Module not found | `make install` |
| Server won't start | Check `.env` exists and has required vars |
| GitHub auth fails | Uncomment `GITHUB_TOKEN` in `.env` |

---

## 🎯 Agent Capabilities

**✅ Can Do:**
- Answer coding questions
- List GitHub repos
- Get repo info
- Create issues
- List issues
- Create pull requests
- Technical discussions

**❌ Cannot Do (Yet):**
- Read file contents
- Close/update issues
- Merge PRs
- Add comments
- Branch management

---

## 📂 Project Structure

```
src/
├── agent/           # Agent factory & runtime
├── tools/           # GitHub tools
├── constants/       # Prompts & messages
├── auth/            # OAuth setup
├── chat/            # Streaming handler
├── config.py        # Settings
└── main.py          # FastAPI app
```

---

## 🚀 Deployment

```bash
# First time (creates OAuth & IAM)
make init-deploy

# Regular updates
make deploy

# View logs
make logs
```

---

## 🔗 Quick Links

- **Detailed Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Dev Guide**: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)
- **Commands**: [docs/COMMANDS_REFERENCE.md](docs/COMMANDS_REFERENCE.md)

---

## 💡 Pro Tips

1. **Hot Reload**: Edit code, server auto-restarts
2. **Custom Port**: `PORT=9000 make dev`
3. **Different Profile**: `AWS_PROFILE=other make dev`
4. **View Help**: `make help` shows all commands
5. **Alias**: `make login` = `make aws-login`

---

**Server URL**: http://localhost:8000
**Health**: http://localhost:8000/health
**Chat**: POST /chat/stream
