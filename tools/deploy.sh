#!/bin/bash
# tools/deploy.sh - Orchestrates deployment of the entire stack
set -e

echo "🚢 Deploying RTLS Analytics Platform..."

# 1. Pull latest images (if you have a registry)
# docker compose pull

# 2. Prevent port conflicts by stopping current execution
echo "🛑 Stopping existing services to free up ports..."
docker compose stop

# 3. Bring up the stack
echo "🏗️ Bringing up the services..."
docker compose up -d --build

# 4. Wait for healthy services
echo "⏳ Waiting for services to be healthy..."
# We can use docker wait or healthcheck-aware until loop
sleep 5

# 5. Run migrations/initialization
echo "🛠️ Finalizing setup..."
./tools/migrate.sh

echo "✅ Platform deployed successfully!"
echo "📍 Access Web Dashboard: http://localhost:5173"
echo "📍 Access API Docs: http://localhost:8000/docs"
