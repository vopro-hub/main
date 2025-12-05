# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH

COPY package.json package-lock.json ./
RUN npm install

COPY . /app
RUN npm run build

# Serve build with nginx (we will let nginx container mount the build)
FROM nginx:1.25-alpine AS runtime

# Copy a minimal nginx config if you want local test (we use main nginx in deploy)
#COPY deploy/nginx.frontend.conf /etc/nginx/conf.d/default.conf

# Copy build output to a named volume (compose mounts)
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
