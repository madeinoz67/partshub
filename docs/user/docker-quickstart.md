# PartsHub Docker Quickstart Guide

Get PartsHub up and running in under 5 minutes with Docker!

## Prerequisites

- Docker installed on your computer
- Internet connection

## Quick Start

1. **Run PartsHub with a single command**:

```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -v partshub_data:/app/data \
  --name partshub \
  ghcr.io/madeinoz67/partshub:latest
```

## Accessing the Application

1. **Open the Frontend**: Navigate to [http://localhost:3000](http://localhost:3000) in your web browser
2. **Access API Documentation**: Visit [http://localhost:8000/docs](http://localhost:8000/docs)

## First-Time Login

1. **Find Admin Credentials**:
   Run this command to see the default admin password:
   ```bash
   docker logs partshub | grep "DEFAULT ADMIN"
   ```

2. **Login Process**:
   - Go to [http://localhost:3000](http://localhost:3000)
   - Click "Login"
   - Username: `admin`
   - Password: Use the password from the logs
   - You'll be prompted to change the password on first login

## Helpful Docker Commands

- **Stop the container**:
  ```bash
  docker stop partshub
  ```

- **Start the container**:
  ```bash
  docker start partshub
  ```

- **View Logs**:
  ```bash
  docker logs -f partshub
  ```

## Next Steps

- [Explore PartsHub Features](features.md)
- [Learn about Docker Deployment](../deployment/docker.md)
- [Backup and Data Management](../deployment/backup.md)

## Troubleshooting

**Ports Already in Use?**
Change the host ports in the `docker run` command, like:
```bash
docker run -d \
  -p 8001:8000 \
  -p 3001:3000 \
  ...
```

**Can't Connect?**
- Check container status: `docker ps`
- View logs: `docker logs partshub`

Need more help? Check our [full deployment documentation](../deployment/docker.md).