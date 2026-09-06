FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Build the app
COPY frontend/ .
RUN npm run build

# Production stage
FROM node:22-alpine AS production
WORKDIR /app

# Install serve for serving static files
RUN npm install -g serve

# Copy built assets from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npx", "serve", ".next", "-l", "3000"]