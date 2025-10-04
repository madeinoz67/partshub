# PartsHub Production Deployment Guide

## 1. Production vs Development Deployment Differences

### Key Considerations
- **Security**: Production deployments require enhanced security measures
- **Performance**: Optimized for high-traffic, mission-critical environments
- **Reliability**: Focuses on zero-downtime deployments and robust error handling
- **Resource Management**: More conservative resource allocation
- **Monitoring**: Comprehensive logging and performance tracking

### Deployment Mode Differences
| Aspect | Development | Production |
|--------|-------------|------------|
| Authentication | Optional/Disabled | Mandatory, multi-factor |
| Logging | Verbose | Structured, performance-optimized |
| Error Handling | Detailed errors | Sanitized error responses |
| Database | In-memory/Local SQLite | Persistent SQLite with backups |
| Resource Limits | Unlimited | Strictly controlled |

## 2. Environment Variable Configuration

### Production-Specific Settings
```bash
# Required Environment Variables
DATABASE_URL=/app/data/production/partshub.db
ENVIRONMENT=production
SECRET_KEY=generate_a_secure_random_key_here
LOG_LEVEL=INFO

# Security Configurations
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Performance Tuning
WORKERS=4  # Number of worker processes (usually 2-4 * CPU cores)
MAX_REQUESTS=1000  # Restart workers after specified requests
TIMEOUT=120  # Request timeout in seconds

# Optional Performance Configurations
CACHE_BACKEND=redis://redis-cache:6379/0
RATE_LIMIT=100/minute  # API request rate limiting
```

!!! danger "Production Environment Variables - Critical"
    **Never set SEED_DB=true in production!** This variable is for demo/testing only and should be omitted or set to `false` in production to prevent accidental data corruption.

## 3. Volume Mount Security Practices

### Permissions and Ownership
```bash
# Create a dedicated service user
useradd -r -s /bin/false partshub_service

# Set strict permissions
chown -R partshub_service:partshub_service /app/data
chmod 750 /app/data
chmod 640 /app/data/partshub.db

# SELinux Context (if applicable)
semanage fcontext -a -t container_file_t "/app/data(/.*)?"
restorecon -Rv /app/data
```

### Volume Configuration Best Practices
- Use read-only mounts where possible
- Minimize host directory exposure
- Use dedicated volumes with limited scope
- Implement regular volume backups

## 4. Network Isolation Recommendations

### Docker Network Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    networks:
      - backend_net
      - proxy_net

  frontend:
    networks:
      - frontend_net
      - proxy_net

networks:
  backend_net:
    driver: bridge
    internal: true  # Isolate from external networks
  frontend_net:
    driver: bridge
  proxy_net:
    external: true
```

### Firewall Rules
```bash
# Recommended UFW/iptables configuration
ufw allow from 172.16.0.0/12 to any port 8000  # Backend
ufw allow from 172.16.0.0/12 to any port 3000  # Frontend
ufw deny from any to any  # Default deny
```

## 5. Versioning Strategy

### Version Tagging
```bash
# Pull specific version
docker pull ghcr.io/madeinoz67/partshub:v0.1.1

# Recommended tagging approach
docker pull ghcr.io/madeinoz67/partshub:${VERSION}
docker pull ghcr.io/madeinoz67/partshub:${VERSION}-${GIT_SHA}
```

### Version Selection Guidelines
- Use semantic versioning (major.minor.patch)
- Avoid `latest` tag in production
- Pin to specific versions for predictability
- Regularly update to security patch releases

## 6. Upgrade and Rollback Procedures

### Zero-Downtime Deployment
```bash
# Blue-Green Deployment Strategy
docker-compose up -d --scale backend=2 backend
docker-compose stop backend_old
docker-compose rm backend_old

# Rollback Procedure
docker-compose down
docker-compose up -d --version=${PREVIOUS_VERSION}
```

### Deployment Checklist
- [ ] Take database backup
- [ ] Validate new image
- [ ] Perform database migrations
- [ ] Run health checks
- [ ] Monitor error logs
- [ ] Have rollback plan ready

## 7. Monitoring and Health Checks

### Container Health Monitoring
```yaml
# docker-compose.yml health check example
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 45s
```

### Logging Configuration
```bash
# Centralized logging
docker-compose logs --tail=100 backend
journalctl -u docker.service

# Recommended logging drivers
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Metrics Collection
- Prometheus endpoint at `/metrics`
- Grafana dashboard recommended
- Track key performance indicators:
  - Request latency
  - Error rates
  - Database connection pool
  - Memory and CPU usage

## 8. Reverse Proxy Integration

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name partshub.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/partshub.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/partshub.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Traefik Configuration
```yaml
# traefik.yml
http:
  routers:
    frontend:
      rule: "Host(`partshub.yourdomain.com`)"
      service: frontend
      tls:
        certResolver: letsencrypt

    backend:
      rule: "Host(`partshub.yourdomain.com`) && PathPrefix(`/api`)"
      service: backend
      tls:
        certResolver: letsencrypt
```

## Conclusion

Follow these guidelines to ensure a secure, performant, and reliable PartsHub production deployment. Always test thoroughly and monitor your application closely.

**Recommended Next Steps**:
- Perform comprehensive security audit
- Set up centralized logging
- Implement automated backup procedures
- Conduct regular dependency and security updates