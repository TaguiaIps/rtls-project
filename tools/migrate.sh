#!/bin/bash
# tools/migrate.sh - Handles database migrations and schema setup
set -e

echo "🛠️ Running database migrations and schema setup..."

# 1. Wait for Database
# Since we are using Docker for development, we can check if timescaledb is healthy
echo "⏳ Waiting for TimescaleDB to be ready..."
until docker compose exec timescaledb pg_isready -U rtls -d rtls; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

# 2. Trigger Table Creation
# Running a simple health check or starting the app once will trigger create_all()
# We can also run a script specifically for this.
echo "🔄 Initializing schema (triggering Base.metadata.create_all())..."
docker compose exec api python -c "from rtls_api.db import create_session_factory; from rtls_api.config import get_settings; create_session_factory(get_settings())"

# 3. Bootstrap Admin (if needed)
# If this is a fresh setup, you can provide EMAIL, PASSWORD, DISPLAY_NAME env vars
if [ ! -z "$RTLS_ADMIN_EMAIL" ] && [ ! -z "$RTLS_ADMIN_PASSWORD" ]; then
    echo "🔑 Bootstrapping Admin account..."
    docker compose exec api python -m rtls_api.bootstrap_admin \
        --email "$RTLS_ADMIN_EMAIL" \
        --password "$RTLS_ADMIN_PASSWORD" \
        --display-name "${RTLS_ADMIN_NAME:-Admin User}"
fi

echo "✅ Database is up to date!"
