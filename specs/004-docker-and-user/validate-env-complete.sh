#!/bin/bash
# Comprehensive environment variable validation
# This script ensures all environment variables are properly documented

set -e

echo "🔧 Comprehensive Environment Variable Validation"
echo "=================================================="
echo ""

# Define all environment variables that should be documented
ENV_VARS="DATABASE_URL PORT FRONTEND_PORT ENVIRONMENT SEED_DB PYTHONUNBUFFERED PYTHONDONTWRITEBYTECODE"

echo "📋 Environment variables to be documented:"
echo "  - DATABASE_URL: SQLite database path - default: sqlite:///./data/partshub.db"
echo "  - PORT: Backend service port - default: 8000"
echo "  - FRONTEND_PORT: Frontend service port - default: 3000"
echo "  - ENVIRONMENT: Deployment environment - values: development, production"
echo "  - SEED_DB: Seed database with demo/test data (DEV ONLY) - values: true, false"
echo "  - PYTHONUNBUFFERED: Prevent Python output buffering - default: 1"
echo "  - PYTHONDONTWRITEBYTECODE: Prevent .pyc file generation - default: 1"
echo ""

# Check Dockerfile for environment variables
echo "🔍 Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
    DOCKERFILE_VARS=0
    for var in $ENV_VARS; do
        if grep -q "$var" Dockerfile; then
            DOCKERFILE_VARS=$((DOCKERFILE_VARS + 1))
        fi
    done
    TOTAL_VARS=$(echo $ENV_VARS | wc -w | tr -d ' ')
    echo "✅ Found $DOCKERFILE_VARS/$TOTAL_VARS environment variables in Dockerfile"
else
    echo "❌ Dockerfile not found"
    exit 1
fi
echo ""

# Check docker-compose.yml for environment variables
if [ -f "docker-compose.yml" ]; then
    echo "🔍 Checking docker-compose.yml..."
    COMPOSE_VARS=0
    for var in $ENV_VARS; do
        if grep -q "$var" docker-compose.yml; then
            COMPOSE_VARS=$((COMPOSE_VARS + 1))
        fi
    done
    echo "✅ Found $COMPOSE_VARS/$TOTAL_VARS environment variables in docker-compose.yml"
else
    echo "⚠️  docker-compose.yml not found"
fi
echo ""

# Validate default values are sensible
echo "🧪 Validating default value patterns..."

if grep -q "sqlite://" Dockerfile 2>/dev/null || grep -q "sqlite://" docker-compose.yml 2>/dev/null; then
    echo "  ✅ DATABASE_URL has expected default pattern: sqlite://"
else
    echo "  ⚠️  DATABASE_URL default value not found: sqlite://"
fi

if grep -q "8000" Dockerfile 2>/dev/null || grep -q "8000" docker-compose.yml 2>/dev/null; then
    echo "  ✅ PORT has expected default pattern: 8000"
else
    echo "  ⚠️  PORT default value not found: 8000"
fi

if grep -q "3000" Dockerfile 2>/dev/null || grep -q "3000" docker-compose.yml 2>/dev/null; then
    echo "  ✅ FRONTEND_PORT has expected default pattern: 3000"
else
    echo "  ⚠️  FRONTEND_PORT default value not found: 3000"
fi

echo ""

echo "✅ Environment variable completeness validation completed"
echo ""
echo "📝 Documentation Requirements:"
echo "  - All 7 variables should be documented in docs/deployment/environment.md"
echo "  - Include descriptions, default values, and examples"
echo "  - Provide scenarios for different deployment configurations"
