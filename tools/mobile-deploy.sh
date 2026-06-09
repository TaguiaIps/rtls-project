#!/bin/bash
# tools/mobile-deploy.sh - Orchestrates mobile build and distribution
set -e

echo "📱 Initiating Mobile Deployment Flow..."

# 1. Environment Check
if ! command -v eas &> /dev/null; then
    echo "❌ EAS CLI not found. Please run 'npm install -g eas-cli' first."
    exit 1
fi

# 2. Workspace Pre-flight
echo "🔍 Validating monorepo contracts..."
npm run build --workspace apps/mobile

# 3. Parameters
STRATEGY=${1:-preview}
PLATFORM=${2:-android}
MODE=${3:-remote}

EXTRA_FLAGS="--non-interactive"
if [ "$MODE" == "local" ]; then
    EXTRA_FLAGS="$EXTRA_FLAGS --local"
    # Essential for local builds
    export NODE_ENV=production
    export SKIP_EXPO_DOCTOR=1
    
    # If Java 17 is installed in a common path, try to use it to avoid Gradle IBM_SEMERU error
    if [ -z "$JAVA_HOME" ] && [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
        export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
        echo "☕ Using Java 17 from $JAVA_HOME"
    fi
fi

case $STRATEGY in
  "init")
    echo "🔗 Connecting project to Expo (EAS)..."
    cd apps/mobile && npx eas-cli init --id a8803e18-189c-40d4-985c-ab65217d9756
    ;;
  "preview")
    echo "🏗️ Building Internal Preview ($PLATFORM) [$MODE]..."
    cd apps/mobile && eas build --platform "$PLATFORM" --profile preview $EXTRA_FLAGS
    ;;
  "update")
    echo "🚀 Sending OTA (Over-The-Air) Update..."
    cd apps/mobile && eas update --branch main --message "${2:-Manual update from CLI}"
    ;;
  "production")
    echo "💎 Building Production Binaries ($PLATFORM) [$MODE]..."
    cd apps/mobile && eas build --platform "$PLATFORM" --profile production $EXTRA_FLAGS
    ;;
  *)
    echo "Usage: ./tools/mobile-deploy.sh [init|preview|update|production] [platform] [local|remote]"
    echo "Example: ./tools/mobile-deploy.sh preview android local"
    exit 1
    ;;
esac

echo "✅ Mobile flow complete!"
