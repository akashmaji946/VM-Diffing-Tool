# Mounting VM Disk Images in Docker

This guide explains how to make your qcow2 and other VM disk images accessible to the dockerized VM-Diffing-Tool.

## 🔍 How It Works

Docker uses **volume mounts** to make host filesystem directories accessible inside containers. The container can then read these files as if they were local.

## 📂 Mounting Options

### Option 1: Mount a Specific Directory (Recommended)

If your VM images are in a specific directory (e.g., `/var/lib/libvirt/images`), mount that directory:

**Edit `docker-compose.yml`:**
```yaml
volumes:
  - /var/lib/libvirt/images:/vm-images:ro
```

**Usage in the app:**
- Access files as: `/vm-images/your-vm.qcow2`

**Example:**
```bash
# Your qcow2 files are in /home/user/virtual-machines/
# Edit docker-compose.yml:
volumes:
  - /home/user/virtual-machines:/vm-images:ro

# Then in the web app, use path: /vm-images/ubuntu.qcow2
```

### Option 2: Mount Multiple Directories

If you have VM images in different locations:

```yaml
volumes:
  - /var/lib/libvirt/images:/libvirt-images:ro
  - /home/user/vms:/user-vms:ro
  - /mnt/storage/backups:/backup-vms:ro
```

**Usage in the app:**
- `/libvirt-images/vm1.qcow2`
- `/user-vms/vm2.qcow2`
- `/backup-vms/vm3.qcow2`

### Option 3: Mount Entire Filesystem (Not Recommended)

For maximum flexibility but less security:

```yaml
volumes:
  - /:/host:ro
```

**Usage in the app:**
- Access any file: `/host/var/lib/libvirt/images/vm.qcow2`
- Access home: `/host/home/user/vm.qcow2`

⚠️ **Warning:** This gives the container read access to your entire filesystem.

### Option 4: Mount Individual Files

For specific VM images:

```yaml
volumes:
  - /path/to/vm1.qcow2:/vm-images/vm1.qcow2:ro
  - /path/to/vm2.qcow2:/vm-images/vm2.qcow2:ro
```

## 🚀 Complete Examples

### Example 1: Standard libvirt Setup

```yaml
# docker-compose.yml
services:
  vmtool-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vmtool-server
    ports:
      - "8000:8000"
    volumes:
      - /var/lib/libvirt/images:/vm-images:ro
      - ./frontend/server/database:/app/frontend/server/database
      - ./frontend/server/.env:/app/frontend/server/.env:ro
    privileged: true
    devices:
      - /dev/kvm:/dev/kvm
    restart: unless-stopped
```

**In the web app, enter:** `/vm-images/your-vm.qcow2`

### Example 2: Custom VM Directory

```yaml
volumes:
  - /home/akashmaji/VMs:/my-vms:ro
  - ./frontend/server/database:/app/frontend/server/database
  - ./frontend/server/.env:/app/frontend/server/.env:ro
```

**In the web app, enter:** `/my-vms/ubuntu-server.qcow2`

### Example 3: Multiple Sources

```yaml
volumes:
  # Production VMs
  - /var/lib/libvirt/images:/production:ro
  # Development VMs
  - /home/user/dev-vms:/development:ro
  # Backup VMs
  - /mnt/backup/vms:/backups:ro
  # Database and config
  - ./frontend/server/database:/app/frontend/server/database
  - ./frontend/server/.env:/app/frontend/server/.env:ro
```

**In the web app, enter:**
- Production: `/production/prod-vm.qcow2`
- Development: `/development/test-vm.qcow2`
- Backup: `/backups/old-vm.qcow2`

## 🛠️ Using Docker CLI Instead of Compose

If you prefer `docker run`:

```bash
docker run -d \
  --name vmtool-server \
  --privileged \
  --device /dev/kvm:/dev/kvm \
  -p 8000:8000 \
  -v /var/lib/libvirt/images:/vm-images:ro \
  -v $(pwd)/frontend/server/database:/app/frontend/server/database \
  -v $(pwd)/frontend/server/.env:/app/frontend/server/.env:ro \
  vmtool:latest
```

