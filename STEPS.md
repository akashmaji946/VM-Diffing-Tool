mkdir VM-Diffing-Tool
cd VM-Diffing-Tool

# Create folders and files
mkdir backend
mkdir frontend
mkdir docs
mkdir tests
mkdir build

# First, initialize a git repo in your project root
git init

# Add pybind11 to your backend folder
git submodule add https://github.com/pybind/pybind11.git backend/pybind11


# Create a virtual environment and activate it
python3.12 -m venv .vm 
source .vm/bin/activate


# Install guestfs
sudo apt install --reinstall python3-guestfs
 
You should see this:
/usr/lib/python3/dist-packages/guestfs.py
/usr/lib/python3/dist-packages/libguestfsmod.cpython-312-x86_64-linux-gnu.so

# --- System dependencies for building the C++ backend (vmtool) ---
# Required toolchain and libraries: cmake, build tools, pkg-config, and libguestfs dev headers
# Note: You don't need Python 'guestfs' if you use the C++ backend via pybind11.
# On Debian/Ubuntu:
```bash
sudo apt update
sudo apt install libguestfs-dev pkg-config
sudo apt install -y build-essential cmake pkg-config libguestfs-dev python3-dev
```

# --- Build the pybind11 module (vmtool) ---
# The CMake project is in backend/. This produces a Python extension module named 'vmtool'
# in the backend/build directory (e.g., vmtool.cpython-312-x86_64-linux-gnu.so).

# Configure
cmake -S backend -B backend/build

# Build
cmake --build backend/build -j

# DO this to run any script
```bash
export PYTHONPATH=$HOME/Documents/VM-Diffing-Tool/backend/build:$PYTHONPATH
export PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=$HOME/Documents/VM-Diffing-Tool/backend/build:$LD_LIBRARY_PATH
```