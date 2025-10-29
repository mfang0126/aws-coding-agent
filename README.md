# AWS Coding Agent MVP

AI coding assistant with GitHub OAuth integration, streaming chat interface, and PR review automation.

## 🚀 Quick Start

**New to this project?** Start here:
```bash
cat START_HERE.md
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[START_HERE.md](START_HERE.md)** | Session startup guide - read this first |
| **[quick-start-guide.md](claudedocs/quick-start-guide.md)** | 5-day implementation roadmap |
| **[implementation-workflow.md](claudedocs/implementation-workflow.md)** | Detailed phase-by-phase guide |
| **[dependency-graph.md](claudedocs/dependency-graph.md)** | Visual dependencies & timelines |
| **[incremental-testing-strategy.md](claudedocs/incremental-testing-strategy.md)** | Test after each phase |
| **[draft.md](draft.md)** | Complete architecture specification |

## 🏗️ Architecture

- **Backend:** Python 3.11+, FastAPI, Strands Agents SDK
- **AI Model:** Amazon Bedrock (Claude Sonnet 4.5)
- **Authentication:** GitHub OAuth via AgentCore Identity
- **Deployment:** AWS AgentCore Runtime
- **Streaming:** Server-Sent Events (SSE)

## 📋 Features

- ✅ GitHub OAuth (3-Legged OAuth with Device Flow)
- ✅ Streaming chat interface
- ✅ PR review automation
- ✅ GitHub API integration (repos, issues, PRs)
- ✅ Functional Python architecture
- ✅ Comprehensive testing strategy

## ⏱️ Timeline

| Approach | Duration |
|----------|----------|
| Sequential | 28-36 hours |
| Parallel (2 devs) | 26-28 hours |
| Optimized (3 devs) | 18-26 hours |
| MVP Fast Track | 18 hours |

## 🛠️ Prerequisites

- Python 3.11+
- uv or Poetry
- Docker
- AWS CLI (configured)
- AgentCore CLI
- GitHub account

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/mfang0126/aws-coding-agent.git
cd aws-coding-agent

# Install dependencies
uv sync
# or: poetry install

# Setup environment
cp .env.example .env
# Edit .env with your credentials
```

## 🚦 Getting Started

Follow the implementation phases:

### Phase 1: Foundation (2-3h)
- Project structure
- Configuration
- Logging

### Phase 2: OAuth Infrastructure (4-5h)
- GitHub OAuth App
- AWS OAuth provider
- Authentication module

### Phase 3: Core Agent (3-4h)
- Prompts & templates
- Data models
- Agent factory

### Phase 4: GitHub Integration (4-5h)
- GitHub SDK setup
- Tool implementations
- Rate limiting

### Phase 5: Streaming Chat (5-6h)
- Stream handler
- FastAPI app
- Session management

### Phase 6: Testing (6-8h)
- Unit tests
- Integration tests
- E2E tests

### Phase 7: Deployment (4-5h)
- AgentCore config
- Docker build
- Production deployment

## ✅ Quality Gates

Each phase includes:
- Specific completion criteria
- Test suite to validate
- Manual verification steps

## 🧪 Testing

```bash
# Run all tests
pytest tests/ --cov=src --cov-report=term-missing

# Run phase-specific tests
pytest tests/test_config.py -v          # Phase 1
pytest tests/test_auth.py -v            # Phase 2
pytest tests/test_agent_creation.py -v  # Phase 3
```

## 🚀 Deployment

```bash
# Configure AgentCore
agentcore configure -e src/agent/runtime.py --region ap-southeast-2

# Launch to AWS
agentcore launch -a coding-agent

# Check status
agentcore status -a coding-agent
```

## 📊 Project Status

- [x] Architecture designed
- [x] Documentation complete
- [ ] Phase 1: Foundation
- [ ] Phase 2: OAuth Infrastructure
- [ ] Phase 3: Core Agent
- [ ] Phase 4: GitHub Integration
- [ ] Phase 5: Streaming Chat
- [ ] Phase 6: Testing
- [ ] Phase 7: Deployment

## 🤝 Contributing

This is currently a personal project. See [implementation-workflow.md](claudedocs/implementation-workflow.md) for development guidelines.

## 📝 License

[Add your license here]

## 🔗 Resources

- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents SDK](https://github.com/aws-samples/strands-agents-sdk)
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps)

---

**Built with:** Python, FastAPI, AWS Bedrock, GitHub OAuth, AgentCore Runtime
