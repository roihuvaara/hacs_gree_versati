FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

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

# Install the pinned test environment (brings matched HA/pytest versions)
COPY requirements_test.txt /tmp/requirements_test.txt
RUN pip install --no-cache-dir -r /tmp/requirements_test.txt