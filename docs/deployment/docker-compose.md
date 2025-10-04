# Docker Compose Usage Guide for PartsHub

## 1. Introduction to Docker Compose for PartsHub

Docker Compose is a powerful tool for defining and managing multi-container Docker applications. For PartsHub, Docker Compose simplifies the process of:
- Defining your application's services
- Configuring their interconnections
- Managing volumes and environment variables
- Easily starting, stopping, and rebuilding your development environment

### Why Use Docker Compose?
- **Consistency**: Ensure the same environment across different development machines
- **Simplicity**: Manage multiple services with a single command
- **Reproducibility**: Version control your deployment configuration
- **Isolation**: Keep your development environment separate from your host system

## 2. Development Compose File Walkthrough

The `docker-compose.yml` for PartsHub defines a single service with several key configurations:

```yaml
version: '3.8'  # Docker Compose file version

services:
  partshub:
    build:
      context: .             # Use the current directory as build context
      dockerfile: Dockerfile # Use the project's Dockerfile
    ports:
      - "3000:3000"  # Map frontend Vue.js dev server port
      - "8000:8000"  # Map backend FastAPI port
    volumes:
      - partshub_data:/app/data  # Persistent data volume
    environment:
      - DATABASE_URL=sqlite:///./data/partshub.db
      - ENVIRONMENT=production
      - SEED_DB=true  # Seed the database on startup
    restart: unless-stopped  # Automatically restart unless manually stopped

volumes:
  partshub_data:
    driver: local  # Use the local volume driver
```

### Key Components Explained
- **Services**: Defines the `partshub` container configuration
- **Build**: Builds the container using the project's Dockerfile
- **Ports**: Maps container ports to host ports
- **Volumes**: Provides persistent storage for application data
- **Environment Variables**: Configures application runtime settings
- **Restart Policy**: Ensures container stays running

## 3. Starting and Stopping Services

### Start Services
To start services in the background:
```bash
docker compose up -d
```
- `-d` runs containers in detached mode (background)
- First run will build the image if not already built

### Stop Services
Stop and remove containers:
```bash
docker compose down
```

### Rebuild and Start
Force a rebuild before starting:
```bash
docker compose up -d --build
```
- `--build` rebuilds images before starting containers

## 4. Viewing Logs

### View All Service Logs
```bash
docker compose logs
```

### Follow Live Logs
```bash
docker compose logs -f
```
- `-f` follows (streams) the logs in real-time

### Filter Logs for Specific Service
```bash
docker compose logs partshub
```

## 5. Common Docker Compose Commands Reference

### List Running Services
```bash
docker compose ps
```

### Stop Specific Service
```bash
docker compose stop partshub
```

### Start Specific Service
```bash
docker compose start partshub
```

### Execute Command in Running Container
```bash
docker compose exec partshub bash
```
- Gives you an interactive shell inside the container

### Restart Service
```bash
docker compose restart partshub
```

## 6. Customizing Compose for Local Development

### Override Configuration
Create a `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  partshub:
    environment:
      - ENVIRONMENT=development
      # Add more development-specific settings
```

### Environment-Specific Configurations
- `docker-compose.yml`: Base configuration
- `docker-compose.override.yml`: Local overrides
- `docker-compose.prod.yml`: Production-specific settings

Docker Compose automatically merges these files, with overrides taking precedence.

## Troubleshooting

### Common Issues
- **Port Conflicts**: Ensure ports 3000 and 8000 are not in use
- **Build Failures**: Check Dockerfile and build context
- **Permission Issues**: Run with `sudo` if needed on Linux

### Debugging
- Check logs: `docker compose logs`
- Verify service status: `docker compose ps`
- Rebuild from scratch: `docker compose down --rmi all && docker compose up -d`

## Best Practices
- Always commit `docker-compose.yml` to version control
- Use environment variables for configuration
- Keep containers stateless where possible
- Regularly update Docker and Docker Compose

## Next Steps
- Review production deployment documentation
- Explore advanced Docker Compose features
- Set up continuous integration with Docker

Happy Dockerizing! 🐳