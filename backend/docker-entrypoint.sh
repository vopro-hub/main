#!/bin/bash
set -e

# wait for Postgres
POSTGRES_HOST=${POSTGRES_HOST:-$DATABASE_HOST}
POSTGRES_PORT=${POSTGRES_PORT:-$DATABASE_PORT}

if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
  until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    echo "Postgres not ready - sleeping 2s"
    sleep 2
  done
  echo "Postgres is up - continuing"
fi

# Run migrations, collect static
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# create media dir if not exists and set safe permissions
mkdir -p ${MEDIA_ROOT:-/vol/web/media}
chown -R www-data:www-data ${MEDIA_ROOT:-/vol/web/media} || true

# exec the container CMD
exec "$@"
