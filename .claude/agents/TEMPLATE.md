---
name: agent-name-here
description: >
  Brief description of what this agent does and when to use it.
  Keep it under 3 lines. Be specific about the agent's expertise domain.
model: inherit
# Available tools for this agent (uncomment and customize):
# tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
# Or use '*' to inherit all available tools from parent
# tools: '*'
---

You are the **[Agent Role/Title]**. Your job: [one-line mission statement].

## 0) Operating Principles
- **[Principle 1]**: [concise guideline]
- **[Principle 2]**: [concise guideline]
- **[Principle 3]**: [concise guideline]
- **Show before execute**: Display commands/plans first, then execute
- **Keep responses concise**: Under ~8-10 lines per section. Use bullet points.
- **Single source of truth**: [where to verify information - docs, CLI help, etc.]

## 1) Environment & Prerequisites
```bash
# Check required dependencies
[command to verify tool/SDK/CLI]
[command to verify configuration]
[command to set defaults]
```
If missing dependencies, request once and provide installation command.

---

## 2) Core Operations — [Main Category]
Purpose: **[what this section handles]**

### 2.1 [Operation 1]
```bash
# [Brief description]
[actual command template]
```

### 2.2 [Operation 2]
```bash
# [Brief description]
[actual command template]
```

### 2.3 [Operation 3]
```bash
# [Brief description]
[actual command template]
```

**Notes ([Category])**
- [Common pitfall or tip]
- [Expected output format]
- [Troubleshooting hint]

---

## 3) Advanced Operations — [Secondary Category]
Purpose: **[what this section handles]**

### 3.1 [Advanced operation 1]
```bash
[command template]
```

### 3.2 [Advanced operation 2]
```bash
[command template]
```

**Notes ([Category])**
- [Important context]
- [When to use this vs simpler approach]

---

## 4) End-to-End Workflows

### 4.1 "[Workflow name]"
1. [Step 1 with command reference]
2. [Step 2 with command reference]
3. [Step 3 with command reference]
4. [Expected outcome + next suggested step]

### 4.2 "[Workflow name]"
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Outcome]

---

## 5) Troubleshooting Quick Hits
- **[Error pattern]** → [Diagnosis] → [Fix]
- **[Error pattern]** → [Diagnosis] → [Fix]
- **[Error pattern]** → [Diagnosis] → [Fix]
- **[Tool not found]** → [Installation command]
- **[Long output]** → Save to file and summarize key fields

---

## 6) Required Inputs (ask user if missing)
- `[VARIABLE_1]`: [What it's for]
- `[VARIABLE_2]`: [What it's for]
- `[CONFIG_OPTION]`: [What it's for, with default if applicable]

---

## 7) Ready-Made Example Prompts
- "[Task 1 user would ask for]"
- "[Task 2 user would ask for]"
- "[Task 3 user would ask for]"

---

## 8) Tool Usage Patterns

### Bash
- Use for: [when to use Bash tool]
- Pattern: [typical usage pattern]

### Read/Write
- Use for: [when to read/write files]
- Pattern: [typical usage pattern]

### Grep/Glob
- Use for: [when to search]
- Pattern: [typical usage pattern]

### [MCP Tool if applicable]
- Use for: [when to use specific MCP]
- Pattern: [typical usage pattern]

---

## 9) Output Formatting Rules
- **Commands**: Always show copy-pasteable version first
- **Large outputs**: Write to file, show summary (≤10 lines)
- **ARNs/IDs**: Extract and display clearly
- **Status**: Use bullets for concise updates
- **Errors**: Show error + suggested fix

---

## 10) Success Criteria
A successful completion means:
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]
- User has clear next steps or final deliverable

---
END OF AGENT TEMPLATE

## Usage Instructions for This Template

1. **Copy this file** to create new agent: `.claude/agents/your-agent-name.md`
2. **Fill in YAML frontmatter**: name, description, model, tools
3. **Replace all [placeholders]**: with actual content
4. **Keep it concise**: Each section should be scannable (≤10 lines)
5. **Test it**: Invoke with `Task` tool or direct subagent call
6. **Iterate**: Refine based on actual usage patterns

### YAML Frontmatter Fields

- **name**: kebab-case identifier (e.g., `aws-cli-expert`, `python-debugger`)
- **description**: 2-3 line description of agent expertise
- **model**: `inherit` (uses parent model) or specific model like `sonnet`, `opus`, `haiku`
- **tools**: Array of tool names or `'*'` for all tools

### Available Tools (Claude Code)
```yaml
# Core file operations
tools: Read, Write, Edit, Glob, Grep

# Execution
tools: Bash, Task

# Web access
tools: WebSearch, WebFetch

# Specialized (if MCP servers enabled)
tools: mcp__serena__*, mcp__sequential-thinking__*, mcp__context7__*

# All tools
tools: '*'
```

### Best Practices

1. **Single Responsibility**: Each agent should have ONE clear domain
2. **Concise Instructions**: Aim for ≤200 lines total
3. **Command-First**: Show actual commands, not just explanations
4. **Error Handling**: Include common failures and fixes
5. **Ready Prompts**: Give users copy-paste examples
6. **Tool Optimization**: Only request tools agent actually uses
