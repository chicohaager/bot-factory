# Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Build final image
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/app.py .

# Copy built frontend
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Create directories
RUN mkdir -p /app/bots /app/config /app/data

# Environment
ENV CONFIG_PATH=/app/config/tasks.yaml
ENV BOTS_PATH=/app/bots
ENV DB_PATH=/app/data/botfactory.db
ENV STATIC_PATH=/app/frontend/dist
ENV HOST=0.0.0.0
ENV PORT=5000
ENV LOG_LEVEL=INFO

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
