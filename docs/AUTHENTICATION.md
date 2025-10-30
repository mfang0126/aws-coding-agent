# GitHub Authentication Guide

The agent supports **hybrid authentication** - automatic detection of local vs production modes.

## Two Authentication Modes

### Mode 1: Local Development (Personal Access Token)
**Use when**: Testing locally, simple development workflow

**Setup**:
1. Create GitHub Personal Access Token at https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`
4. Copy the token (starts with `ghp_`)
5. Add to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

**Pros**:
- ✅ Simple setup (just add token to .env)
- ✅ Works immediately
- ✅ No OAuth flow setup needed
- ✅ Great for testing

**Cons**:
- ⚠️ Your personal token (not user-specific)
- ⚠️ Single user access only
- ⚠️ Token in .env (don't commit!)

### Mode 2: Production (OAuth)
**Use when**: Multi-user production deployment, user-specific actions

**Setup**:
1. Create GitHub OAuth App at https://github.com/settings/developers
2. Set callback URL: `https://your-agentcore-gateway.amazonaws.com/oauth/callback`
3. Add credentials to `.env`:
   ```bash
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```
4. Run OAuth provider setup:
   ```bash
   make setup-github
   ```

**Pros**:
- ✅ User-specific tokens (each user's own access)
- ✅ Secure (no tokens in .env)
- ✅ Production-ready
- ✅ Proper OAuth flow

**Cons**:
- ⚠️ More complex setup
- ⚠️ Requires AgentCore Identity service
- ⚠️ OAuth app configuration needed

## How the Agent Chooses

The agent **automatically detects** which mode to use:

```
Check GITHUB_TOKEN in .env
├─ If set → Use local token (Mode 1)
└─ If not set → Use OAuth (Mode 2)
```

**Priority**: Local token always takes precedence if set.

## Example Configurations

### Local Dev Only
```bash
# .env
GITHUB_TOKEN=ghp_abc123...
# OAuth not needed for local dev
```

### Production Only
```bash
# .env
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=9e32c1...
# No GITHUB_TOKEN = uses OAuth
```

### Hybrid (Switch Between)
```bash
# .env
GITHUB_TOKEN=ghp_abc123...        # Local: uncomment this
# GITHUB_TOKEN=ghp_abc123...      # Production: comment this out
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=9e32c1...
```

## Testing GitHub Tools

### With Local Token
```bash
# 1. Add token to .env
echo "GITHUB_TOKEN=ghp_your_token" >> .env

# 2. Start server
make dev

# 3. Test (agent will use your token)
curl -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"List my GitHub repositories","session_id":"test"}' \
  --no-buffer
```

### With OAuth
```bash
# 1. Setup OAuth provider (one-time)
make setup-github

# 2. Start server
make dev

# 3. User goes through OAuth flow
# Agent gets user-specific token automatically
```

## Security Best Practices

### Local Development
- ✅ Never commit `.env` with tokens (already in `.gitignore`)
- ✅ Use tokens with minimal required scopes
- ✅ Rotate tokens regularly
- ✅ Delete tokens when done testing

### Production
- ✅ Use OAuth for all production deployments
- ✅ Store OAuth secrets in AWS Secrets Manager
- ✅ Use AgentCore Identity for token management
- ✅ Implement token refresh logic
- ✅ Monitor token usage

## Token Scopes Required

| Tool | Scope Needed | Why |
|------|--------------|-----|
| `list_github_repos` | `repo`, `read:user` | Read user's repos |
| `get_repo_info` | `repo`, `read:user` | Read repo details |
| `list_github_issues` | `repo`, `read:user` | Read issues |
| `create_github_issue` | `repo` | Create issues |
| `create_pull_request` | `repo` | Create PRs |

**Minimum scopes**: `repo`, `read:user`

## Troubleshooting

### "No GitHub authentication available"
**Problem**: Neither local token nor OAuth token found

**Solution**:
```bash
# Check .env has either:
GITHUB_TOKEN=ghp_...  # For local
# OR
GITHUB_CLIENT_ID=...  # For OAuth
```

### "Bad credentials" Error
**Problem**: Token is invalid or expired

**Solution**:
```bash
# For local token:
# 1. Check token at https://github.com/settings/tokens
# 2. Regenerate if expired
# 3. Update .env

# For OAuth:
# 1. Check OAuth app at https://github.com/settings/developers
# 2. Verify client ID/secret
# 3. Re-run: make setup-github
```

### Local Token Not Working
**Problem**: Set GITHUB_TOKEN but getting OAuth errors

**Solution**:
```bash
# 1. Verify token format (should start with ghp_)
echo $GITHUB_TOKEN

# 2. Check token scopes at https://github.com/settings/tokens

# 3. Restart server to reload .env
make dev
```

## Migration Path

### Start → Production Path

**Week 1-2: Development**
- Use local token (`GITHUB_TOKEN`)
- Test all GitHub tools
- Validate functionality

**Week 3: Pre-Production**
- Set up GitHub OAuth App
- Configure AgentCore Identity
- Test OAuth flow with test users

**Week 4: Production**
- Remove `GITHUB_TOKEN` from .env
- Deploy with OAuth only
- Monitor user authentication

**Benefit**: Smooth transition, test everything locally first!

## Code Example

The hybrid authentication is transparent to your code:

```python
# The decorator handles everything automatically
@github_auth_hybrid(scopes=['repo', 'read:user'])
async def list_github_repos(*, access_token: str, limit: int = 10):
    # access_token is automatically:
    # - Local token if GITHUB_TOKEN is set
    # - OAuth token if using OAuth flow
    g = Github(access_token)
    ...
```

No code changes needed when switching modes!
