#!/bin/bash
# Release Notes Generation Script
# Generates release notes from git commits and pull requests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_OUTPUT_FILE="release-notes.md"
REPOSITORY_NAME="partshub"

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS] [PREVIOUS_TAG] [CURRENT_TAG]"
    echo ""
    echo "Generate release notes from git commits and pull requests."
    echo ""
    echo "Options:"
    echo "  -o, --output FILE    Output file (default: $DEFAULT_OUTPUT_FILE)"
    echo "  -r, --repo NAME      Repository name (default: $REPOSITORY_NAME)"
    echo "  -f, --format FORMAT  Output format: markdown, text, json (default: markdown)"
    echo "  -t, --template FILE  Use custom template file"
    echo "  --no-prs            Skip pull request information"
    echo "  --no-contributors   Skip contributor information"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 v1.0.0 v1.1.0                    # Generate notes between tags"
    echo "  $0 --output CHANGELOG.md v1.0.0     # From tag to HEAD"
    echo "  $0 --format json > release.json     # Output as JSON"
    echo ""
}

# Parse command line arguments
PREVIOUS_TAG=""
CURRENT_TAG=""
OUTPUT_FILE="$DEFAULT_OUTPUT_FILE"
OUTPUT_FORMAT="markdown"
TEMPLATE_FILE=""
INCLUDE_PRS=true
INCLUDE_CONTRIBUTORS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -r|--repo)
            REPOSITORY_NAME="$2"
            shift 2
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -t|--template)
            TEMPLATE_FILE="$2"
            shift 2
            ;;
        --no-prs)
            INCLUDE_PRS=false
            shift
            ;;
        --no-contributors)
            INCLUDE_CONTRIBUTORS=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$PREVIOUS_TAG" ]; then
                PREVIOUS_TAG="$1"
            elif [ -z "$CURRENT_TAG" ]; then
                CURRENT_TAG="$1"
            else
                echo -e "${RED}❌ Too many arguments${NC}"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Function to get the latest tag
get_latest_tag() {
    git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1
}

# Function to get the previous tag
get_previous_tag() {
    local current_tag=$1
    if [ -z "$current_tag" ]; then
        git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -2 | tail -1
    else
        git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | grep -A1 "^$current_tag$" | tail -1
    fi
}

# Set default values if not provided
if [ -z "$CURRENT_TAG" ]; then
    CURRENT_TAG=$(get_latest_tag)
    if [ -z "$CURRENT_TAG" ]; then
        CURRENT_TAG="HEAD"
    fi
fi

if [ -z "$PREVIOUS_TAG" ]; then
    PREVIOUS_TAG=$(get_previous_tag "$CURRENT_TAG")
fi

echo -e "${GREEN}📝 Generating Release Notes${NC}"
echo "============================="
echo -e "${BLUE}Repository:${NC} $REPOSITORY_NAME"
echo -e "${BLUE}From:${NC} $PREVIOUS_TAG"
echo -e "${BLUE}To:${NC} $CURRENT_TAG"
echo -e "${BLUE}Format:${NC} $OUTPUT_FORMAT"
echo -e "${BLUE}Output:${NC} $OUTPUT_FILE"
echo ""

# Function to get commits between tags
get_commits() {
    local from_tag=$1
    local to_tag=$2

    if [ -z "$from_tag" ]; then
        git log --pretty=format:"%H|%s|%an|%ae|%ad" --date=short "$to_tag"
    else
        git log --pretty=format:"%H|%s|%an|%ae|%ad" --date=short "$from_tag..$to_tag"
    fi
}