## 📋 Step-by-Step Setup

### 1. Find Your VM Images

```bash
# Common locations:
ls /var/lib/libvirt/images/
ls ~/VirtualMachines/
ls /home/$USER/vms/

# Or search for qcow2 files:
find /home -name "*.qcow2" 2>/dev/null
find /var -name "*.qcow2" 2>/dev/null
```

### 2. Update docker-compose.yml

```bash
cd /home/akashmaji/Documents/VM-Diffing-Tool
nano docker-compose.yml
```

Change the volume mount to your directory:
```yaml
volumes:
  - /your/vm/directory:/vm-images:ro
```

### 3. Start the Container

```bash
docker-compose up -d
```

### 4. Verify Access

```bash
# List files in the mounted directory
docker exec vmtool-server ls -lh /vm-images

# Check if a specific file is accessible
docker exec vmtool-server ls -lh /vm-images/your-vm.qcow2
```

### 5. Use in Web App

Navigate to `http://localhost:8000` and enter paths like:
- `/vm-images/your-vm.qcow2`

## 🔒 Read-Only vs Read-Write

### Read-Only (`:ro`) - Recommended
```yaml
- /var/lib/libvirt/images:/vm-images:ro
```
✅ Prevents accidental modifications
✅ Safer for production VMs
✅ Good for analysis and comparison

### Read-Write (default)
```yaml
- /var/lib/libvirt/images:/vm-images
```
⚠️ Allows modifications (use with caution!)

## 🐛 Troubleshooting

### "File not found" Error

1. **Check the mount:**
   ```bash
   docker exec vmtool-server ls -lh /vm-images
   ```

2. **Verify host path exists:**
   ```bash
   ls -lh /var/lib/libvirt/images
   ```

3. **Check permissions:**
   ```bash
   # Container runs as root, but check file permissions
   ls -l /var/lib/libvirt/images/*.qcow2
   ```

### Permission Denied

The container needs read access to the files:
```bash
# Make files readable (if needed)
sudo chmod +r /path/to/vm.qcow2

# Or change ownership
sudo chown $USER:$USER /path/to/vm.qcow2
```

### libguestfs Can't Open Disk

Ensure the container has:
1. **Privileged mode:** `privileged: true`
2. **KVM access:** `devices: - /dev/kvm:/dev/kvm`

```bash
# Verify KVM is available
docker exec vmtool-server ls -l /dev/kvm
```

## 💡 Best Practices

1. **Use read-only mounts** (`:ro`) to prevent accidental modifications
2. **Mount specific directories** rather than entire filesystem
3. **Use absolute paths** in docker-compose.yml
4. **Test access** before using in the web app:
   ```bash
   docker exec vmtool-server ls -lh /vm-images
   ```
5. **Keep backups** of important VM images
6. **Use descriptive mount points** (e.g., `/production`, `/backups`)

## 📝 Quick Reference

| Host Path | Container Path | Usage in App |
|-----------|---------------|--------------|
| `/var/lib/libvirt/images` | `/vm-images` | `/vm-images/vm.qcow2` |
| `/home/user/VMs` | `/my-vms` | `/my-vms/vm.qcow2` |
| `/mnt/storage` | `/storage` | `/storage/vm.qcow2` |
| Entire filesystem `/` | `/host` | `/host/path/to/vm.qcow2` |

## 🎯 Recommended Configuration

For most users, this is the recommended setup:

```yaml
# docker-compose.yml
services:
  vmtool-app:
    # ... other settings ...
    volumes:
      # Replace with your actual VM directory
      - /var/lib/libvirt/images:/vm-images:ro
      - ./frontend/server/database:/app/frontend/server/database
      - ./frontend/server/.env:/app/frontend/server/.env:ro
    privileged: true
    devices:
      - /dev/kvm:/dev/kvm
```

Then in the web app, use paths like: `/vm-images/your-vm.qcow2`

---

**Need help?** Contact: akashmaji@iisc.ac.in
