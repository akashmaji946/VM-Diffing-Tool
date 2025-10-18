# Multi-stage Dockerfile for VM-Diffing-Tool
# Stage 1: Build the base image (can be pre-built and cached)
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    git \
    python3.10 \
    python3.10-dev \
    python3-pip \
    libguestfs-dev \
    libguestfs-tools \
    python3-guestfs \
    libguestfs0 \
    qemu-utils \
    sqlite3 \
    libsqlite3-dev \
    linux-image-generic \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

WORKDIR /app

# Stage 2: Build backend
FROM base AS backend-builder

# Copy backend source code
COPY backend/ /app/backend/
COPY guestfs/ /app/guestfs/

# Initialize git submodules for pybind11
WORKDIR /app/backend
RUN git submodule update --init --recursive || \
    (cd /app/backend && \
     git init && \
     git submodule add https://github.com/pybind/pybind11.git pybind11 || \
     echo "pybind11 already exists")

# Build the backend
RUN mkdir -p build && cd build && \
    cmake .. && \
    make && \
    make install

# Verify vmtool installation
RUN python3 -c "import vmtool; print('vmtool successfully imported')" || \
    echo "Warning: vmtool import failed"

# Stage 3: Final application image
FROM base AS final

# Copy built vmtool from backend-builder
COPY --from=backend-builder /usr/lib/python3.10/site-packages/vmtool*.so /usr/local/lib/python3.10/dist-packages/
COPY --from=backend-builder /usr/lib/python3.10/site-packages/vmtool*.so /usr/lib/python3/dist-packages/

# Copy application code
COPY frontend/ /app/frontend/
COPY requirements.txt /app/
COPY README.md /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Install server-specific dependencies
WORKDIR /app/frontend/server
RUN if [ -f requirements.txt ]; then pip3 install --no-cache-dir -r requirements.txt; fi

# Create necessary directories
RUN mkdir -p /app/frontend/server/database && \
    mkdir -p /app/frontend/server/uploads && \
    chmod -R 755 /app/frontend/server

# Configure libguestfs for Docker environment
RUN mkdir -p /usr/lib/guestfs && \
    update-guestfs-appliance || true

# Set libguestfs environment variables
ENV LIBGUESTFS_BACKEND=direct
ENV LIBGUESTFS_DEBUG=1
ENV LIBGUESTFS_TRACE=1

# Copy environment sample file
COPY frontend/server/.env.sample /app/frontend/server/.env.sample

# Expose port 8000
EXPOSE 8000

# Set working directory to server
WORKDIR /app/frontend/server

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/login')" || exit 1

# Default command
CMD ["python3", "app.py"]
