#!/bin/bash
# Test script for deployed AgentCore runtime
# Usage: ./scripts/test-runtime.sh [RUNTIME_ARN]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
  echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ${NC}  $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

# Load environment
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_ROOT/.env"

# Get runtime ARN
RUNTIME_ARN="$1"

if [ -z "$RUNTIME_ARN" ]; then
  print_info "No runtime ARN provided, attempting to find it..."

  # Try to find runtime
  RUNTIME_ARN=$(aws bedrock-agentcore-control list-agent-runtimes \
    --region "${AWS_REGION}" \
    2>/dev/null | jq -r '.agentRuntimes[] | select(.agentRuntimeName=="coding-agent-production") | .agentRuntimeArn' || echo "")

  if [ -z "$RUNTIME_ARN" ]; then
    print_error "Runtime ARN not found"
    echo "Usage: $0 <RUNTIME_ARN>"
    echo ""
    echo "Find your runtime ARN with:"
    echo "  aws bedrock-agentcore-control list-agent-runtimes --region ${AWS_REGION}"
    exit 1
  fi
fi

print_success "Using runtime: $RUNTIME_ARN"
echo ""

# Create test payloads
print_step "Creating test payloads..."

mkdir -p /tmp/agentcore-tests

# Test 1: Simple greeting
cat > /tmp/agentcore-tests/test1-greeting.json <<'EOF'
{
  "inputText": "Hello! Can you help me with Python code?",
  "sessionId": "test-session-001"
}
EOF
print_success "Test 1: Simple greeting"

# Test 2: List GitHub repos
cat > /tmp/agentcore-tests/test2-github.json <<'EOF'
{
  "inputText": "List my GitHub repositories",
  "sessionId": "test-session-002"
}
EOF
print_success "Test 2: GitHub integration"

# Test 3: Code analysis
cat > /tmp/agentcore-tests/test3-code.json <<'EOF'
{
  "inputText": "Explain this Python code: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
  "sessionId": "test-session-003"
}
EOF
print_success "Test 3: Code explanation"

echo ""

# Run tests
run_test() {
  local test_name=$1
  local payload_file=$2
  local output_file=$3

  print_step "Running: $test_name"

  if aws bedrock-agentcore invoke-agent-runtime \
    --region "${AWS_REGION}" \
    --agent-runtime-arn "$RUNTIME_ARN" \
    --payload "fileb://$payload_file" \
    "$output_file" 2>/tmp/test-error.log; then

    print_success "Test completed"

    # Show response excerpt
    if [ -f "$output_file" ]; then
      echo -e "${BLUE}Response excerpt:${NC}"
      head -n 20 "$output_file" | sed 's/^/  /'
      echo ""
    fi
  else
    print_error "Test failed"
    cat /tmp/test-error.log
    echo ""
    return 1
  fi
}

# Execute tests
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Running Agent Runtime Tests                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1
if run_test "Test 1: Simple Greeting" \
   "/tmp/agentcore-tests/test1-greeting.json" \
   "/tmp/agentcore-tests/response1.json"; then
  ((TESTS_PASSED++))
else
  ((TESTS_FAILED++))
fi

# Test 2
if run_test "Test 2: GitHub Integration" \
   "/tmp/agentcore-tests/test2-github.json" \
   "/tmp/agentcore-tests/response2.json"; then
  ((TESTS_PASSED++))
else
  ((TESTS_FAILED++))
fi

# Test 3
if run_test "Test 3: Code Explanation" \
   "/tmp/agentcore-tests/test3-code.json" \
   "/tmp/agentcore-tests/response3.json"; then
  ((TESTS_PASSED++))
else
  ((TESTS_FAILED++))
fi

# Summary
echo ""
print_step "Test Summary"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  print_success "All tests passed!"
  echo ""
  echo "View detailed responses:"
  echo "  cat /tmp/agentcore-tests/response*.json | jq"
  echo ""
  echo "View runtime logs:"
  echo "  aws logs tail /aws/bedrock/agentcore/coding-agent-production \\"
  echo "    --region ${AWS_REGION} --follow"
  echo ""
  exit 0
else
  print_error "Some tests failed. Check logs for details."
  echo ""
  echo "Debug commands:"
  echo "  1. Check runtime status:"
  echo "     aws bedrock-agentcore-control get-agent-runtime \\"
  echo "       --region ${AWS_REGION} \\"
  echo "       --agent-runtime-identifier coding-agent-production"
  echo ""
  echo "  2. View CloudWatch logs:"
  echo "     aws logs tail /aws/bedrock/agentcore/coding-agent-production \\"
  echo "       --region ${AWS_REGION} --follow"
  echo ""
  exit 1
fi
