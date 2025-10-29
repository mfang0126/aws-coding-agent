# AWS MCP Tools - Integration Summary

## Available AWS MCP Servers

You have two AWS MCP servers configured:

### 1. AWS Documentation MCP Server (`awslabs.aws-documentation-mcp-server`)
**Tools:**
- `read_documentation` - Fetch and convert AWS documentation pages to markdown
- `search_documentation` - Search AWS documentation using official search API
- `recommend` - Get content recommendations for related AWS documentation

**Best For:**
- Looking up official AWS Bedrock AgentCore documentation
- Finding API references and feature explanations
- Discovering related documentation
- Checking latest AWS service updates

**Example Use Cases:**
```bash
search_documentation(search_phrase="bedrock agentcore gateway creation")
read_documentation(url="https://docs.aws.amazon.com/bedrock/latest/userguide/...")
recommend(url="https://docs.aws.amazon.com/bedrock/...")
```

---

### 2. AWS API MCP Server (`awslabs.aws-api-mcp-server`)
**Tools:**
- `call_aws` - Execute AWS CLI commands with validation and error handling
- `suggest_aws_commands` - Get AWS CLI command suggestions from natural language

**Best For:**
- Executing AWS CLI commands with better validation
- Automatic region handling (defaults to ap-southeast-2)
- Pagination support for large result sets
- Command discovery when uncertain about exact syntax

**Example Use Cases:**
```bash
# Execute commands
call_aws(cli_command="aws bedrock-agentcore-control list-gateways")

# Get suggestions when uncertain
suggest_aws_commands(query="Create a new AgentCore gateway with MCP protocol")
```

---

## Integration with bedrock-agentcore-cli Agent

The agent configuration has been updated to include:

### Tools Enabled:
```yaml
tools:
  # Core file and shell operations
  - Bash
  - Read, Write, Edit
  - Grep, Glob

  # AWS API MCP Server
  - mcp__awslabs_aws-api-mcp-server__call_aws
  - mcp__awslabs_aws-api-mcp-server__suggest_aws_commands

  # AWS Documentation MCP Server
  - mcp__awslabs_aws-documentation-mcp-server__read_documentation
  - mcp__awslabs_aws-documentation-mcp-server__search_documentation
  - mcp__awslabs_aws-documentation-mcp-server__recommend
```

### New Usage Guidance Added:

**Section 0.1: AWS MCP Tools Usage**
- Tool selection strategy
- When to use call_aws vs Bash
- When to use suggest_aws_commands
- Practical examples

**Updated Command Examples:**
- Data Plane (Section 2): Shows call_aws examples
- Control Plane (Section 3): Shows call_aws examples with pagination
- Command Discovery (Section 3.2a): Shows suggest_aws_commands usage

---

## Tool Selection Decision Tree

```
AWS CLI Command Needed?
├─ Know exact command/flags?
│  ├─ Yes → Use call_aws (preferred for validation)
│  └─ No → Use suggest_aws_commands first
│
├─ Need AWS documentation?
│  ├─ Know specific URL → Use read_documentation
│  ├─ Need to search → Use search_documentation
│  └─ Need related docs → Use recommend
│
├─ AgentCore Toolkit (agentcore CLI)?
│  └─ Use Bash (not supported by call_aws)
│
└─ Local file operations?
   └─ Use Bash, Read, Write, Edit
```

---

## Key Benefits

**call_aws vs raw Bash:**
- ✅ Automatic syntax validation before execution
- ✅ Better error messages with context
- ✅ Built-in pagination support (max_results parameter)
- ✅ Consistent region handling
- ✅ Prevents common CLI mistakes

**suggest_aws_commands:**
- ✅ Provides multiple command options with confidence scores
- ✅ Shows required parameters for each suggestion
- ✅ Helpful when user requests are vague
- ✅ Great for learning new AWS services

**AWS Documentation Tools:**
- ✅ Always up-to-date with official AWS documentation
- ✅ Faster than web search for AWS-specific queries
- ✅ Provides structured, markdown-formatted content
- ✅ Recommendation system finds related content

---

## Example Workflows

### Workflow 1: Create Gateway (Using MCP Tools)
```bash
# Step 1: If uncertain about command
suggest_aws_commands(query="Create AgentCore gateway with MCP protocol and IAM role")

# Step 2: Execute the suggested command
call_aws(cli_command="aws bedrock-agentcore-control create-gateway --name my-gw --protocol-type MCP --role-arn arn:aws:iam::123456789012:role/MyRole")

# Step 3: If need more info about gateways
search_documentation(search_phrase="bedrock agentcore gateway configuration")
```

### Workflow 2: List Resources (Using MCP Tools)
```bash
# List all gateways with automatic pagination
call_aws(cli_command="aws bedrock-agentcore-control list-gateways", max_results=50)

# List runtimes
call_aws(cli_command="aws bedrock-agentcore-control list-agent-runtimes")
```

### Workflow 3: Learning New Feature (Using Documentation)
```bash
# Search for information
search_documentation(search_phrase="bedrock agentcore memory management")

# Read specific documentation page
read_documentation(url="https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-memory.html")

# Get recommendations for related topics
recommend(url="https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-memory.html")
```

---

## When to Use Bash Instead

**Use Bash for:**
- AgentCore Toolkit (`agentcore`) commands
- Shell features: pipes (`|`), redirection (`>`, `>>`), command substitution (`$()`)
- Local file operations requiring shell scripting
- Complex command chains with `&&` or `;`

**Examples:**
```bash
# AgentCore Toolkit - use Bash
agentcore launch -a my-agent
agentcore gateway create-mcp-gateway --name "org-gw"

# Shell features - use Bash
aws bedrock-agentcore-control list-gateways | jq -r '.gateways[] | .gatewayId'

# File operations - use Bash
cat > request.json <<'JSON'
{ "inputText": "hello" }
JSON
```

---

## Updated Agent File Location

**File:** `/Users/freedom/ai/aws-coding-agent/.claude/agents/bedrock-agentcore-cli.md`

**Changes:**
1. Added tools configuration (lines 10-24)
2. Added Section 0.1: AWS MCP Tools Usage (lines 38-78)
3. Updated Section 2.2: Data Plane examples (lines 100-113)
4. Updated Section 3.1: Gateway creation examples (lines 131-147)
5. Updated Section 3.2: List resources examples (lines 150-172)
6. Added Section 3.2a: Command Discovery (lines 174-186)

---

## Next Steps

1. **Test the integration:**
   - Try using the agent with a simple command
   - Verify AWS MCP servers are working correctly

2. **Experiment with tools:**
   - Use `suggest_aws_commands` for command discovery
   - Try `search_documentation` for AWS Bedrock AgentCore docs
   - Compare `call_aws` vs Bash for AWS CLI commands

3. **Monitor performance:**
   - Check if MCP tools improve accuracy
   - Verify region handling works correctly
   - Test pagination with large result sets

4. **Update other agents:**
   - Consider adding AWS MCP tools to other agents if needed
   - Create specialized agents for specific AWS services
