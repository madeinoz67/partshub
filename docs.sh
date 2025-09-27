#!/bin/bash
# Documentation development commands for PartsHub

case "$1" in
    "serve" | "dev")
        echo "🚀 Starting MkDocs development server on http://localhost:8010"
        uv run mkdocs serve --dev-addr 0.0.0.0:8010
        ;;
    "build")
        echo "🏗️  Building documentation site"
        uv run mkdocs build
        ;;
    "clean")
        echo "🧹 Cleaning documentation build files"
        rm -rf site/
        ;;
    *)
        echo "📚 PartsHub Documentation Commands"
        echo ""
        echo "Usage: ./docs.sh [command]"
        echo ""
        echo "Commands:"
        echo "  serve, dev  - Start development server on port 8010"
        echo "  build       - Build static documentation site"
        echo "  clean       - Clean build artifacts"
        echo ""
        echo "Development server will be available at:"
        echo "  http://localhost:8010"
        echo ""
        echo "Port allocation:"
        echo "  8000 - Backend API (production)"
        echo "  8001 - Backend API (testing)"
        echo "  8010 - Documentation site"
        ;;
esac