# ---------------------------
# Base Python Image
# ---------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------------------------
# Install System Dependencies
# ---------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Set Working Directory
# ---------------------------
WORKDIR /app

# ---------------------------
# Install Python Dependencies
# ---------------------------
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# ---------------------------
# Copy Project Files
# ---------------------------
COPY . /app

# ---------------------------
# Add Entrypoint Script
# ---------------------------
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ---------------------------
# Gunicorn (production WSGI)
# ---------------------------
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

EXPOSE 8000
