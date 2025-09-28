#!/bin/bash
# Workflow Testing Script
# Tests GitHub Actions workflows locally and remotely

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 GitHub Workflows Testing Script${NC}"
echo "======================================"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI not found. Installing...${NC}"
    echo "Please install GitHub CLI: https://cli.github.com/"
    echo "Or use: brew install gh"
    exit 1
fi

# Check if act is installed for local testing
if ! command -v act &> /dev/null; then
    echo -e "${YELLOW}⚠️  Act not found. Installing...${NC}"
    echo "Please install act for local testing: https://github.com/nektos/act"
    echo "Or use: brew install act"
    echo "Continuing without local testing capability..."
fi

# Function to test workflow syntax
test_workflow_syntax() {
    local workflow_file=$1
    echo -e "${YELLOW}🔍 Testing syntax for $workflow_file${NC}"

    if [ ! -f "$workflow_file" ]; then
        echo -e "${RED}❌ Workflow file not found: $workflow_file${NC}"
        return 1
    fi

    # Basic YAML syntax check
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ YAML syntax valid${NC}"
        else
            echo -e "${RED}❌ YAML syntax invalid${NC}"
            return 1
        fi
    fi
}

# Function to run local workflow test with act
test_local_workflow() {
    local workflow_file=$1
    local event=${2:-"push"}

    echo -e "${YELLOW}🏃 Running local test for $workflow_file${NC}"

    if command -v act &> /dev/null; then
        echo "Testing with event: $event"
        act "$event" -W "$workflow_file" --dryrun
    else
        echo -e "${YELLOW}⚠️  Act not available, skipping local test${NC}"
    fi
}

# Function to validate workflow against GitHub
validate_remote_workflow() {
    local workflow_name=$1

    echo -e "${YELLOW}🌐 Validating workflow remotely: $workflow_name${NC}"

    # Check if workflow exists on GitHub
    if gh workflow list | grep -q "$workflow_name"; then
        echo -e "${GREEN}✅ Workflow found on GitHub${NC}"

        # Get latest run status
        local status=$(gh run list --workflow="$workflow_name" --limit=1 --json status -q '.[0].status' 2>/dev/null)
        if [ ! -z "$status" ]; then
            echo "Latest run status: $status"
        fi
    else
        echo -e "${YELLOW}⚠️  Workflow not found on GitHub (may not be pushed yet)${NC}"
    fi
}

# Main testing function
run_tests() {
    echo -e "${GREEN}📋 Available Tests:${NC}"
    echo "1. Test all workflow syntax"
    echo "2. Test CI workflow locally"
    echo "3. Test CD workflow locally"
    echo "4. Test Release workflow locally"
    echo "5. Validate remote workflows"
    echo "6. Run all tests"
    echo ""

    read -p "Select test (1-6): " choice

    case $choice in
        1)
            echo -e "${YELLOW}🔍 Testing all workflow syntax...${NC}"
            test_workflow_syntax ".github/workflows/ci.yml"
            test_workflow_syntax ".github/workflows/cd.yml"
            test_workflow_syntax ".github/workflows/release.yml"
            ;;
        2)
            test_workflow_syntax ".github/workflows/ci.yml"
            test_local_workflow ".github/workflows/ci.yml" "push"
            ;;
        3)
            test_workflow_syntax ".github/workflows/cd.yml"
            test_local_workflow ".github/workflows/cd.yml" "push"
            ;;
        4)
            test_workflow_syntax ".github/workflows/release.yml"
            test_local_workflow ".github/workflows/release.yml" "release"
            ;;
        5)
            validate_remote_workflow "ci"
            validate_remote_workflow "cd"
            validate_remote_workflow "release"
            ;;
        6)
            echo -e "${GREEN}🚀 Running all tests...${NC}"
            test_workflow_syntax ".github/workflows/ci.yml"
            test_workflow_syntax ".github/workflows/cd.yml"
            test_workflow_syntax ".github/workflows/release.yml"
            test_local_workflow ".github/workflows/ci.yml" "push"
            validate_remote_workflow "ci"
            validate_remote_workflow "cd"
            validate_remote_workflow "release"
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -d ".github/workflows" ]; then
    echo -e "${RED}❌ .github/workflows directory not found${NC}"
    echo "Please run this script from the repository root"
    exit 1
fi

# Run the tests
run_tests

echo -e "${GREEN}✅ Workflow testing complete!${NC}"