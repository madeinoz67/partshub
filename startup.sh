#!/bin/sh
set -e

echo "Starting FastAPI backend on port ${PORT:-8000}..."
cd /app

# Verify data directory exists and is writable
if [ ! -d "/app/data" ]; then
    echo "Creating /app/data directory..."
    mkdir -p /app/data/attachments
    chmod -R 777 /app/data
fi

# Test write permissions
if ! touch /app/data/.write_test 2>/dev/null; then
    echo "ERROR: /app/data is not writable!"
    ls -la /app/data
    exit 1
fi
rm -f /app/data/.write_test

# Run Alembic migrations
echo "Running Alembic migrations..."
cd /app/backend
if ! uv run --project .. alembic upgrade head; then
    echo "ERROR: Alembic migrations failed!"
    echo "DATABASE_URL: $DATABASE_URL"
    echo "Current directory: $(pwd)"
    echo "Data directory contents:"
    ls -la /app/data
    exit 1
fi
cd /app
echo "Migrations completed successfully."

# Seed database with mock data if SEED_DB environment variable is set
if [ "$SEED_DB" = "true" ]; then
    echo "Seeding database with mock data..."
    cd backend && uv run --project .. python -m src.database.seed_data
    cd /app
fi

# Start backend in background
echo "Starting backend from /app/backend..."
cd /app/backend
uv run --project .. uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} &
BACKEND_PID=$!

# Start frontend
echo "Starting Vue.js frontend on port ${FRONTEND_PORT:-3000}..."
cd /app/frontend
npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT:-3000} &
FRONTEND_PID=$!

# Wait for both processes
echo "Both services started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
wait $BACKEND_PID $FRONTEND_PID