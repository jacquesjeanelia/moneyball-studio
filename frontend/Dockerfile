# syntax=docker/dockerfile:1

# --- build the static bundle ---
FROM node:22-alpine AS builder

WORKDIR /app

# Install deps first for better layer caching
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .

# VITE_API_BASE_URL is baked at build time. Leave empty to use same-origin
# "/api" (served via the nginx proxy below) — the recommended default.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# --- serve with nginx ---
FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
