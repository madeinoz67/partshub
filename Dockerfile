# Multi-stage Dockerfile for PartsHub - Separate Backend and Frontend builds

# ==============================================================================
# Backend Stage
# ==============================================================================
FROM python:3.11-slim AS backend

# Install system dependencies for backend
RUN apt-get update && apt-get install -y \
    curl \
    file \
    libmagic1 \
    libzbar0 \
    libzbar-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for faster Python dependency management
RUN pip install uv

# Copy Python dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --all-extras

# Copy backend source code
COPY backend/ ./backend/

# Create data directories
RUN mkdir -p /app/data /app/data/attachments

# Set environment variables
ENV DATABASE_URL=sqlite:////app/data/partshub.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Expose backend port
EXPOSE 8000

# Health check for backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start backend application
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================================================
# Frontend Build Stage
# ==============================================================================
FROM node:20-alpine AS frontend-build

# Set working directory
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# ==============================================================================
# Frontend Runtime Stage
# ==============================================================================
FROM nginx:alpine AS frontend

# Copy built frontend from build stage
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration (create a basic one)
RUN echo 'server { \
    listen 3000; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose frontend port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ==============================================================================
# Development Stage (Combined for local development)
# ==============================================================================
FROM node:20-alpine AS development

# Install Python and required build tools + libmagic for file type detection + zbar for barcode scanning
RUN apk add --no-cache python3 py3-pip python3-dev make g++ curl file-dev libmagic zbar zbar-dev

# Set working directory
WORKDIR /app

# Install Python uv (bypass externally managed environment)
RUN pip3 install uv --break-system-packages

# Copy and install Python dependencies (consolidated)
COPY pyproject.toml uv.lock* ./
RUN uv sync --all-extras

# Copy backend source
COPY backend/ ./backend/

# Switch to frontend directory and install dependencies
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Create directories for SQLite database and file storage
WORKDIR /app
RUN mkdir -p /app/data /app/data/attachments

# Set environment variables
ENV DATABASE_URL=sqlite:////app/data/partshub.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV FRONTEND_PORT=3000

# Expose both ports
EXPOSE $FRONTEND_PORT $PORT

# Copy startup script
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Health check for backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Override node entrypoint and run the application
ENTRYPOINT ["/app/startup.sh"]