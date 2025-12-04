#!/bin/bash
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  echo "Postgres not ready - retrying..."
  sleep 2
done
echo "Postgres is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Ensure media folder exists
echo "Ensuring media directory exists..."
mkdir -p /app/media
chown -R www-data:www-data /app/media || true

# Optionally: preload cache, create superuser, etc.

echo "Starting application..."
exec "$@"