# Function to categorize commits
categorize_commits() {
    local commits="$1"

    echo "$commits" | while IFS='|' read -r hash subject author email date; do
        local category="other"
        local emoji="🔧"

        # Categorize based on commit message
        if [[ $subject =~ ^feat(\(.+\))?!?: ]]; then
            category="features"
            emoji="🚀"
        elif [[ $subject =~ ^fix(\(.+\))?!?: ]]; then
            category="bugfixes"
            emoji="🐛"
        elif [[ $subject =~ ^docs(\(.+\))?!?: ]]; then
            category="documentation"
            emoji="📚"
        elif [[ $subject =~ ^test(\(.+\))?!?: ]]; then
            category="tests"
            emoji="🧪"
        elif [[ $subject =~ ^chore(\(.+\))?!?: ]]; then
            category="chores"
            emoji="🔧"
        elif [[ $subject =~ ^refactor(\(.+\))?!?: ]]; then
            category="refactoring"
            emoji="♻️"
        elif [[ $subject =~ ^perf(\(.+\))?!?: ]]; then
            category="performance"
            emoji="⚡"
        elif [[ $subject =~ ^ci(\(.+\))?!?: ]]; then
            category="ci"
            emoji="👷"
        elif [[ $subject =~ ^build(\(.+\))?!?: ]]; then
            category="build"
            emoji="📦"
        elif [[ $subject =~ ^style(\(.+\))?!?: ]]; then
            category="style"
            emoji="💄"
        fi

        echo "$category|$emoji|$hash|$subject|$author|$email|$date"
    done
}

# Function to get pull request information
get_pr_info() {
    local hash=$1
    if command -v gh &> /dev/null && $INCLUDE_PRS; then
        # Try to find PR for this commit
        pr_number=$(gh pr list --state merged --search "$hash" --json number --jq '.[0].number' 2>/dev/null || echo "")
        if [ ! -z "$pr_number" ]; then
            echo " (#$pr_number)"
        fi
    fi
    echo ""
}

# Function to generate markdown output
generate_markdown() {
    local commits="$1"
    local version="$2"

    echo "# Release $version"
    echo ""
    echo "Released on $(date +%Y-%m-%d)"
    echo ""

    if [ ! -z "$PREVIOUS_TAG" ]; then
        echo "## Changes since $PREVIOUS_TAG"
        echo ""
    else
        echo "## Initial Release"
        echo ""
        echo "This is the first release of $REPOSITORY_NAME."
        echo ""
    fi

    # Group commits by category
    local categorized_commits
    categorized_commits=$(echo "$commits" | categorize_commits)

    # Features
    local features
    features=$(echo "$categorized_commits" | grep "^features|" || true)
    if [ ! -z "$features" ]; then
        echo "### 🚀 Features"
        echo ""
        echo "$features" | while IFS='|' read -r category emoji hash subject author email date; do
            pr_info=$(get_pr_info "$hash")
            echo "- $subject (\`${hash:0:7}\`)$pr_info"
        done
        echo ""
    fi

    # Bug fixes
    local bugfixes
    bugfixes=$(echo "$categorized_commits" | grep "^bugfixes|" || true)
    if [ ! -z "$bugfixes" ]; then
        echo "### 🐛 Bug Fixes"
        echo ""
        echo "$bugfixes" | while IFS='|' read -r category emoji hash subject author email date; do
            pr_info=$(get_pr_info "$hash")
            echo "- $subject (\`${hash:0:7}\`)$pr_info"
        done
        echo ""
    fi

    # Documentation
    local documentation
    documentation=$(echo "$categorized_commits" | grep "^documentation|" || true)
    if [ ! -z "$documentation" ]; then
        echo "### 📚 Documentation"
        echo ""
        echo "$documentation" | while IFS='|' read -r category emoji hash subject author email date; do
            pr_info=$(get_pr_info "$hash")
            echo "- $subject (\`${hash:0:7}\`)$pr_info"
        done
        echo ""
    fi

    # Performance improvements
    local performance
    performance=$(echo "$categorized_commits" | grep "^performance|" || true)
    if [ ! -z "$performance" ]; then
        echo "### ⚡ Performance Improvements"
        echo ""
        echo "$performance" | while IFS='|' read -r category emoji hash subject author email date; do
            pr_info=$(get_pr_info "$hash")
            echo "- $subject (\`${hash:0:7}\`)$pr_info"
        done
        echo ""
    fi

    # Other changes
    local other
    other=$(echo "$categorized_commits" | grep -v "^features|" | grep -v "^bugfixes|" | grep -v "^documentation|" | grep -v "^performance|" || true)
    if [ ! -z "$other" ]; then
        echo "### 🔧 Other Changes"
        echo ""
        echo "$other" | head -10 | while IFS='|' read -r category emoji hash subject author email date; do
            pr_info=$(get_pr_info "$hash")
            echo "- $subject (\`${hash:0:7}\`)$pr_info"
        done
        echo ""
    fi

    # Contributors
    if $INCLUDE_CONTRIBUTORS; then
        echo "## Contributors"
        echo ""
        if [ ! -z "$PREVIOUS_TAG" ]; then
            git log --pretty=format:"- %an" "$PREVIOUS_TAG..$CURRENT_TAG" | sort | uniq
        else
            git log --pretty=format:"- %an" | sort | uniq
        fi
        echo ""
        echo ""
    fi

    # Docker images section
    echo "## Docker Images"
    echo ""
    echo "- Backend: \`ghcr.io/$REPOSITORY_NAME-backend:$version\`"
    echo "- Frontend: \`ghcr.io/$REPOSITORY_NAME-frontend:$version\`"
    echo ""

    # Documentation links
    echo "## Documentation"
    echo ""
    echo "- [Release Documentation](https://github.com/$REPOSITORY_NAME/tree/$version/docs)"
    echo "- [API Documentation](https://$REPOSITORY_NAME.github.io/partshub/)"
    echo ""

    # Installation instructions
    echo "## Installation"
    echo ""
    echo "\`\`\`bash"
    echo "# Pull and run the images"
    echo "docker pull ghcr.io/$REPOSITORY_NAME-backend:$version"
    echo "docker pull ghcr.io/$REPOSITORY_NAME-frontend:$version"
    echo "\`\`\`"
}

