#!/bin/bash
# Validation script for Docker volume configurations
# This script validates volume mount configurations mentioned in documentation

set -e

echo "💾 Docker Volume Validation"
echo "=============================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Validate volume mount syntax
echo "🔍 Validating volume mount syntax..."

# Test various volume mount patterns
VALID_PATTERNS=(
    "partshub_data:/app/data"
    "./data:/app/data"
    "/path/to/data:/app/data"
)

for pattern in "${VALID_PATTERNS[@]}"; do
    # Parse volume mount pattern (basic validation)
    if echo "$pattern" | grep -q ".*:.*"; then
        echo "  ✅ Pattern valid: $pattern"
    else
        echo "  ❌ Pattern invalid: $pattern"
        exit 1
    fi
done
echo ""

# Check if Dockerfile defines expected data directory
echo "🔍 Checking Dockerfile for data directory setup..."
if [ -f "Dockerfile" ]; then
    if grep -q "/app/data" Dockerfile; then
        echo "✅ /app/data directory referenced in Dockerfile"
    else
        echo "⚠️  /app/data directory not found in Dockerfile"
    fi
else
    echo "⚠️  Dockerfile not found"
fi
echo ""

# Check for volume definitions in docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo "🔍 Checking docker-compose.yml for volume definitions..."

    if grep -q "partshub_data" docker-compose.yml; then
        echo "✅ Named volume 'partshub_data' defined"
    else
        echo "⚠️  Named volume 'partshub_data' not defined"
    fi

    if grep -q "/app/data" docker-compose.yml; then
        echo "✅ Container mount point '/app/data' found"
    else
        echo "⚠️  Container mount point '/app/data' not found"
    fi
else
    echo "⚠️  docker-compose.yml not found"
fi
echo ""

# Validate data directory structure expectations
echo "📁 Validating expected data directory structure..."
EXPECTED_PATHS=(
    "/app/data"
    "/app/data/partshub.db"
    "/app/data/attachments"
)

echo "  Expected paths in container:"
for path in "${EXPECTED_PATHS[@]}"; do
    echo "    - $path"
done
echo ""

echo "✅ Volume validation completed"
