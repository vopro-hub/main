# ===========================
# FRONTEND BUILD (Vite)
# ===========================
FROM node:22-alpine AS build

WORKDIR /app

# Install deps
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy project files
COPY . .

# Build Vite
RUN npm run build


# ===========================
# PRODUCTION NGINX SERVER
# ===========================
FROM nginx:1.25-alpine AS runtime

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
