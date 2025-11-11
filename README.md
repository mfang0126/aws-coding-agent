# AWS Coding Agent

AI coding assistant powered by AWS Bedrock and Claude Sonnet 4.5 with GitHub integration.

## 🎯 What It Actually Does

### **Implemented GitHub Tools (5 functions):**

Based on `src/tools/github_tools.py`:

```python
# 1. List repositories
@requires_access_token
async def list_github_repos(limit: int = 10) -> list[dict]

# 2. Get repository information
@requires_access_token
async def get_repo_info(repo_full_name: str) -> dict

# 3. Create GitHub issue
@requires_access_token
async def create_github_issue(repo_full_name: str, title: str, body: str, labels: list[str] = None) -> dict

# 4. List repository issues
@requires_access_token
async def list_github_issues(repo_full_name: str, state: str = 'open', limit: int = 10) -> list[dict]

# 5. Create pull request
@requires_access_token
async def create_pull_request(repo_full_name: str, title: str, body: str, head: str, base: str = 'main') -> dict
```

### **AI Agent Implementation:**

Based on `src/agent/create_agent.py`:

```python
# Single Strands Agent with:
- Claude Sonnet 4.5 via AWS Bedrock
- 5 GitHub tools (above)
- System prompt for coding assistance
- OAuth or personal token authentication
```

### **Authentication Modes:**

From `src/agent/create_agent.py` lines 16-33:

```python
if settings.github_token:
    # Local development: Use GITHUB_TOKEN from .env
    from ..tools.github_tools_hybrid import [...]
else:
    # Production: Use OAuth via AgentCore Identity
    from ..tools.github_tools import [...]
```

### **Session Management:**

From `src/chat/session.py`:

```python
class SessionManager:
    def __init__(self):
        self._sessions: dict[str, list[ChatMessage]] = {}

    def add_message(self, message: ChatMessage) -> None
    def get_messages(self, session_id: str, limit: int | None = None) -> list[ChatMessage]
```

### **Deployment Architecture:**

From `src/runtime.py`:

```python
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    agent = get_agent()  # Lazy loading
    async for chunk in agent(payload["prompt"]):
        yield chunk  # Streaming responses
```

### **Actual Use Cases (What Works Right Now):**

```bash
# Working examples based on implemented tools:

# 1. List repos (limited to 10)
"List my GitHub repositories"

# 2. Get repo info
"Get information about facebook/react"

# 3. Create issue
"Create an issue in myrepo titled 'Bug in login page' with body 'Users cannot log in when using special characters'"

# 4. List issues
"List open issues in microsoft/vscode"

# 5. Create PR (basic)
"Create a pull request from feature-branch to main in myrepo with title 'Add user authentication'"
```

### **Technical Implementation Details:**

- **Framework**: Strands agents + AWS Bedrock
- **Language**: Python 3.11+
- **Database**: In-memory session storage
- **Authentication**: GitHub OAuth via AgentCore Identity or personal tokens
- **Streaming**: Server-Sent Events for real-time responses
- **Testing**: 38 tests covering AgentCore integration patterns

## 🚀 Quick Start

**New to this project? Start here:**

👉 **[Complete Quick Start Guide →](QUICKSTART.md)**

**TL;DR for experienced users:**

```bash
# 1. Login to AWS
make aws-login

# 2. Configure environment
cp .env.example .env
# Edit .env with your AWS_PROFILE and credentials

# 3. Install dependencies
make install

# 4. Start development server
make dev

# 5. Test it
make health
```

Server runs at: **http://localhost:8000**

**Deploy to AWS AgentCore:**
```bash
# 1. Install CLI
pip install bedrock-agentcore-starter-toolkit

# 2. Setup GitHub OAuth Provider (one-time)
#    Creates 'github-provider' in AgentCore Identity
python -m src.auth.setup_provider
#    → Copy callback URL from output
#    → Register in GitHub OAuth App: https://github.com/settings/developers

# 3. Configure agent with OAuth
agentcore configure \
  --entrypoint src/runtime.py \
  --name coding_agent \
  --region ap-southeast-2 \
  --disable-memory \
  --disable-otel \
  --authorizer-config '{"workload_name": "coding-agent-workload", "credential_providers": ["github-provider"]}' \
  --non-interactive

# 4. Deploy to AWS (auto-creates IAM, ECR, builds via CodeBuild)
agentcore launch

# 5. Test deployment
agentcore invoke '{"prompt": "Hello!"}'
```

