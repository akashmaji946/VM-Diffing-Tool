# Docker Deployment Guide for VM-Diffing-Tool

This guide explains how to build and run the VM-Diffing-Tool using Docker.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 1.29+
- At least 4GB of free disk space
- Access to VM disk images you want to analyze

## 🏗️ Architecture

The Docker setup uses a multi-stage build process:

1. **Base Stage**: Installs all C++ and Python system dependencies (libguestfs, CMake, etc.)
2. **Backend Builder Stage**: Compiles the C++ backend with pybind11 to create the `vmtool` Python module
3. **Final Stage**: Copies the compiled `vmtool` module and sets up the Flask frontend server

## 🚀 Quick Start

### 1. Configure Environment Variables

Create a `.env` file in `frontend/server/`:

```bash
cd frontend/server
cp .env.sample .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-random-secret-key-here
BASE_URL=http://localhost:8000
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
EMAIL_VERIFICATION_REQUIRED=true
EMAIL_VERIFICATION_TOKEN_MAX_AGE=3600
MAIL_AUTH_METHOD=password
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The application will be available at `http://localhost:8000`

### 3. Alternative: Build with Docker Only

```bash
# Build the image
docker build -t vmtool:latest .

# Run the container
docker run -d \
  --name VMT-Docker \
  --privileged \
  --device /dev/kvm:/dev/kvm \
  -p 8000:8000 \
  -v $HOME:$HOME:ro \
  -v $(pwd)/frontend/server/database:/app/frontend/server/database \
  -v $(pwd)/frontend/server/.env:/app/frontend/server/.env:ro \
  vmtool:latest
```

## 📁 Volume Mounts

The Docker setup uses several volume mounts:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `$HOME` | `$HOME` | Your home directory with VM disk images (read-only) |
| `./frontend/server/database` | `/app/frontend/server/database` | SQLite database persistence |
| `./frontend/server/.env` | `/app/frontend/server/.env` | Environment configuration |

### Accessing VM Images

The container mounts your entire home directory (`$HOME`) to the same path inside the container. This means:

- Any VM images in your home directory are automatically accessible
- Use the full path in the web app (e.g., `/home/username/VMs/vm.qcow2`)
- The mount is read-only (`:ro`) to prevent accidental modifications

**Example paths:**
```bash
# If your VM is at: /home/akashmaji/VirtualBox VMs/Ubuntu/ubuntu.qcow2
# Use in the app:  /home/akashmaji/VirtualBox VMs/Ubuntu/ubuntu.qcow2
```

## 🔧 Building the Base Image Separately (Optional)

For faster rebuilds during development, you can build the base image separately:

```bash
# Build base image with all dependencies
docker build -f Dockerfile.base -t vmtool-base:latest .

# Modify Dockerfile to use the base image
# Change: FROM ubuntu:22.04 AS base
# To:     FROM vmtool-base:latest AS base

# Build the application
docker build -t vmtool:latest .
```

## 🐛 Troubleshooting

### Container Won't Start

Check logs:
```bash
docker-compose logs -f
# or
docker logs VMT-Docker -f
```

### Permission Issues with libguestfs

The container needs privileged mode to access disk images:
```yaml
privileged: true
devices:
  - /dev/kvm:/dev/kvm
```

### vmtool Module Not Found

Verify the module was built correctly:
```bash
docker exec -it VMT-Docker python3 -c "import vmtool; print(vmtool.__file__)"
```

### Database Permissions

Ensure the database directory is writable:
```bash
chmod -R 755 frontend/server/database
```

## 🔒 Security Considerations

1. **Privileged Mode**: The container runs in privileged mode to access KVM and disk images. Only run this on trusted systems.

2. **Environment Variables**: Never commit `.env` files with real credentials to version control.

3. **Network Exposure**: By default, the app is exposed on all interfaces (0.0.0.0:8000). For production, use a reverse proxy like Nginx.

4. **VM Images**: Mount VM images as read-only (`:ro`) to prevent accidental modifications.

## 📊 Resource Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 2GB for Docker image + space for VM images and database

## 🔄 Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## 🧹 Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Remove images
docker rmi vmtool:latest
docker rmi vmtool-base:latest

# Clean up build cache
docker builder prune
```

## 📞 Support

For issues related to Docker deployment:
- Check the logs: `docker logs VMT-Docker -f`
- Verify environment configuration
- Ensure all prerequisites are met
- Contact: akashmaji@iisc.ac.in

## 🚀 Quick Reference

```bash
# Start the container
docker-compose up -d

# View logs
docker logs VMT-Docker -f

# Check status
docker ps | grep VMT-Docker

# Access container shell
docker exec -it VMT-Docker bash

# Stop the container
docker-compose down

# Restart the container
docker restart VMT-Docker
```

**Container Name:** `VMT-Docker`  
**Port:** `8000` (host) → `8000` (container)  
**Access URL:** `http://localhost:8000`

---

**Built with ❤️ for VM analysis**
