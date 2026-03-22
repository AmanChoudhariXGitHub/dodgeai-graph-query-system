# Multi-stage build for Graph Query System

# Stage 1: Backend builder
FROM python:3.11-slim as backend-builder

WORKDIR /app/backend

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Stage 2: Frontend builder
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend code
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 3: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install Node runtime for frontend serving
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from builder
COPY --from=backend-builder /app/backend /app/backend

# Copy frontend build from builder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Install Python dependencies again for runtime
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 8000 5173

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://localhost/graph_query_db
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start both services
CMD ["sh", "-c", "cd /app/backend && python main.py & cd /app/frontend && npx serve -s dist -l 5173"]
