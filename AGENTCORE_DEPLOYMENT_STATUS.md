# AgentCore Deployment Status

## Current State (2025-10-31)

### Deployment Info
- **Agent ARN**: `arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/coding_agent-sQJDwfGL8y`
- **Region**: ap-southeast-2
- **Platform**: linux/arm64 (AWS Graviton)
- **Status**: READY (per agentcore status)
- **Build Time**: ~50 seconds via CodeBuild

### What's Working
- ✅ AgentCore CLI configuration
- ✅ CodeBuild container builds
- ✅ ECR repository auto-creation
- ✅ IAM role auto-creation
- ✅ OAuth provider configuration (github-provider)
- ✅ Runtime starts successfully (logs confirm)
- ✅ Application reaches "startup complete" state

### Known Issues
- ❌ **Health check timeouts**: Invocations fail with "Runtime health check failed or timed out"
  - Agent status shows READY
  - Logs show successful startup
  - But actual invocations timeout
  - Attempted fix: Lazy agent loading (not yet resolved)

### Configuration
- Entrypoint: `src/runtime.py` with `@app.entrypoint` decorator
- Source path: `/Users/freedom/ai/aws-coding-agent` (project root)
- Dockerfile CMD: `python -m src.runtime`
- OAuth: Configured with workload `coding-agent-workload` and provider `github-provider`
- Memory: Disabled
- Observability: Disabled

### Files Modified/Created
- `src/runtime.py` - AgentCore wrapper with @app.entrypoint
- `src/pyproject.toml` - Copy of root pyproject.toml (required by CLI)
- `src/config.py` - Made GitHub OAuth fields optional
- `.bedrock_agentcore.yaml` - Deployment configuration
- `README.md` - Added complete deployment documentation

### Next Investigation Steps
1. Compare runtime.py with working template implementations
2. Check BedrockAgentCoreApp health check endpoint requirements
3. Verify port configuration (8000 vs 8080)
4. Test with minimal agent (no GitHub tools) to isolate issue
5. Check if agent creation is still blocking despite lazy loading
6. Review AgentCore docs for entrypoint streaming requirements
