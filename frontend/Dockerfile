# frontend/Dockerfile
FROM node:18 as build

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH


COPY package.json package-lock.json ./
RUN apk add --no-cache libc6-compat

RUN npm ci

COPY . /app
RUN npm run build

FROM nginx:1.25-alpine AS runtime
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
