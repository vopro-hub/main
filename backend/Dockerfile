# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# build deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
       git \
    && rm -rf /var/lib/apt/lists/*

# workdir
WORKDIR /app

# copy pip requirements
COPY requirements.txt /app/requirements.txt

# install python deps
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy project
COPY . /app

# create static & media dir
RUN mkdir -p /vol/web/static /vol/web/media

# collect static (will use production settings via DJANGO_SETTINGS_MODULE)
# We do this at container start time in entrypoint for flexibility

# expose port for Daphne
EXPOSE 8000

# default entrypoint (you can override in docker-compose)
COPY ./nginx/docker-entrypoint.sh /app/nginx/docker-entrypoint.sh
RUN chmod +x /app/nginx/docker-entrypoint.sh

ENTRYPOINT ["/app/nginx/docker-entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "PROJECT_NAME.asgi:application"]
