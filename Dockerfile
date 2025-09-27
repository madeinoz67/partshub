# Multi-service Dockerfile for PartsHub - Frontend (Vue.js dev server) + Backend (FastAPI)
FROM node:18-alpine

# Install Python and required build tools + libmagic for file type detection + zbar for barcode scanning
RUN apk add --no-cache python3 py3-pip python3-dev make g++ curl file-dev libmagic zbar zbar-dev

# Set working directory
WORKDIR /app

# Install Python uv (bypass externally managed environment)
RUN pip3 install uv --break-system-packages

# Copy and install Python dependencies (consolidated)
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system --break-system-packages -r pyproject.toml

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
ENV DATABASE_URL=sqlite:///./data/partshub.db
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