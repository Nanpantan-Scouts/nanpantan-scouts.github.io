# syntax=docker/dockerfile:1

# Container image for working on the 1st Nanpantan Scouts website.
# See README.md for how to use it (normally via `docker compose`).
#
# Stages:
#   dev     - Hugo + Go, runs the live-reloading dev server on port 1313
#   build   - builds the production site into /src/public
#   preview - (default) serves the built site with nginx on port 80

# Keep HUGO_VERSION in step with .github/workflows/deploy-hugo.yml so local
# builds match what GitHub Pages publishes.
ARG HUGO_VERSION=0.150.0
ARG GO_VERSION=1.26

FROM golang:${GO_VERSION}-bookworm AS base
ARG HUGO_VERSION
ARG TARGETARCH

# Hugo extended. Go (from the base image) is also required: Hugo uses it to
# download the theme, which is a Hugo Module (see go.mod).
RUN set -eux; \
    curl -fsSL -o /tmp/hugo.tar.gz \
      "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-${TARGETARCH}.tar.gz"; \
    tar -xzf /tmp/hugo.tar.gz -C /usr/local/bin hugo; \
    rm /tmp/hugo.tar.gz; \
    hugo version

# Keep the Hugo/Go caches in one world-writable place so they can be persisted
# in a volume and still work when the container runs as a non-root user.
ENV HUGO_CACHEDIR=/cache/hugo \
    GOCACHE=/cache/go-build \
    HOME=/tmp
RUN mkdir -p /cache/hugo /cache/go-build && chmod -R 1777 /cache

WORKDIR /src


FROM base AS dev
EXPOSE 1313
# --bind 0.0.0.0 makes the server reachable from outside the container.
# --renderToMemory stops the dev server (which includes drafts) writing pages
# into ./public, where they could be mistaken for a real build.
# --poll is used because file-change events don't always reach a container
# (e.g. Docker Desktop with the repo on the Windows drive), so live reload
# would otherwise silently stop working.
CMD ["hugo", "server", "--bind", "0.0.0.0", "--port", "1313", "--buildDrafts", "--renderToMemory", "--poll", "700ms"]


FROM base AS build
# The baseURL in hugo.toml is the live site, and some links (e.g. to blog
# posts) are absolute, so a local preview would jump to production. Override it.
ARG BASE_URL=http://localhost:8080/
COPY . .
RUN hugo --minify --gc --baseURL "${BASE_URL}"


FROM nginx:stable-alpine AS preview
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    error_page 404 /404.html;
    # Redirects (e.g. /about -> /about/) keep whatever host:port you used.
    absolute_redirect off;

    location / {
        try_files $uri $uri/ =404;
    }
}
EOF
COPY --from=build /src/public /usr/share/nginx/html
