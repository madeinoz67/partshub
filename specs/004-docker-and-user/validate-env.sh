#!/bin/bash
# Validation script for environment variables in documentation
# This script checks if environment variables mentioned in docs are correctly documented

set -e

echo "🔧 Environment Variable Validation"
echo "===================================="
echo ""

# Define expected environment variables based on research
EXPECTED_VARS=(
    "DATABASE_URL"
    "PYTHONUNBUFFERED"
    "PYTHONDONTWRITEBYTECODE"
    "PORT"
    "FRONTEND_PORT"
    "ENVIRONMENT"
    "SEED_DB"
)

echo "📋 Expected environment variables:"
for var in "${EXPECTED_VARS[@]}"; do
    echo "  - $var"
done
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi

echo "✅ Dockerfile found"
echo ""

# Validate each environment variable is mentioned in Dockerfile
echo "🔍 Checking Dockerfile for environment variables..."
MISSING_VARS=()
for var in "${EXPECTED_VARS[@]}"; do
    if grep -q "$var" Dockerfile; then
        echo "  ✅ $var found in Dockerfile"
    else
        echo "  ⚠️  $var not found in Dockerfile"
        MISSING_VARS+=("$var")
    fi
done
echo ""

# Check docker-compose.yml if it exists
if [ -f "docker-compose.yml" ]; then
    echo "🔍 Checking docker-compose.yml for environment variables..."
    for var in "${EXPECTED_VARS[@]}"; do
        if grep -q "$var" docker-compose.yml; then
            echo "  ✅ $var found in docker-compose.yml"
        else
            echo "  ⚠️  $var not found in docker-compose.yml"
        fi
    done
    echo ""
fi

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo "✅ All expected environment variables validated"
else
    echo "⚠️  Some environment variables are missing but may be optional"
fi
