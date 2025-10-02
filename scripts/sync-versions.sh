#!/bin/bash
# Version Synchronization Script
# Synchronizes version from pyproject.toml to package.json files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 Version Synchronization Script${NC}"
echo "====================================="

# Function to extract version from pyproject.toml
get_pyproject_version() {
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ pyproject.toml not found${NC}"
        exit 1
    fi

    VERSION=$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    if [ -z "$VERSION" ]; then
        echo -e "${RED}❌ Version not found in pyproject.toml${NC}"
        exit 1
    fi

    echo "$VERSION"
}

# Function to update package.json version
update_package_json() {
    local file_path=$1
    local version=$2

    if [ ! -f "$file_path" ]; then
        echo -e "${YELLOW}⚠️  $file_path not found, skipping${NC}"
        return 0
    fi

    echo -e "${YELLOW}🔄 Updating $file_path${NC}"

    # Create a backup
    cp "$file_path" "$file_path.backup"

    # Update version using jq if available, otherwise use sed
    if command -v jq &> /dev/null; then
        jq --arg version "$version" '.version = $version' "$file_path" > "$file_path.tmp"
        mv "$file_path.tmp" "$file_path"
    else
        # Fallback to sed
        sed -i.tmp "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$file_path"
        rm -f "$file_path.tmp"
    fi

    echo -e "${GREEN}✅ Updated $file_path to version $version${NC}"
}

# Function to update mkdocs.yml site name with version
update_mkdocs_version() {
    local version=$1

    if [ ! -f "mkdocs.yml" ]; then
        echo -e "${YELLOW}⚠️  mkdocs.yml not found, skipping${NC}"
        return 0
    fi

    echo -e "${YELLOW}🔄 Updating mkdocs.yml site name${NC}"

    # Update site_name to include version
    sed -i.backup "s/site_name: .*/site_name: 'PartsHub Documentation (v$version)'/" mkdocs.yml

    echo -e "${GREEN}✅ Updated mkdocs.yml site name to include version $version${NC}"
}

# Function to verify version consistency
verify_versions() {
    local expected_version=$1
    local errors=0

    echo -e "${YELLOW}🔍 Verifying version consistency${NC}"

    # Check frontend/package.json
    if [ -f "frontend/package.json" ]; then
        FRONTEND_VERSION=$(grep '"version"' frontend/package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
        if [ "$FRONTEND_VERSION" != "$expected_version" ]; then
            echo -e "${RED}❌ Frontend version mismatch: expected $expected_version, got $FRONTEND_VERSION${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Frontend version correct: $FRONTEND_VERSION${NC}"
        fi
    fi

    # Check package.json (if exists in root)
    if [ -f "package.json" ]; then
        ROOT_VERSION=$(grep '"version"' package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
        if [ "$ROOT_VERSION" != "$expected_version" ]; then
            echo -e "${RED}❌ Root package.json version mismatch: expected $expected_version, got $ROOT_VERSION${NC}"
            errors=$((errors + 1))
        else
            echo -e "${GREEN}✅ Root package.json version correct: $ROOT_VERSION${NC}"
        fi
    fi

    return $errors
}

# Function to show version status
show_version_status() {
    echo -e "${GREEN}📋 Current Version Status${NC}"
    echo "========================="

    # PyProject version
    if [ -f "pyproject.toml" ]; then
        PYPROJECT_VERSION=$(get_pyproject_version)
        echo "PyProject: $PYPROJECT_VERSION"
    fi

    # Frontend version
    if [ -f "frontend/package.json" ]; then
        FRONTEND_VERSION=$(grep '"version"' frontend/package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
        echo "Frontend:  $FRONTEND_VERSION"
    fi

    # Root package.json version
    if [ -f "package.json" ]; then
        ROOT_VERSION=$(grep '"version"' package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
        echo "Root:      $ROOT_VERSION"
    fi

    echo ""
}

# Main execution
main() {
    local command=${1:-"sync"}

    case $command in
        "status")
            show_version_status
            ;;
        "verify")
            PYPROJECT_VERSION=$(get_pyproject_version)
            verify_versions "$PYPROJECT_VERSION"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}🎉 All versions are synchronized!${NC}"
            else
                echo -e "${RED}💥 Version synchronization issues found${NC}"
                exit 1
            fi
            ;;
        "sync")
            echo -e "${YELLOW}🚀 Starting version synchronization${NC}"

            # Get the master version from pyproject.toml
            PYPROJECT_VERSION=$(get_pyproject_version)
            echo -e "${GREEN}📌 Master version from pyproject.toml: $PYPROJECT_VERSION${NC}"

            # Update all package.json files
            update_package_json "frontend/package.json" "$PYPROJECT_VERSION"
            update_package_json "package.json" "$PYPROJECT_VERSION"

            # Update mkdocs.yml
            update_mkdocs_version "$PYPROJECT_VERSION"

            # Verify the synchronization
            echo ""
            verify_versions "$PYPROJECT_VERSION"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}🎉 Version synchronization completed successfully!${NC}"

                # Clean up backup files
                rm -f frontend/package.json.backup package.json.backup mkdocs.yml.backup
            else
                echo -e "${RED}💥 Synchronization completed with errors${NC}"
                exit 1
            fi
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  sync     Synchronize versions from pyproject.toml to all files (default)"
            echo "  status   Show current version status across all files"
            echo "  verify   Verify that all versions are synchronized"
            echo "  help     Show this help message"
            echo ""
            echo "This script treats pyproject.toml as the single source of truth for versioning."
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@"