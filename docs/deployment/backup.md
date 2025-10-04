# PartsHub Backup and Recovery Procedures

## Overview

This document provides comprehensive backup and recovery procedures for the PartsHub application, focusing on data preservation and system resilience.

## 1. What to Backup

The critical data for PartsHub is located in the `/app/data` directory, which contains:

- `partshub.db`: SQLite database file containing all application data
- `attachments/`: Directory storing user-uploaded file attachments

### Backup Locations
- Container mount point: `/app/data`
- Typical local volume: `partshub_data`

## 2. Backup Frequency Recommendations

### Critical Data Components
- **Database (`partshub.db`)**: Contains all parts inventory, relationships, and metadata
- **Attachments directory**: User-uploaded files, datasheets, images, and supporting documents

!!! warning "Backup Both Database AND Attachments"
    Always backup the **entire `/app/data` directory** to ensure both the database and all attachments are preserved together. Backing up only the database will result in broken file references and missing attachments.

### Recommended Backup Strategy
1. **Full Backup Frequency**: Daily
   - Backup the entire `/app/data` directory (database + attachments)
   - Both components are critical and should be backed up together

2. **Retention Policy**
   - Keep last 7 daily backups
   - Keep last 4 weekly backups (every Sunday)
   - Maintain monthly archive for long-term retention

## 3. Backup Procedures

### 3.1 Docker Volume Backup Methods

#### A. Docker CP Method (Complete Data Backup)
Backup entire `/app/data` directory using `docker cp`:
```bash
# Backup entire data directory (database + attachments together)
docker cp partshub:/app/data ./backups/partshub_data_$(date +%Y%m%d)

# Compress for efficient storage
tar czvf ./backups/partshub_backup_$(date +%Y%m%d).tar.gz -C ./backups partshub_data_$(date +%Y%m%d)
```

!!! tip "Why backup the entire directory?"
    Backing up `/app/data` as a complete unit ensures database and attachment references remain consistent. Individual file backups may lead to sync issues.

#### B. Volume Backup Method
Create a backup of the named Docker volume:
```bash
# Create a backup container to copy volume contents
docker run --rm \
  -v partshub_data:/source \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czvf /backup/partshub_backup_$(date +%Y%m%d).tar.gz -C /source .
```

#### C. Filesystem Copy Method
For hosts with direct volume access:
```bash
# Backup using filesystem copy
cp -R /var/lib/docker/volumes/partshub_data/_data ./backups/$(date +%Y%m%d)
```

### 3.2 Automated Backup Script (Recommended)
Create a shell script for consistent backups of the entire data directory:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
CONTAINER_NAME="partshub"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup entire /app/data directory (database + attachments)
docker cp "$CONTAINER_NAME":/app/data "$BACKUP_DIR/$DATE/"

# Compress backup for efficient storage
tar czvf "$BACKUP_DIR/partshub_backup_$DATE.tar.gz" -C "$BACKUP_DIR/$DATE" data

# Clean up uncompressed backup
rm -rf "$BACKUP_DIR/$DATE"

# Optional: Remove backups older than 7 days
find "$BACKUP_DIR" -name "partshub_backup_*.tar.gz" -mtime +7 -delete
```

## 4. Recovery Procedures

### 4.1 Database Recovery
To restore a database backup:
```bash
# Stop the running PartsHub container
docker stop partshub

# Copy backup to container's data directory
docker cp ./backups/partshub_20250101.db partshub:/app/data/partshub.db

# Restart container (migrations will run automatically)
docker start partshub
```

### 4.2 Attachments Recovery
Restore attachments directory:
```bash
# Stop container
docker stop partshub

# Remove existing attachments
docker exec partshub rm -rf /app/data/attachments

# Copy backup
docker cp ./backups/attachments_20250101 partshub:/app/data/attachments

# Restart container
docker start partshub
```

## 5. Version Compatibility Notes

### Database Migration Considerations
- Always backup database before version upgrades
- Use Alembic for managing database schema migrations
- Recommended upgrade workflow:
  1. Create full backup
  2. Test migration in staging environment
  3. Perform production migration
  4. Verify data integrity

### Recommended Migration Checks
```bash
# Run Alembic migrations (part of entrypoint)
docker exec partshub alembic upgrade head

# Verify database integrity
docker exec partshub uv run python -c "import database_checks; database_checks.verify_database()"
```

## 6. Container Upgrade Strategies

### Safe Upgrade Procedure
1. Backup current data
2. Pull new image
3. Stop current container
4. Create new container with same volume mounts
5. Verify functionality
6. Retire old container

```bash
# Upgrade example
docker pull ghcr.io/madeinoz67/partshub:latest
docker stop partshub
docker rename partshub partshub_old
docker run -d \
  --name partshub \
  -v partshub_data:/app/data \
  ghcr.io/madeinoz67/partshub:latest
```

## Best Practices
- Test backups regularly
- Store backups in multiple locations
- Use offsite/cloud storage for critical backups
- Implement backup rotation and retention policies
- Document and practice recovery scenarios

## Troubleshooting
- If migrations fail, restore from the last known good backup
- Use database integrity checks after recovery
- Consult application logs for detailed error information

---

**Note**: Always validate backups in a staging environment before critical restorations.