**All commands**: See [docs/COMMANDS.md](docs/COMMANDS.md)

## Status: ✅ Fully Functional

All 7 implementation phases complete:
- ✅ Foundation (config, logging, structure)
- ✅ OAuth Infrastructure (hybrid auth)
- ✅ Core Agent (Claude Sonnet 4.5)
- ✅ GitHub Integration (5 tools)
- ✅ Streaming Chat (SSE)
- ✅ Testing (29/31 passing)
- ✅ Deployment Ready (Docker + AgentCore)

## Architecture: Dual-Mode Deployment

```
Core Agent (Pure Strands)
    src/agent/create_agent.py
           ↓
    ┌──────┴──────┐
    ↓             ↓
FastAPI      AgentCore
(Container)   (AWS Only)
```

**Three Deployment Options:**
1. **Local Dev**: `python src/main.py` (FastAPI server)
2. **3rd Party Container**: Docker → ECS/K8s/Cloud Run/etc
3. **AWS AgentCore**: `agentcore launch` (AWS-native features)

## Features

- **AI Agent**: Claude Sonnet 4.5 via AWS Bedrock
- **Streaming**: Real-time responses with Server-Sent Events
- **GitHub Tools**: List repos, create issues, create PRs, get repo info
- **Hybrid Auth**: Local token (dev) OR OAuth (production)
- **Modern Python**: Functions-first, Pydantic v2, type hints

## Prerequisites

- Python 3.11+
- AWS account with Bedrock access
- GitHub account
- AWS CLI configured with SSO

## Installation

```bash
# Clone repository
git clone <your-repo-url>
cd aws-coding-agent

# Install dependencies (uses uv)
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Required Environment Variables

```bash
# AWS
AWS_REGION=ap-southeast-2
AWS_PROFILE=your-profile

# Bedrock Model
MODEL_ID=au.anthropic.claude-sonnet-4-5-20250929-v1:0

# GitHub OAuth (for production)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# GitHub Personal Token (for local dev)
# GITHUB_TOKEN=ghp_your_token  # Optional, bypasses OAuth
```

### Authentication Setup

**Option 1: Local Development (Recommended)**

Create a GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:user`
4. Add to `.env`: `GITHUB_TOKEN=ghp_...`

**Option 2: Production (OAuth)**

Setup OAuth provider:
```bash
make setup-github
```

Then register the callback URL in your GitHub OAuth App.

**Full guide**: See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)

## Usage

### Start Server

```bash
make dev  # Development with hot reload
```

### Test the Agent

```bash
# General coding questions
curl -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Explain recursion","session_id":"test"}' \
  --no-buffer

# GitHub operations
curl -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"List my GitHub repos","session_id":"test"}' \
  --no-buffer
```

### Run Tests

```bash
make test          # All tests
make test-cov      # With coverage
make lint          # Code quality
```

## Project Structure

```
aws-coding-agent/
├── src/
│   ├── agent/          # Agent factory
│   ├── auth/           # OAuth setup
│   ├── chat/           # SSE streaming
│   ├── models/         # Pydantic models
│   ├── prompts/        # System prompts
│   ├── tools/          # GitHub tools
│   ├── utils/          # Logging
│   ├── config.py       # Settings
│   └── main.py         # FastAPI app
├── tests/              # Test suite
├── Makefile            # Commands
├── COMMANDS.md         # Command reference
├── AUTHENTICATION.md   # Auth guide
└── .env                # Configuration
```

## Architecture

**Backend**: Python 3.11, FastAPI, Uvicorn
**AI Model**: Claude Sonnet 4.5 (AWS Bedrock)
**Agent Framework**: Strands Agents SDK
**Auth**: Hybrid (local token or AWS AgentCore OAuth)
**Deployment**: Docker, AWS AgentCore Runtime
**Streaming**: Server-Sent Events (SSE)

## Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/chat/stream` | POST | Streaming chat |
| `/docs` | GET | API documentation |

## GitHub Integration

The agent can:
- List your repositories
- Get repository information
- Create issues
- List issues
- Create pull requests

Works in both auth modes (local token or OAuth).

## Development

```bash
# Start server with hot reload
make dev

# In another terminal
make test          # Run tests
make lint          # Check code
make format        # Format code
```

## Deployment

