#!/bin/sh
set -e

echo "Starting FastAPI backend on port ${PORT:-8000}..."
cd /app

# Run database migrations
cd backend && uv run --project .. alembic upgrade head

# Seed database with mock data if SEED_DB environment variable is set
if [ "$SEED_DB" = "true" ]; then
    echo "Seeding database with mock data..."
    uv run --project .. python -m src.database.seed_data
fi

# Start backend in background
uv run --project .. python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} &
BACKEND_PID=$!

# Start frontend
echo "Starting Vue.js frontend on port ${FRONTEND_PORT:-3000}..."
cd /app/frontend
npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT:-3000} &
FRONTEND_PID=$!

# Wait for both processes
echo "Both services started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
wait $BACKEND_PID $FRONTEND_PID