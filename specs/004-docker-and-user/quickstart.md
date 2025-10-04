# Docker Deployment Quickstart

This quickstart guide gets PartsHub running with Docker in under 5 minutes.

## Prerequisites

- Docker installed and running
- Internet connection to pull the image

## Quick Start (Single Command)

Pull and run the latest development image:

```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -v partshub_data:/app/data \
  --name partshub \
  ghcr.io/owner/partshub:dev
```

**What this does**:
- Pulls the latest development image from GitHub Container Registry
- Maps ports 8000 (backend API) and 3000 (frontend)
- Creates a named volume for persistent data storage
- Runs the container in detached mode

## Access the Application

1. **Frontend**: Open http://localhost:3000 in your browser
2. **Backend API**: Available at http://localhost:8000
3. **API Documentation**: Visit http://localhost:8000/docs for Swagger UI

## Find Admin Credentials

View the container logs to find the automatically generated admin password:

```bash
docker logs partshub | grep "DEFAULT ADMIN"
```

You should see output like:
```
🔑 DEFAULT ADMIN CREATED:
   Username: admin
   Password: <randomly-generated-password>
```

## First Login

1. Navigate to http://localhost:3000
2. Click "Login"
3. Enter username: `admin` and the password from logs
4. You'll be prompted to change the password on first login

## Verify Deployment

Check container health:
```bash
docker ps | grep partshub
```

Status should show "healthy" after ~45 seconds.

## Common Operations

**View logs**:
```bash
docker logs -f partshub
```

**Stop the container**:
```bash
docker stop partshub
```

**Start the container**:
```bash
docker start partshub
```

**Remove the container** (keeps data):
```bash
docker rm -f partshub
```

**Remove container and data**:
```bash
docker rm -f partshub
docker volume rm partshub_data
```

## Using Docker Compose (Alternative)

For easier management, create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  partshub:
    image: ghcr.io/owner/partshub:dev
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

Then run:
```bash
docker compose up -d
```

## Next Steps

- Explore the comprehensive Docker deployment documentation at `docs/deployment/docker.md`
- Learn about data persistence and backups at `docs/deployment/backup.md`
- Review production deployment recommendations at `docs/deployment/production.md`
- Read the complete user guide at `docs/user/features.md`

## Troubleshooting

**Port already in use**:
Change the host port mapping: `-p 8001:8000 -p 3001:3000`

**Container won't start**:
Check logs: `docker logs partshub`

**Cannot connect to application**:
Verify container is running: `docker ps`
Check health status: `docker inspect partshub | grep Health`

For more troubleshooting, see the full deployment documentation.
