# PartsHub Data Persistence and Volumes Guide

## 1. Purpose of /app/data Directory

The `/app/data` directory is the central location for persistent data storage in PartsHub. It contains two primary components:

- `partshub.db`: The SQLite database file storing all application data
- `attachments/`: A directory for storing file attachments associated with parts and inventories

### Data Storage Hierarchy
```
/app/data/
├── partshub.db        # SQLite database file
└── attachments/       # Directory for file attachments
```

## 2. Volume Mount Configuration Examples

### Docker Run Command
```bash
# Named Volume
docker run -v partshub_data:/app/data partshub/app

# Bind Mount (Local Directory)
docker run -v /path/to/local/data:/app/data partshub/app
```

### Docker Compose Configuration
```yaml
version: '3.8'
services:
  partshub:
    image: partshub/app
    volumes:
      # Named Volume
      - partshub_data:/app/data

      # Bind Mount
      - ./local-data:/app/data

volumes:
  partshub_data:  # Optional: Explicitly define named volume
```

## 3. Data Directory Structure Details

### Database File
- `partshub.db`: SQLite database storing all application data
- Location: `/app/data/partshub.db`
- Managed by SQLAlchemy ORM
- Automatically migrated on container startup

### Attachments Directory
- Location: `/app/data/attachments/`
- Stores uploaded files and attachments
- Automatically created if not existing
- Supports file uploads from the web interface

## 4. Named Volumes vs Bind Mounts

### Named Volumes
**Recommended for Production**
- Managed entirely by Docker
- Persistent across container restarts
- Platform-independent
- More secure and portable

Example:
```yaml
volumes:
  partshub_data:  # Docker manages this volume
```

### Bind Mounts
**Recommended for Development**
- Maps a host directory to container directory
- Useful for local development
- Allows direct file system access
- Less portable across different systems

Example:
```yaml
volumes:
  - ./local-data:/app/data  # Direct host directory mapping
```

## 5. Permissions and Ownership Considerations

PartsHub container is configured with:
- User: `appuser`
- Group: `appgroup`
- Directory Permissions: `777` (Read/Write/Execute for all)

### Ensuring Proper Permissions
- For bind mounts, ensure host directory is writable
- Use `chown` to set correct ownership if needed:
  ```bash
  # On Linux/macOS
  chown 1000:1000 /path/to/data
  ```

## 6. Platform-Specific Mounting Instructions

### Linux
- Native Docker support
- Use bind mounts or named volumes seamlessly
- Recommend SELinux context adjustment if needed

### macOS
- Uses Docker Desktop's VM
- Bind mounts may have performance overhead
- Recommended: Use named volumes
- Ensure sufficient disk space in Docker Desktop VM

### Windows
- Use Docker Desktop with WSL 2 backend
- Bind mount paths use forward slashes
- Example: `C:/Users/YourName/partshub-data:/app/data`
- Recommend named volumes for better compatibility

## 7. Troubleshooting Volume Issues

### Common Problems and Solutions

1. **Permission Denied Errors**
   - Symptom: Cannot write to `/app/data`
   - Solution:
     ```bash
     # Check and adjust directory permissions
     chmod 777 /path/to/data
     ```

2. **Missing Data Directory**
   - Symptom: No data persists between container restarts
   - Solution: Ensure volume is correctly mounted
     ```yaml
     volumes:
       - partshub_data:/app/data
     ```

3. **Large Database File**
   - Symptom: Slow performance or large volume
   - Solution:
     - Use SQLite's vacuum command periodically
     - Consider database rotation or archiving strategy

4. **Attachment Storage Limitations**
   - Symptom: Running out of disk space
   - Solution:
     - Monitor `/app/data/attachments/` size
     - Implement attachment cleanup policies
     - Configure max attachment size in application settings

### Backup Recommendations
- **Always backup the entire `/app/data` directory** (database + attachments together)
- Backup both `/app/data/partshub.db` AND `/app/data/attachments/` as a complete unit
- Use volume snapshots or complete directory backups
- See [Backup & Recovery Guide](backup.md) for detailed procedures

!!! warning "Complete Backups Required"
    Never backup only the database! Attachments must be backed up together with the database to maintain file reference integrity.

## Best Practices

1. Always use named volumes in production
2. Keep data directory on fast, reliable storage
3. Monitor disk space and performance
4. Implement regular backups
5. Use environment variables for flexible configuration

## Conclusion

The `/app/data` directory provides a flexible, robust mechanism for data persistence in PartsHub. By understanding volume configuration, you can ensure your data remains safe, portable, and easily manageable across different deployment environments.