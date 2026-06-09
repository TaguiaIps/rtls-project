#!/bin/bash
# scripts/build.sh - Orchestrates building backend and frontend
set -e

echo "🚀 Building RTLS Analytics Platform..."

# 1. Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# 2. Build API (Python)
echo "🐍 Building Backend (API)..."
# In Python, building usually means preparing the environment and linting/testing
# but we can also build a wheel
if [ -d "apps/api" ]; then
    uv build --project apps/api
fi

# 3. Build Web (Frontend)
echo "🌐 Building Frontend (Web)..."
npm run build --workspace apps/web

# 4. Build Mobile (Typecheck)
echo "📱 Building Mobile (Typecheck)..."
npm run build --workspace apps/mobile

# 5. Docker images build
echo "🐳 Building Docker images..."
docker compose build

echo "✅ Build complete!"
