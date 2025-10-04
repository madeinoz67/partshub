# PartsHub Docker Infrastructure Research

## Preliminary Research Notes

This document captures research findings on the PartsHub Docker infrastructure, focusing on architectural, environmental, and deployment considerations.

## 1. Docker Architecture Analysis

### Multi-Stage Build Structure
PartsHub uses a sophisticated multi-stage Dockerfile with four primary targets:
- `backend`: Python 3.11-slim based backend stage
- `frontend-build`: Node.js 20-alpine frontend build stage
- `frontend`: Nginx-alpine frontend runtime stage
- `development`: Combined all-in-one local development stage

#### Key Architectural Decisions
- Uses separate stages for build and runtime
- Minimizes final image size through multi-stage builds
- Supports distinct deployment modes (production, development)

### Build Targets
1. **Backend Target**:
   - Uses Python 3.11-slim
   - Installs system dependencies for file and barcode processing
   - Sets up `uv` for dependency management
   - Configures data directories with 777 permissions
   - Exposes port 8000

2. **Frontend Targets**:
   - Build stage: Node.js 20-alpine to compile Vue.js application
   - Runtime stage: Nginx-alpine to serve static files
   - Includes API proxy configuration for backend communication
   - Exposes port 3000

3. **Development Target**:
   - Combines backend and frontend dependencies
   - Includes Python and Node.js in single image
   - Supports local development workflow

### Entrypoint and Database Migration
- Custom entrypoint script (`entrypoint.sh`) runs Alembic migrations
- Automatically runs migrations before starting backend
- Uses `uvicorn` to serve FastAPI application

### Health Checks
- Backend health check:
  - Interval: 30 seconds
  - Timeout: 10 seconds
  - Start period: 45 seconds
  - Max retries: 3
- Checks `/health` endpoint for backend availability

## 2. Environment Variables Inventory

### Dockerfile Environment Variables
- `DATABASE_URL`: SQLite database path (default: `/app/data/partshub.db`)
- `PYTHONUNBUFFERED`: Prevents Python buffering output
- `PYTHONDONTWRITEBYTECODE`: Prevents `.pyc` file generation
- `PORT`: Backend service port (default: 8000)
- `FRONTEND_PORT`: Frontend service port (default: 3000)

### Docker Compose Environment Variables
- `DATABASE_URL`: Confirms SQLite database location
- `ENVIRONMENT`: Set to "production"
- `SEED_DB`: Boolean flag to seed database (set to true)

## 3. Data Persistence Analysis

### Data Directory Structure
- `/app/data/`: Root data directory
- `/app/data/partshub.db`: SQLite database file
- `/app/data/attachments/`: Directory for file attachments

### Volume Configuration
- Uses Docker volume `partshub_data`
- Mounted to `/app/data`
- Local driver ensures persistent storage
- 777 permissions for maximum flexibility

## 4. GitHub Actions Docker Publishing

### Continuous Deployment Workflow
- Publishes to GitHub Container Registry (ghcr.io)
- Triggers on main branch push
- Supports manual workflow dispatch

#### Image Tagging Strategy
1. Development Images:
   - `dev`
   - `dev-{version}`
   - `dev-{short_sha}`

2. Versioning Sources:
   - Version extracted from `pyproject.toml`
   - Short Git SHA for unique identifiers

### Deployment Prerequisites
- Requires passing:
  - Backend Tests
  - Frontend Tests
  - Security Scan
  - Docker Build

## 5. Existing Documentation Analysis

### Current Documentation Status
- Minimal Docker-specific documentation
- No comprehensive deployment guide
- Lacks user-friendly deployment instructions

## 6. Content Organization Recommendations

### Proposed Documentation Structure
1. `/docs/deployment/`
   - `docker.md`: Comprehensive Docker guide
   - `local-development.md`: Development environment setup
   - `production-deployment.md`: Production deployment instructions

2. Documentation Updates Needed
   - Update README with Docker quickstart
   - Expand mkdocs.yml with deployment section
   - Create detailed configuration and customization guides

## Research Conclusions

### Key Findings
- Robust, flexible Docker architecture
- Multi-stage builds for efficient deployment
- Strong emphasis on local development support
- Comprehensive CI/CD integration

### Recommended Next Steps
- Develop comprehensive Docker documentation
- Create deployment guides for various environments
- Document environment variable configuration
- Provide examples for common deployment scenarios