# PartsHub Makefile
# Convenient commands for development, testing, and documentation

.PHONY: help install dev test docs build clean backend frontend all

# Default target
help:
	@echo "📦 PartsHub Development Commands"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make install     - Install all dependencies (backend + docs)"
	@echo "  make dev         - Start development servers (backend + docs)"
	@echo "  make backend     - Start backend development server only"
	@echo "  make frontend    - Start frontend development server only"
	@echo "  make docs        - Start documentation server only"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test        - Run all backend tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-contract - Run contract tests only"
	@echo ""
	@echo "🏗️  Building:"
	@echo "  make build       - Build all components"
	@echo "  make build-docs  - Build documentation site"
	@echo "  make build-frontend - Build frontend for production"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean       - Clean all build artifacts"
	@echo "  make sync        - Sync dependencies"
	@echo "  make update      - Update dependencies"
	@echo ""
	@echo "📊 Database:"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Seed database with demo data"
	@echo ""
	@echo "🚢 Deployment:"
	@echo "  make docker      - Build Docker image"
	@echo "  make docker-run  - Run Docker container"
	@echo ""
	@echo "Port allocation:"
	@echo "  8000 - Backend API (production)"
	@echo "  8001 - Backend API (testing)"
	@echo "  3000 - Frontend development server"
	@echo "  8010 - Documentation site"

# Installation
install:
	@echo "📦 Installing all dependencies..."
	@echo "🐍 Installing Python dependencies (backend + docs)..."
	uv sync --extra dev --extra docs
	@echo "🎨 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

sync:
	@echo "🔄 Syncing dependencies..."
	uv sync --extra dev --extra docs
	@echo "✅ Dependencies synced!"

update:
	@echo "📈 Updating dependencies..."
	uv sync --upgrade --extra dev --extra docs
	cd frontend && npm update
	@echo "✅ Dependencies updated!"

# Development servers
dev:
	@echo "🚀 Starting all development servers..."
	@echo "📚 Documentation will be available at: http://localhost:8010"
	@echo "⚙️  Backend will be available at: http://localhost:8000"
	@echo "🎨 Frontend will be available at: http://localhost:3000"
	@echo ""
	@echo "Starting servers in background..."
	@make backend-bg docs-bg frontend-bg
	@echo "✅ All servers started! Use 'make stop' to stop all servers."

backend:
	@echo "⚙️  Starting backend development server..."
	cd backend && PORT=8000 uv run --project .. uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

backend-bg:
	@echo "⚙️  Starting backend server in background..."
	cd backend && PORT=8000 uv run --project .. uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &

frontend:
	@echo "🎨 Starting frontend development server..."
	cd frontend && npm run dev

frontend-bg:
	@echo "🎨 Starting frontend server in background..."
	cd frontend && npm run dev &

docs:
	@echo "📚 Starting documentation server..."
	uv run mkdocs serve --dev-addr 0.0.0.0:8010

docs-bg:
	@echo "📚 Starting documentation server in background..."
	uv run mkdocs serve --dev-addr 0.0.0.0:8010 &

stop:
	@echo "🛑 Stopping all development servers..."
	pkill -f "uvicorn src.main:app" || true
	pkill -f "mkdocs serve" || true
	pkill -f "npm run dev" || true
	@echo "✅ All servers stopped!"

# Testing
test:
	@echo "🧪 Running all backend tests..."
	cd backend && uv run --project .. python run_tests.py

test-unit:
	@echo "🧪 Running unit tests..."
	cd backend && uv run --project .. python run_tests.py tests/unit/

test-contract:
	@echo "🧪 Running contract tests..."
	cd backend && uv run --project .. python run_tests.py tests/contract/

test-integration:
	@echo "🧪 Running integration tests..."
	cd backend && uv run --project .. python run_tests.py tests/integration/

# Building
build: build-docs build-frontend
	@echo "✅ All components built!"

build-docs:
	@echo "🏗️  Building documentation site..."
	uv run mkdocs build
	@echo "✅ Documentation built in site/ directory"

build-frontend:
	@echo "🏗️  Building frontend for production..."
	cd frontend && npm run build
	@echo "✅ Frontend built in frontend/dist/ directory"

# Database operations
migrate:
	@echo "📊 Running database migrations..."
	cd backend && uv run --project .. alembic upgrade head
	@echo "✅ Database migrations completed!"

migrate-create:
	@echo "📊 Creating new migration..."
	@read -p "Migration description: " desc; \
	cd backend && uv run --project .. alembic revision --autogenerate -m "$$desc"

seed:
	@echo "🌱 Seeding database with demo data..."
	cd backend && uv run --project .. python demo_seed.py
	@echo "✅ Database seeded!"

# Cleaning
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf site/
	rm -rf frontend/dist/
	rm -rf backend/.pytest_cache/
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned all build artifacts!"

# Docker operations
docker:
	@echo "🐳 Building Docker image..."
	docker build -t partshub .
	@echo "✅ Docker image built as 'partshub'"

docker-run:
	@echo "🚢 Running Docker container..."
	docker run -p 3000:3000 -p 8000:8000 -v $(PWD)/data:/app/data partshub

docker-dev:
	@echo "🔧 Running Docker container in development mode..."
	docker run -it -p 3000:3000 -p 8000:8000 -v $(PWD):/app -v $(PWD)/data:/app/data partshub /bin/sh

# Linting and formatting
lint:
	@echo "🔍 Running linters..."
	uv run ruff check backend/
	cd frontend && npm run lint
	@echo "✅ Linting completed!"

format:
	@echo "✨ Formatting code..."
	uv run ruff format backend/
	cd frontend && npm run format
	@echo "✅ Code formatted!"

# Quick commands for common workflows
all: install migrate build
	@echo "✅ Full setup completed!"

reset: clean install migrate seed
	@echo "✅ Project reset completed!"

check: lint test
	@echo "✅ Quality checks completed!"