### Quick Deploy to AWS BedrockAgentCore

```bash
# One-command deployment
make deploy

# Test deployment
make test-runtime

# View logs
make logs
```

**Full deployment guide**: See [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

### Docker (Local)

```bash
docker build -t aws-coding-agent .
docker run -p 8000:8000 --env-file .env aws-coding-agent
```

### AWS AgentCore CLI Deployment

**Prerequisites:**
```bash
# Install AgentCore CLI
pip install bedrock-agentcore-starter-toolkit

# Ensure AWS SSO is active
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

**Project Structure Required:**
```
aws-coding-agent/
├── src/
│   ├── runtime.py          # Must have @app.entrypoint decorator
│   ├── pyproject.toml      # Must be inside src/ directory
│   └── agent/
├── .bedrock_agentcore.yaml # Generated by configure
└── tests/
```

**Deployment Steps:**

1. **Setup GitHub OAuth Provider** (one-time setup):
```bash
# Ensure .env has GitHub OAuth credentials:
# GITHUB_CLIENT_ID=your_github_oauth_app_client_id
# GITHUB_CLIENT_SECRET=your_github_oauth_app_secret

# Create provider in AgentCore Identity
python -m src.auth.setup_provider

# Output will show:
# ✅ Created OAuth provider: arn:aws:bedrock-agentcore:...
# 🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:
#    https://oauth.agentcore.bedrock.aws.dev/...

# Go to https://github.com/settings/developers
# → Select your OAuth App
# → Add callback URL to "Authorization callback URL"
# → Save changes
```

**Note:** You can verify existing providers:
```bash
python3 -c "
import boto3
client = boto3.client('bedrock-agentcore-control', region_name='ap-southeast-2')
providers = client.list_oauth2_credential_providers()
for p in providers.get('credentialProviders', []):
    print(f\"{p['name']}: {p['credentialProviderArn']}\")
"
```

2. **Configure Agent** (creates `.bedrock_agentcore.yaml` with OAuth):
```bash
agentcore configure \
  --entrypoint src/runtime.py \
  --name coding_agent \
  --region ap-southeast-2 \
  --disable-memory \
  --disable-otel \
  --authorizer-config '{"workload_name": "coding-agent-workload", "credential_providers": ["github-provider"]}' \
  --non-interactive
```

3. **Deploy to AWS** (auto-creates IAM roles, ECR, builds container via CodeBuild):
```bash
agentcore launch
```

4. **Test Agent**:
```bash
agentcore invoke '{"prompt": "Hello, explain recursion"}'
```

**Important Notes:**
- `pyproject.toml` must be in `src/` directory (CLI looks for dependencies relative to entrypoint)
- CodeBuild handles containerization remotely (no Docker needed locally)
- Auto-creates IAM execution role and ECR repository
- Platform: `linux/arm64` (AWS Graviton)
- `@app.entrypoint` decorator required in `runtime.py`

**Detailed commands**: See [COMMANDS_REFERENCE.md](COMMANDS_REFERENCE.md)

## Troubleshooting

### Agent won't start
- Check AWS SSO: `aws sso login --profile your-profile`
- Verify .env configuration
- Check logs for errors

### GitHub tools not working
- **Local mode**: Verify GITHUB_TOKEN is set
- **OAuth mode**: Check OAuth provider setup
- See [AUTHENTICATION.md](AUTHENTICATION.md)

### Streaming issues
- Check server logs
- Verify curl `--no-buffer` flag
- Test `/health` endpoint first

## Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | This file - overview & quick start |
| [docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md) | Complete deployment overview |
| [docs/QUICK_START.md](docs/QUICK_START.md) | 5-minute deployment guide |
| [docs/CLEANUP.md](docs/CLEANUP.md) | Resource cleanup and destruction guide |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Detailed deployment steps |
| [docs/COMMANDS_REFERENCE.md](docs/COMMANDS_REFERENCE.md) | Copy-paste command reference |
| [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) | Auth setup (local vs OAuth) |
| [docs/COMMANDS.md](docs/COMMANDS.md) | Development commands |

## Contributing

This is a reference implementation. Feel free to fork and customize for your needs.

## License

MIT License - See LICENSE file

## Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents SDK](https://github.com/aws-samples/strands-agents-sdk)
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with**: Python • AWS Bedrock • Strands Agents • FastAPI • Claude Sonnet 4.5
