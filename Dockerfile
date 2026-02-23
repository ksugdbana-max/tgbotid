# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime (no Node.js = smaller, less memory)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend
COPY backend/ backend/

# Copy ONLY the built frontend dist (no node_modules)
COPY --from=frontend-builder /app/frontend/dist/ frontend/dist/

# Create uploads dir
RUN mkdir -p uploads

# Expose Railway's default port
EXPOSE 8080

# Use shell form so $PORT env var is expanded by Railway
CMD gunicorn -k uvicorn.workers.UvicornWorker backend.main:app \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 1 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
