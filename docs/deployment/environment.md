# PartsHub Environment Variables Reference

## Overview

This document provides a comprehensive reference for environment variables used in PartsHub deployments. These variables control various aspects of the application's configuration, from database settings to runtime behavior.

## Environment Variables Reference

### 1. DATABASE_URL

- **Description**: Specifies the path and connection string for the SQLite database
- **Default Value**: `sqlite:///./data/partshub.db`
- **Possible Values**:
  - SQLite file path (recommended)
  - Full SQLite connection string
- **Usage Examples**:
  ```bash
  # Default local file storage
  DATABASE_URL=sqlite:///./data/partshub.db

  # Explicit file path
  DATABASE_URL=sqlite:////app/data/custom_location.db

  # In-memory database (for testing)
  DATABASE_URL=sqlite:///:memory:
  ```
- **When to Customize**:
  - Change database location for persistent storage
  - Use different storage strategies
  - Configure for specific deployment environments

### 2. PORT

- **Description**: Defines the port for the backend service
- **Default Value**: `8000`
- **Possible Values**: Any valid port number (1-65535)
- **Usage Examples**:
  ```yaml
  # docker-compose.yml
  services:
    backend:
      environment:
        - PORT=8080  # Custom port

  # docker run
  docker run -e PORT=9000 partshub-backend
  ```
- **When to Customize**:
  - Avoid port conflicts
  - Align with existing infrastructure
  - Meet specific network configuration requirements

### 3. FRONTEND_PORT

- **Description**: Specifies the port for the frontend service
- **Default Value**: `3000`
- **Possible Values**: Any valid port number (1-65535)
- **Usage Examples**:
  ```yaml
  # docker-compose.yml
  services:
    frontend:
      environment:
        - FRONTEND_PORT=3030  # Custom port

  # docker run
  docker run -e FRONTEND_PORT=4000 partshub-frontend
  ```
- **When to Customize**:
  - Prevent port conflicts
  - Match existing network configurations
  - Support multiple frontend instances

### 4. ENVIRONMENT

- **Description**: Sets the deployment environment mode
- **Allowed Values**:
  - `development`
  - `production`
- **Default Value**: `development`
- **Usage Examples**:
  ```yaml
  # docker-compose.yml
  services:
    backend:
      environment:
        - ENVIRONMENT=production

  # docker run
  docker run -e ENVIRONMENT=production partshub-backend
  ```
- **When to Customize**:
  - Enable environment-specific configurations
  - Adjust logging and error handling
  - Control feature flags and debugging options

### 5. SEED_DB

- **Description**: Controls automatic database seeding with demo/test data
- **Allowed Values**:
  - `true`
  - `false`
  - Empty (defaults to `false`)
- **Default Value**: `false`
- **Usage Examples**:
  ```yaml
  # docker-compose.yml (DEVELOPMENT ONLY)
  services:
    backend:
      environment:
        - SEED_DB=true  # Populate with demo data

  # docker run (DEVELOPMENT ONLY)
  docker run -e SEED_DB=true partshub-backend
  ```
- **When to Customize**:
  - Initial setup of development environments
  - Automated testing scenarios
  - Demonstration or training purposes

!!! warning "Production Usage"
    **DO NOT use SEED_DB=true in production environments!** This variable is intended for demo and testing purposes only. Production deployments should always use `SEED_DB=false` (or omit the variable entirely) to ensure data integrity.

### 6. PYTHONUNBUFFERED

- **Description**: Prevents Python from buffering standard output and standard error streams
- **Default Value**: `1`
- **Possible Values**:
  - `1` (unbuffered)
  - `0` (buffered)
- **Usage Examples**:
  ```yaml
  # docker-compose.yml
  services:
    backend:
      environment:
        - PYTHONUNBUFFERED=1

  # docker run
  docker run -e PYTHONUNBUFFERED=1 partshub-backend
  ```
- **When to Customize**:
  - Real-time logging
  - Debugging
  - Container logging scenarios

### 7. PYTHONDONTWRITEBYTECODE

- **Description**: Prevents generation of `.pyc` bytecode files
- **Default Value**: `1`
- **Possible Values**:
  - `1` (no `.pyc` files)
  - `0` (generate `.pyc` files)
- **Usage Examples**:
  ```yaml
  # docker-compose.yml
  services:
    backend:
      environment:
        - PYTHONDONTWRITEBYTECODE=1

  # docker run
  docker run -e PYTHONDONTWRITEBYTECODE=1 partshub-backend
  ```
- **When to Customize**:
  - Performance tuning
  - Reducing container image size
  - Specific caching requirements

## Deployment Scenarios

### Development Environment

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - DATABASE_URL=sqlite:///./data/dev.db
      - PORT=8000
      - FRONTEND_PORT=3000
      - ENVIRONMENT=development
      - SEED_DB=true
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
```

### Production Environment

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - DATABASE_URL=sqlite:///./data/partshub.db
      - PORT=8000
      - FRONTEND_PORT=3000
      - ENVIRONMENT=production
      - SEED_DB=false
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
```

## Best Practices

1. Always use absolute paths for `DATABASE_URL`
2. Keep sensitive configurations out of version control
3. Use environment-specific settings
4. Monitor and log environment variable usage
5. Validate environment configurations during startup

## Troubleshooting

- Check Docker logs for environment-related issues
- Verify port availability before deployment
- Ensure proper volume mappings for persistent data