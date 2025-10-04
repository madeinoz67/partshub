#!/bin/bash
# Validation script for Docker Compose configuration
# This script validates docker-compose.yml syntax and structure

set -e

echo "🐳 Docker Compose Validation"
echo "=============================="
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

echo "✅ docker-compose.yml found"
echo ""

# Check if Docker Compose is available
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "✅ Docker Compose is available: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is available: $(docker-compose --version)"
else
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo ""

# Validate docker-compose.yml syntax
echo "🔍 Validating docker-compose.yml syntax..."
if docker compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax is valid"
elif docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml syntax validation failed"
    exit 1
fi
echo ""

# Check for required services
echo "🔍 Checking for required services..."
if grep -q "services:" docker-compose.yml; then
    echo "✅ Services section found"

    # Check for partshub service
    if grep -q "partshub:" docker-compose.yml; then
        echo "✅ PartsHub service defined"
    else
        echo "⚠️  PartsHub service not found"
    fi
else
    echo "❌ No services section found"
    exit 1
fi
echo ""

# Check for volume definitions
echo "🔍 Checking for volume definitions..."
if grep -q "volumes:" docker-compose.yml; then
    echo "✅ Volumes section found"
else
    echo "⚠️  No volumes section found"
fi
echo ""

# Check for port mappings
echo "🔍 Checking for port mappings..."
if grep -q "ports:" docker-compose.yml; then
    echo "✅ Port mappings defined"

    # Check for specific ports
    if grep -q "3000:3000" docker-compose.yml; then
        echo "  ✅ Frontend port (3000) mapped"
    else
        echo "  ⚠️  Frontend port (3000) not mapped"
    fi

    if grep -q "8000:8000" docker-compose.yml; then
        echo "  ✅ Backend port (8000) mapped"
    else
        echo "  ⚠️  Backend port (8000) not mapped"
    fi
else
    echo "⚠️  No port mappings found"
fi
echo ""

echo "✅ Docker Compose validation completed"
