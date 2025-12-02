# syntax=docker/dockerfile:1

# ============================================
# UI-CLI Docker Image
# Gorilla Powered! 🦍
# ============================================

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .
COPY src/ src/
COPY VERSION .
COPY README.md .

# Install package
RUN pip install --no-cache-dir --user .

# ============================================
# Production image
# ============================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="UI-CLI"
LABEL org.opencontainers.image.description="Manage your UniFi infrastructure from the command line"
LABEL org.opencontainers.image.source="https://github.com/vedanta/ui-cli"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash uicli

# Copy installed packages from builder
COPY --from=builder /root/.local /home/uicli/.local

# Copy application
COPY --chown=uicli:uicli src/ src/
COPY --chown=uicli:uicli VERSION .

# Copy entrypoint
COPY --chown=uicli:uicli docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create config directory for session persistence
RUN mkdir -p /home/uicli/.config/ui-cli && \
    chown -R uicli:uicli /home/uicli/.config

# Switch to non-root user
USER uicli

# Add local bin to PATH
ENV PATH="/home/uicli/.local/bin:${PATH}"

# Environment variables (override at runtime)
ENV UNIFI_API_KEY=""
ENV UNIFI_CONTROLLER_URL=""
ENV UNIFI_CONTROLLER_USERNAME=""
ENV UNIFI_CONTROLLER_PASSWORD=""
ENV UNIFI_CONTROLLER_SITE="default"
ENV UNIFI_CONTROLLER_VERIFY_SSL="false"

# Volume for session persistence
VOLUME ["/home/uicli/.config/ui-cli"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["--help"]
