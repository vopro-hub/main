#!/bin/bash
set -e

# wait for DB (optional simple wait loop)
host="$POSTGRES_HOST"
port="${POSTGRES_PORT:-5432}"

echo "Waiting for Postgres at $host:$port..."
until nc -z "$host" "$port"; do
  echo "Postgres not ready - sleeping 2s"
  sleep 2
done
echo "Postgres is up - continuing"

# run migrations
python manage.py migrate --noinput

# collect static files
python manage.py collectstatic --noinput

# create media folder permissions
mkdir -p ${MEDIA_ROOT:-/vol/web/media}
chown -R www-data:www-data ${MEDIA_ROOT:-/vol/web/media} || true

# run the CMD from Dockerfile (daphne by default) 
exec "$@"
