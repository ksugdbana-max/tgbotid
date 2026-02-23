FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + Node.js for frontend build
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy full project
COPY . .

# Build the React frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Return to app root
WORKDIR /app

# Expose port
EXPOSE 7860

# Start FastAPI (which serves the built frontend from /frontend/dist)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", \
     "--bind", "0.0.0.0:7860", \
     "--workers", "1", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
