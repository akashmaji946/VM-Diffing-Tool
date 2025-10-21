# VM-Diffing-Tool

A powerful web-based tool for analyzing and comparing virtual machine disk images. Built with Flask, C++ (pybind11), and libguestfs, this tool provides an intuitive interface for forensic analysis, backup verification, and VM state comparison.

![ascii-art-text](images/ascii-art-text.png)

Go to Docs here: [VM-Diffing-Tool Docs](https://akashmaji946.github.io/VM-Diffing-Tool/)

## 🌟 Features

### VM Disk Analysis
- **List Files**: Browse all files in a VM disk image
- **File Contents**: View file contents with syntax highlighting
- **Disk Metadata**: View partition information, filesystem types, and disk properties
- **File Search**: Check if specific files exist in the VM

### Comparison Tools
- **File Compare**: Side-by-side comparison of files from different VM disks
- **Files Diff**: Compare file lists between two VM disks
- **Directory Compare**: Recursively compare directories across VM images
- **Block Compare**: Compare blockwise data of two VM disks
- **Convert**: Convert VM disk images to different formats
- **Run VM**: Run a VM from a disk image
- **Export Reports**: Export comparison results as JSON or PDF

### User Management
- **Secure Authentication**: Email-based user registration with verification
- **Gmail OAuth**: Automated email verification system
- **Session Management**: Secure login/logout with Flask-Login

### Modern UI
- **Responsive Design**: Built with Pico CSS for clean, modern interface
- **Dark/Light Theme**: Toggle between themes with persistent preference
- **Interactive Tables**: AG Grid and DataTables for powerful data viewing
- **Real-time Notifications**: Flash messages with dismissible alerts

## 🏗️ Architecture

```
VM-Diffing-Tool/
├── backend/              # C++ core with pybind11 bindings
│   ├── src/
│   │   └── VMTool.cpp   # Core VM analysis logic
│   ├── include/
│   │   └── VMTool.hpp   # Header files
│   └── pybind11/        # Python bindings submodule
│   └── main.cpp        
├── frontend/
|   ├── vmt/             # CLI tool
│   ├── server/          # Flask web application
│   │   ├── app.py       # Main Flask application
│   │   ├── models.py    # Database models
│   │   ├── config.py    # Configuration
│   │   └── templates/   # HTML templates
│   └── vmtool_scripts/  # Frontend scripts
└── guestfs/             # Libguestfs Python bindings
```

## 🚀 Installation

### Docker Installation (Recommended)

Refer to [docker/DOCKER.md](docker/DOCKER.md) for detailed Docker installation instructions.

**Quick Start:**
```bash
# Navigate to docker directory
cd docker

# Build and start the container
docker-compose up -d

# View logs
docker logs VMT-Docker -f

# Stop the container
docker-compose down
```

The application will be available at `http://localhost:8000`

For manual Docker build or advanced configuration, see [docker/DOCKER.md](docker/DOCKER.md) and [docker/MOUNTING_VM_IMAGES.md](docker/MOUNTING_VM_IMAGES.md).

### Prerequisites

- **Python 3.8+**
- **CMake 3.15+**
- **C++ Compiler** (GCC/Clang with C++17 support)
- **libguestfs** and dependencies
- **SQLite3**

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    cmake \
    g++ \
    libguestfs-dev \
    libguestfs-tools \
    python3-guestfs

# Fedora/RHEL
sudo dnf install -y \
    python3-devel \
    cmake \
    gcc-c++ \
    libguestfs-devel \
    libguestfs-tools \
    python3-libguestfs
```

### Build Backend

```bash
cd backend
git submodule update --init --recursive  # Initialize pybind11
mkdir build && cd build
cmake ..
make
sudo make install  # Or: export PYTHONPATH=/path/to/build
```

### Install Frontend Dependencies

```bash
cd frontend/server
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file**:
```bash
cp .env.sample .env
```

Refer file `.env.sample` (inside `frontend/server`) for more details.

2. **Configure Gmail OAuth** (for email verification):
```env
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
EMAIL_VERIFICATION_REQUIRED=True
BASE_URL=http://localhost:8000 #or your domain
```

3. **Generate Secret Key**:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```
Add to `.env` as `SECRET_KEY=<generated-key>`

## 🎯 Usage

### Start the Server

```bash
cd frontend/server
sudo python3 app.py
```

The server will start on `http://localhost:8000`

### First Time Setup

1. Navigate to `http://localhost:8000`
2. Click **Sign Up** to create an account
3. Verify your email (check inbox/spam)
4. Log in with your credentials

### Analyzing VM Disks

1. **List Files**:
   - Go to "List Files"
   - Enter VM disk path (e.g., `/path/to/vm.qcow2`)
   - Browse the file tree

2. **Compare Files**:
   - Go to "File Compare"
   - Enter two VM disk paths
   - Enter file path to compare
   - View side-by-side diff

3. **Directory Comparison**:
   - Go to "Compare Files In Directory"
   - Enter two VM disk paths and directory path
   - View comprehensive comparison report

4. **Export Results**:
   - Use "Export as PDF" or "Export as JSON" buttons
   - Save comparison reports for documentation

## 🛠️ CLI (vmt) Setup and Usage

The project ships a command-line tool named `vmt` for running VM inspection utilities from the terminal. The CLI dynamically discovers commands from `frontend/vmtool_scripts/` and executes them.

### Install the CLI (development/editable mode)

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv .vm
source .vm/bin/activate

# Install Python dependencies at repo root
pip3 install -r requirements.txt

# Install the vmt CLI (editable)
cd frontend
# install in env
pip3 install -e .
# install in system
sudo pip3 install . --break-system-packages

# check version
which vmt
vmt -v
```

Editable install means any changes you make to `frontend/vmt/vmt.py` take effect immediately.

### Verify installation

```bash
which vmt       # should show the vmt entry point in your venv
vmt -h          # global help
vmt -v          # version
vmt list        # list all available commands detected from vmtool_scripts
```

If `vmt list` shows no commands, ensure the directory exists: `frontend/vmtool_scripts/`.

### How command discovery works

- `vmt` discovers scripts matching the pattern `vmtool_*.py` inside `frontend/vmtool_scripts/`.
- It exposes them as commands by stripping the `vmtool_` prefix. For example:
  - `vmtool_check_file_exists_in_disk.py` → `check_file_exists_in_disk`
  - `vmtool_get_disk_meta_data.py` → `get_disk_meta_data`
  - `vmtool_get_all_files_in_disk_json.py` → `get_all_files_in_disk_json`
  - `vmtool_get_file_contents_in_disk.py` → `get_file_contents_in_disk`
  - `vmtool_get_file_contents_in_disk_format.py` → `get_file_contents_in_disk_format`
  - `vmtool_list_all_filenames_in_disk.py` → `list_all_filenames_in_disk`
  - `vmtool_list_all_files_in_disk.py` → `list_all_files_in_disk`
  - `vmtool_list_files_in_directory_in_disk.py` → `list_files_in_directory_in_disk`
  - `vmtool_vmmanager_create_vbox_from_iso.py` → `vmmanager_create_vbox_from_iso`
  - `vmtool_vmmanager_run_qemu_vm.py` → `vmmanager_run_qemu_vm`
  - `vmtool_vmmanager_stop_qemu_vm.py` → `vmmanager_stop_qemu_vm`
  - `vmtool_vmmanager_list_qemu_vms.py` → `vmmanager_list_qemu_vms`
  -  `vmtool_convertor.py` → `convertor`

### Global usage

```bash
vmt -h | --help     # Print global help and list available commands
vmt -v | --version  # Print version
vmt list            # List all discovered commands
vmt -c <command>    # Run a specific command; append -h for command help
```

### Examples

```bash
# Check if a file exists inside a guest
vmt -c check_file_exists_in_disk \
  --disk /path/to/disk.qcow2 \
  --name /etc/hosts

# Get aggregated disk metadata (JSON)
vmt -c get_disk_meta_data \
  --disk /path/to/disk.qcow2 \
  --json $PWD/meta.json

# Dump a guest file
vmt -c get_file_contents_in_disk \
  --disk /path/to/disk.qcow2 \
  --name /etc/hosts

# Dump a guest file in hex format
vmt -c get_file_contents_in_disk_format \
  --disk /path/to/disk.qcow2 \
  --name /bin/bash \
  --format hex \
  --out $PWD/output.txt

# List all file names and save to JSON
vmt -c list_all_filenames_in_disk \
  --disk /path/to/disk.qcow2 \
  --json $PWD/output.json

# List files of a guest directory
vmt -c list_files_in_directory_in_disk \
  --disk /path/to/disk.qcow2 \
  --directory /etc \
  --detailed

# Run a QEMU VM
vmt -c vmmanager_run_qemu_vm \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048

# Run a VBox VM
vmt -c vmmanager_run_vbox_vm \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048

# Run a VMWare VM
vmt -c vmmanager_run_vmware_vmdk \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048

# Convert a disk
vmt -c convertor \
  --src_img /path/to/src.qcow2 \
  --dest_img /path/to/dest.vdi \
  --src_format qcow2 \
  --dest_format vdi

# Create a VBox VM from ISO
vmt -c vmmanager_create_vbox_from_iso \
  --iso /path/to/iso.iso \
  --vdi_dir /path/to/vdi_dir \
  --vm_name vm_name \
  --ostype ostype \
  --memory_mb memory_mb \
  --cpus cpus


```

### Script Reference: Convert and VM Launch

This project ships helper scripts under `frontend/converter_scripts/` and `frontend/vmmanager_scripts/`. You can run them directly with Python, or via the `vmt` CLI using the mapped command names shown below.

#### Convert a disk image (qemu-img)

- Python script: `frontend/converter_scripts/vmtool_convertor.py`
- vmt command: `convertor`

Usage (direct):

```bash
python3 frontend/converter_scripts/vmtool_convertor.py \
  --src_img /path/to/src.qcow2 \
  --dest_img /path/to/dest.vdi \
  --src_format qcow2 \
  --dest_format vdi
```

Usage (via vmt):

```bash
vmt -c convertor \
  --src_img /path/to/src.qcow2 \
  --dest_img /path/to/dest.vdi \
  --src_format qcow2 \
  --dest_format vdi
```

Notes:
- The destination directory must be writable. When running inside Docker, ensure the path is mounted read-write.
- Supported formats depend on `qemu-img` (e.g., qcow2, vdi, vmdk, raw).

#### Run a QEMU VM from a disk

- Python script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_qemu_vm.py`
- vmt command: `vmmanager_run_qemu_vm`

Usage (via vmt):

```bash
vmt -c vmmanager_run_qemu_vm \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048 \
  --name my-vm [--no-kvm] [--uefi] [--convert]
```

Headless/VNC inside Docker:
- Headless fallback: the backend will auto-use `-display none` when no `DISPLAY` is present.
- Force headless: set `VMTOOL_QEMU_HEADLESS=1` in the environment.
- VNC mode: set `VMTOOL_QEMU_VNC=<N>` to enable `-display none -vnc :N` and map the port (e.g., `-p 5900:5900` for `N=0`). Then connect your VNC viewer to `127.0.0.1:5900`.

Networking:
- User networking is enabled with SSH forward: host `127.0.0.1:2222` -> guest `22`.

#### Run a VirtualBox VM from a disk

- Python script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_vbox_vm.py`
- vmt command: `vmmanager_run_vbox_vm`

Usage (via vmt):

```bash
vmt -c vmmanager_run_vbox_vm \
  --disk /path/to/disk.vdi \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --ostype Ubuntu_64 [--bridged-if eth0] [--convert]
```

Notes:
- VirtualBox operations require VBox kernel modules on the host. If using Docker, it is generally easier to run VBox on the host directly.

#### Run a VMware VM from a VMDK

- Python script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_vmware_vmdk.py`
- vmt command: `vmmanager_run_vmware_vmdk`

Usage (via vmt):

```bash
vmt -c vmmanager_run_vmware_vmdk \
  --disk /path/to/disk.vmdk \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --guestos ubuntu22-64 \
  [--vm-dir ~/vmware/my-vm] \
  [--nic-model e1000|e1000e|vmxnet3] \
  [--no-net] [--convert] [--nogui]
```

Notes:
- VMware is a host hypervisor; `vmrun/vmplayer` and kernel modules must be installed on the host. Running VMware fully inside Docker is not recommended. Use the script to prepare the VM and launch commands on the host.


### Notes on permissions

Many operations require elevated privileges for libguestfs access. `vmt` runs the underlying scripts using `sudo python3 …`. If prompted, provide your sudo password.

### Portability notes

This CLI discovers scripts from the repository layout (`frontend/vmtool_scripts/`) when installed in editable mode. If you plan to distribute the CLI without the repo, include those scripts alongside the install or package them inside the wheel.

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home dashboard |
| `/login` | GET/POST | User login |
| `/signup` | GET/POST | User registration |
| `/logout` | GET | User logout |
| `/list-files` | GET/POST | List files in VM disk |
| `/files-json` | GET/POST | Get file list as JSON |
| `/meta` | GET/POST | Get disk metadata |
| `/file-contents` | GET/POST | View file contents |
| `/file-compare` | GET/POST | Compare two files |
| `/files-diff` | GET/POST | Compare file lists |
| `/directory-diff` | GET/POST | Compare directories |
| `/verify-email/<token>` | GET | Email verification |

## 🛡️ Security

- **Password Hashing**: Werkzeug's secure password hashing
- **Email Verification**: Token-based email confirmation
- **Session Management**: Secure cookie-based sessions
- **CSRF Protection**: Built-in Flask CSRF protection
- **Input Validation**: Server-side validation for all inputs

## 🧪 Development

### Running in Debug Mode

The server runs in debug mode by default. Flask's auto-reloader will restart the server when code changes are detected.

### Database

SQLite database is created automatically at `frontend/server/database/users.db`

To reset the database:
```bash
rm -rf frontend/server/database/*
```

## 📝 Configuration Options

**Environment Variables** (`.env`):

- `SECRET_KEY`: Flask secret key for sessions
- `GMAIL_USER`: Gmail address for sending emails
- `GMAIL_APP_PASSWORD`: Gmail app-specific password
- `EMAIL_VERIFICATION_REQUIRED`: Enable/disable email verification (`True`/`False`)
- `BASE_URL`: Base URL for email verification links
- `EMAIL_VERIFICATION_TOKEN_MAX_AGE`: Token expiration time in seconds (default: 3600)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the GPL-3.0 License.

## 🙏 Acknowledgments

- **libguestfs**: For VM disk access capabilities
- **pybind11**: For seamless C++ and Python integration
- **Flask**: For the web framework
- **Pico CSS**: For the beautiful UI

## 📞 Support

- For issues and questions, please open an issue on the project repository.
- Contact: [akashmaji@iisc.ac.in](mailto:akashmaji@iisc.ac.in)

---

**Built with ❤️ for VM analysis**
```
'##::::'##:'##::::'##:'########::'#######:::'#######::'##:::::::
 ##:::: ##: ###::'###:... ##..::'##.... ##:'##.... ##: ##:::::::
 ##:::: ##: ####'####:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
 ##:::: ##: ## ### ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
. ##:: ##:: ##. #: ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
:. ## ##::: ##:.:: ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
::. ###:::: ##:::: ##:::: ##::::. #######::. #######:: ########:
:::...:::::..:::::..:::::..::::::.......::::.......:::........::
```
