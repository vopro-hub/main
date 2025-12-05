# Deployment — Docker Compose / Coolify

## Overview
This repo contains everything required to run the Virtual Office backend (Django + Channels + Celery) and frontend (React) with Docker Compose.

## Pre-reqs (local)
- Docker & Docker Compose
- Python 3.12 (for local dev)
- Node 18+ (for frontend dev/build)

## Steps (local)
1. Copy `.env.example` to `.env` and fill values.
2. Build & run:
   ```bash
   docker compose up --build
