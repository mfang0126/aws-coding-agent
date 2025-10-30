# AWS Coding Agent

AI coding assistant powered by AWS Bedrock and Claude Sonnet 4.5 with GitHub integration.

## Quick Start

```bash
# Start development server
make dev

# Run tests
make test

# Setup GitHub OAuth (optional)
make setup-github
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

### Docker

```bash
docker build -t aws-coding-agent .
docker run -p 8000:8000 --env-file .env aws-coding-agent
```

### AWS AgentCore

```bash
# Configure
agentcore configure -e src/agent/runtime.py --region ap-southeast-2

# Deploy
agentcore launch -a coding-agent

# Check status
agentcore status -a coding-agent
```

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
| [docs/COMMANDS.md](docs/COMMANDS.md) | All available make commands |
| [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) | Auth setup (local vs OAuth) |

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
