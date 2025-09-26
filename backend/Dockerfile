FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for barcode scanning and image processing
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Install dependencies with uv
RUN uv pip install --system -e .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app/src

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]