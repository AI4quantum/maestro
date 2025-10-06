# Multi-stage build: build static assets with Node, serve with NGINX

FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# Basic security headers and SPA fallback
RUN printf "server {\n  listen 80;\n  server_name _;\n  add_header X-Content-Type-Options nosniff;\n  add_header X-Frame-Options SAMEORIGIN;\n  add_header X-XSS-Protection '1; mode=block';\n  location / {\n    try_files $uri /index.html;\n  }\n}\n" > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


