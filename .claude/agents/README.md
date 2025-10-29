# Claude Code Subagents

This directory contains specialized Claude Code subagents for AWS development workflows.

## Available Agents

### 1. **TEMPLATE.md** (Blueprint)
- **Purpose**: Template for creating new subagents
- **Use**: Copy this to create your own specialized agents
- **Format**: YAML frontmatter + structured markdown instructions

### 2. **aws-strands-agent.md** (Strands SDK Expert)
- **Purpose**: AWS Strands Agents SDK, AgentCore Gateway, streaming applications
- **Expertise**: Functional Python patterns, MCP integration, FastAPI streaming
- **Use when**: Building streaming agents, setting up AgentCore Gateway, OAuth providers
- **Triggers**: `--strands`, keywords: "strands", "gateway", "streaming agent", "mcp integration"

### 3. **bedrock-agentcore-cli.md** (CLI Operator)
- **Purpose**: AWS CLI expert for Bedrock AgentCore operations
- **Expertise**: Data plane (`bedrock-agentcore`), Control plane (`bedrock-agentcore-control`), Starter Toolkit
- **Use when**: Running AWS CLI commands, provisioning gateways, managing runtimes
- **Triggers**: `--agentcore-cli`, keywords: "gateway", "runtime", "aws cli", "invoke"

---

## How to Use Subagents

### Method 1: Via Task Tool (Recommended)
```javascript
// In your Claude Code conversation
Task({
  subagent_type: "aws-strands-agent",
  prompt: "Bootstrap a new Strands Agent with GitHub MCP integration",
  description: "Create Strands agent project"
})
```

### Method 2: Via Agent File Reference
```
Tell Claude Code: "Use the aws-strands-agent to help me set up a streaming agent"
```

### Method 3: Auto-Activation via Keywords
The agents automatically activate when you use their trigger keywords:
- "Set up AgentCore Gateway" → triggers aws-strands-agent
- "Invoke runtime ARN" → triggers bedrock-agentcore-cli

---

## Creating Your Own Subagent

1. **Copy the template**
   ```bash
   cp .claude/agents/TEMPLATE.md .claude/agents/your-agent-name.md
   ```

2. **Fill in YAML frontmatter**
   ```yaml
   ---
   name: your-agent-name
   description: >
     What this agent does (2-3 lines)
   model: inherit
   tools: Bash, Read, Write, Grep, Glob
   ---
   ```

3. **Write concise instructions**
   - Keep sections ≤10 lines
   - Show commands before explanations
   - Provide copy-pasteable examples
   - Include troubleshooting section

4. **Test it**
   ```
   Ask Claude: "Use your-agent-name to [task]"
   ```

---

## Subagent Best Practices

### YAML Frontmatter
```yaml
name: kebab-case-name          # File name without .md
description: >                  # Multi-line description
  Single responsibility focus
  Keep under 3 lines
model: inherit                  # Or: sonnet, opus, haiku
tools: Bash, Read, Write        # Only tools you need
# OR for all tools:
tools: '*'
```

### Tools Available
- **File ops**: `Read, Write, Edit, Glob, Grep`
- **Execution**: `Bash, Task`
- **Web**: `WebSearch, WebFetch`
- **MCP**: `mcp__serena__*, mcp__sequential-thinking__*, mcp__context7__*`
- **All**: `'*'`

### Content Structure
1. **Operating Principles** (≤5 bullets)
2. **Environment Setup** (verify commands)
3. **Core Operations** (command templates)
4. **Workflows** (end-to-end recipes)
5. **Troubleshooting** (common errors + fixes)
6. **Ready-Made Prompts** (copy-paste examples)

### Writing Style
- ✅ **Concise**: ≤10 lines per section
- ✅ **Commands first**: Show, then explain
- ✅ **Copy-pasteable**: Real commands, not pseudocode
- ✅ **Actionable**: Every section has next steps
- ❌ **No verbosity**: Avoid long explanations
- ❌ **No theory**: Focus on practical operations

---

## Integration with SuperClaude Framework

These subagents work with your SuperClaude framework:

