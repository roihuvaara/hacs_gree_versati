FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install basic dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to use
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Setup home directory for non-root user
WORKDIR /workspace

# Switch to non-root user
USER $USERNAME

# Install pytest and other testing packages globally (to avoid venv issues)
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-homeassistant-custom-component 