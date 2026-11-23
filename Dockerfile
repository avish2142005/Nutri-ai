# ==============================================================================
# KrishiNetra Multi-Stage Production Dockerfile
# Builds the React/Vite frontend and serves the integrated FastAPI backend
# ==============================================================================

# --- Stage 1: Build Frontend Assets ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY farmai/frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY farmai/frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend & Integrated Server ---
FROM python:3.11-slim AS production

# Install OS dependencies for OpenCV, image processing, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set production environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    PORT=8000 \
    HOST=0.0.0.0

# Install Python backend dependencies
COPY farmai/backend/requirements.txt ./farmai/backend/requirements.txt
RUN pip install --no-cache-dir -r ./farmai/backend/requirements.txt

# Copy backend code, models, and knowledge bases
COPY farmai/backend/ ./farmai/backend/
COPY models/ ./models/
COPY severity/ ./severity/

# Copy built frontend assets from Stage 1 into the location expected by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./farmai/frontend/dist

# Expose production port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production server with multiple uvicorn workers
WORKDIR /app/farmai/backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
