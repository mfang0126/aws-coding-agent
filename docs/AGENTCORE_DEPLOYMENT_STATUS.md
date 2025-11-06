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

### Investigation Progress (2025-10-31 03:10 UTC)

**Root Cause Identified**: Port mismatch
- AWS docs require HTTP protocol on port **8080**
- App is running on port **8000** (MCP protocol port)
- `/ping` and `/invocations` endpoints are correctly implemented by BedrockAgentCoreApp

**Fix Attempted**: Modified `src/runtime.py` to call `app.run(port=8080, host="0.0.0.0")`
- BedrockAgentCoreApp.run() method signature confirms `port: int = 8080` as default
- However, logs still show `Uvicorn running on http://0.0.0.0:8000`
- Port parameter not taking effect despite correct syntax

**Possible Causes**:
1. Module invocation (`python -m src.runtime`) may not execute `__main__` block as expected
2. BedrockAgentCoreApp may auto-start on import with hardcoded port
3. Environment variable or config override not yet discovered
4. Agent toolkit CLI may inject additional runtime configuration

###Next Investigation Steps
1. Test module-level `app.run()` call outside conditional block
2. Check for BEDROCK_AGENTCORE_PORT or similar environment variables
3. Review bedrock-agentcore-starter-toolkit source for port configuration patterns
4. Test with simpler entrypoint to isolate Strands agent loading overhead
5. Contact AWS support or check GitHub issues for port configuration guidance
6. Examine successful template implementations from AWS samples
