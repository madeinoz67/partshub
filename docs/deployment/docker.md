# PartsHub Docker Deployment Guide

## 1. Introduction to PartsHub Docker Image

PartsHub provides a comprehensive, all-in-one Docker container that simplifies deployment by bundling both the backend and frontend components into a single, easy-to-manage image. This approach ensures consistent performance across different environments and reduces configuration complexity.

## 2. All-in-One Architecture Overview

The PartsHub Docker image is built using a multi-stage build strategy with four primary targets:

- `backend`: Python 3.11-slim based backend stage
- `frontend-build`: Node.js 20-alpine frontend build stage
- `frontend`: Nginx-alpine frontend runtime stage
- `development`: Combined all-in-one local development stage

Key architectural features:
- Minimal image size through multi-stage builds
- Support for development and production deployment modes
- Integrated backend (FastAPI) and frontend (Vue.js) services
- Automatic database migration on container startup

## 3. Quick Start with Docker Run

To quickly deploy PartsHub, use the following Docker run command:

```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -v partshub_data:/app/data \
  --name partshub \
  ghcr.io/madeinoz67/partshub:dev
```

### Command Breakdown
- `-d`: Run in detached mode
- `-p 8000:8000`: Map backend API port
- `-p 3000:3000`: Map frontend port
- `-v partshub_data:/app/data`: Create a persistent data volume
- `--name partshub`: Name the container
- `ghcr.io/madeinoz67/partshub:dev`: Use the development image

## 4. Port Configuration

The PartsHub Docker container exposes two primary ports:

- **Backend API**: Port 8000
  - Base URL: `http://localhost:8000`
  - Swagger UI: `http://localhost:8000/docs`

- **Frontend**: Port 3000
  - Base URL: `http://localhost:3000`

## 5. Health Check Configuration

The container includes a robust health check mechanism:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 45 seconds
- **Max Retries**: 3

Health checks verify the backend's `/health` endpoint to ensure application availability.

Verify container health:
```bash
docker ps | grep partshub  # Status should show "healthy"
```

## 6. Image Pulling from GitHub Container Registry

Pull images directly from the PartsHub GitHub Container Registry:

```bash
docker pull ghcr.io/madeinoz67/partshub:dev     # Latest development image
docker pull ghcr.io/madeinoz67/partshub:latest  # Latest stable release
```

## 7. Deployment Patterns

### Basic Deployment
Simplest method using `docker run`:
```bash
docker run -p 8000:8000 -p 3000:3000 ghcr.io/madeinoz67/partshub:dev
```

### Development Deployment
For local development with persistent data:
```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -v partshub_data:/app/data \
  -e ENVIRONMENT=development \
  ghcr.io/madeinoz67/partshub:dev
```

### Production Deployment
For production environments:
```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -v partshub_data:/app/data \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=sqlite:///./data/production.db \
  --restart unless-stopped \
  ghcr.io/madeinoz67/partshub:latest
```

## 8. Troubleshooting

### Common Issues and Solutions

1. **Port Conflicts**
   - Problem: Ports 8000 or 3000 are already in use
   - Solution: Map to different host ports
     ```bash
     docker run -p 8001:8000 -p 3001:3000 ...
     ```

2. **Container Won't Start**
   - Check container logs:
     ```bash
     docker logs partshub
     ```

3. **Cannot Connect to Application**
   - Verify container is running:
     ```bash
     docker ps
     ```
   - Check health status:
     ```bash
     docker inspect partshub | grep Health
     ```

4. **First Login and Admin Credentials**
   - Retrieve initial admin password from logs:
     ```bash
     docker logs partshub | grep "DEFAULT ADMIN"
     ```

5. **Data Persistence**
   - Use named volume for persistent storage
   - Location: `/app/data` inside the container
   - Includes database and attachments

## Recommended Next Steps

- Review `docs/deployment/backup.md` for data backup strategies
- Explore `docs/deployment/production.md` for production deployment recommendations
- Read the user guide at `docs/user/features.md`

## Container Management

### Start/Stop/Remove
```bash
# Start container
docker start partshub

# Stop container
docker stop partshub

# Remove container (keeps data)
docker rm partshub

# Remove container and data volume
docker rm -f partshub
docker volume rm partshub_data
```

## Docker Compose Alternative

For easier management, use Docker Compose:

```yaml
version: '3.8'

services:
  partshub:
    image: ghcr.io/madeinoz67/partshub:dev
    ports:
      - "3000:3000"
      - "8000:8000"
    volumes:
      - partshub_data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/partshub.db
      - ENVIRONMENT=production
    restart: unless-stopped

volumes:
  partshub_data:
    driver: local
```

Run with:
```bash
docker compose up -d
```