### Mode Compatibility
- **--brainstorm**: Use before creating subagent to clarify requirements
- **--introspect**: Debug why subagent isn't activating
- **--task-manage**: Subagents auto-create TodoWrite lists for multi-step workflows
- **--orchestrate**: Subagents optimize tool selection automatically

### MCP Integration
Subagents can use MCP servers:
- **Context7**: For official AWS documentation lookup
- **Sequential**: For complex multi-step reasoning
- **Serena**: For project memory and session persistence
- **Tavily**: For current AWS best practices research

### Example Combined Usage
```
User: "Use aws-strands-agent with --think to design a production-ready agent architecture"

Result:
1. Sequential MCP analyzes requirements
2. aws-strands-agent creates functional Python structure
3. Context7 provides AWS best practices
4. Serena stores architecture in project memory
```

---

## Subagent Activation Matrix

| Task | Subagent | Alternative |
|------|----------|-------------|
| Set up Gateway | aws-strands-agent | bedrock-agentcore-cli |
| Invoke runtime | bedrock-agentcore-cli | Manual AWS CLI |
| Create streaming agent | aws-strands-agent | Native Claude |
| List resources | bedrock-agentcore-cli | Manual AWS CLI |
| Design architecture | aws-strands-agent + Sequential | Native Claude |

---

## Quick Start Examples

### Example 1: Create Gateway
```
User: "Use bedrock-agentcore-cli to create a gateway named 'prod-gw' and show me the ARN"

Agent:
1. Verifies AWS credentials and region
2. Shows command: aws bedrock-agentcore-control create-gateway ...
3. Executes command
4. Extracts ARN from output
5. Suggests next steps (add targets, configure auth)
```

### Example 2: Bootstrap Strands Agent
```
User: "Use aws-strands-agent to bootstrap a new project with GitHub MCP"

Agent:
1. Creates project structure
2. Sets up Gateway with OAuth provider
3. Creates functional Python modules
4. Adds streaming FastAPI endpoint
5. Provides test commands
```

### Example 3: Combined Workflow
```
User: "Design and deploy a streaming agent with GitHub integration"

Workflow:
1. --brainstorm mode: Clarify requirements
2. aws-strands-agent: Design architecture
3. bedrock-agentcore-cli: Provision Gateway
4. aws-strands-agent: Generate code
5. bedrock-agentcore-cli: Deploy and test
```

---

## Troubleshooting Subagents

### Agent Not Activating
- Check file is in `.claude/agents/` directory
- Verify YAML frontmatter is valid
- Ensure `name` in YAML matches filename (without .md)
- Try explicit activation: "Use [agent-name] to..."

### Agent Using Wrong Tools
- Check `tools:` list in YAML frontmatter
- Verify tools are available in Claude Code
- Use `tools: '*'` to inherit all tools

### Agent Not Following Instructions
- Ensure instructions are concise (≤10 lines per section)
- Use imperative commands: "Run X", not "You should run X"
- Provide concrete examples, not abstract descriptions
- Test with simple task first

---

## Directory Structure

```
.claude/agents/
├── README.md                      # This file
├── TEMPLATE.md                    # Blueprint for new agents
├── aws-strands-agent.md          # Strands SDK expert
├── bedrock-agentcore-cli.md      # AWS CLI operator
└── [your-custom-agent].md        # Your agents here
```

---

## Contributing New Agents

1. Use TEMPLATE.md as starting point
2. Follow naming convention: `domain-specific-name.md`
3. Keep total length ≤400 lines
4. Test with at least 3 real scenarios
5. Document in this README

### Suggested Future Agents
- **aws-iam-expert**: IAM policy creation and troubleshooting
- **lambda-deployer**: Lambda function deployment and configuration
- **cloudformation-builder**: IaC template generation
- **bedrock-model-tester**: Model invocation and testing
- **observability-setup**: CloudWatch, X-Ray, logging configuration

---

## Resources

- [Claude Code Docs](https://docs.anthropic.com/claude/docs)
- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Strands Agents SDK](https://github.com/aws-samples/sample-strands-agent-chatbot)
- [SuperClaude Framework](.claude/CLAUDE.md)

---

Last updated: 2025-10-29