# Function to generate JSON output
generate_json() {
    local commits="$1"
    local version="$2"

    echo "{"
    echo "  \"version\": \"$version\","
    echo "  \"release_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"previous_version\": \"$PREVIOUS_TAG\","
    echo "  \"commits\": ["

    local first=true
    echo "$commits" | categorize_commits | while IFS='|' read -r category emoji hash subject author email date; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        echo "    {"
        echo "      \"hash\": \"$hash\","
        echo "      \"subject\": \"$subject\","
        echo "      \"author\": \"$author\","
        echo "      \"email\": \"$email\","
        echo "      \"date\": \"$date\","
        echo "      \"category\": \"$category\""
        echo -n "    }"
    done

    echo ""
    echo "  ]"
    echo "}"
}

# Main execution
main() {
    echo -e "${YELLOW}🔍 Collecting commit information...${NC}"

    # Get commits
    local commits
    commits=$(get_commits "$PREVIOUS_TAG" "$CURRENT_TAG")

    if [ -z "$commits" ]; then
        echo -e "${YELLOW}⚠️  No commits found between $PREVIOUS_TAG and $CURRENT_TAG${NC}"
        exit 0
    fi

    echo -e "${GREEN}✅ Found $(echo "$commits" | wc -l) commits${NC}"

    # Determine version for output
    local version="$CURRENT_TAG"
    if [ "$version" = "HEAD" ]; then
        # Try to get version from pyproject.toml
        if [ -f "pyproject.toml" ]; then
            version=$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/' || echo "unreleased")
        else
            version="unreleased"
        fi
    fi

    echo -e "${YELLOW}📝 Generating release notes...${NC}"

    # Generate output based on format
    case $OUTPUT_FORMAT in
        "markdown"|"md")
            generate_markdown "$commits" "$version" > "$OUTPUT_FILE"
            ;;
        "json")
            generate_json "$commits" "$version" > "$OUTPUT_FILE"
            ;;
        "text")
            generate_markdown "$commits" "$version" | sed 's/^#\+\s*//' | sed 's/\*\*//' | sed 's/`//g' > "$OUTPUT_FILE"
            ;;
        *)
            echo -e "${RED}❌ Unknown format: $OUTPUT_FORMAT${NC}"
            exit 1
            ;;
    esac

    echo -e "${GREEN}🎉 Release notes generated successfully!${NC}"
    echo -e "${BLUE}Output file:${NC} $OUTPUT_FILE"
    echo ""

    # Show preview
    if [ "$OUTPUT_FORMAT" = "markdown" ]; then
        echo -e "${YELLOW}📖 Preview:${NC}"
        echo "============"
        head -20 "$OUTPUT_FILE"
        if [ $(wc -l < "$OUTPUT_FILE") -gt 20 ]; then
            echo "..."
            echo "(truncated - see $OUTPUT_FILE for full content)"
        fi
    fi
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Run main function
main "$@"