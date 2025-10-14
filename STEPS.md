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

# Install guestfs
sudo apt install python3-guestfs

# Create a virtual environment and activate it
python3.12 -m venv .vm 
source .vm/bin/activate

# --- System dependencies for building the C++ backend (vmtool) ---
# Required toolchain and libraries: cmake, build tools, pkg-config, and libguestfs dev headers
# Note: You don't need Python 'guestfs' if you use the C++ backend via pybind11.
# On Debian/Ubuntu:
# sudo apt update
# sudo apt install libguestfs-dev pkg-config
# sudo apt install -y build-essential cmake pkg-config libguestfs-dev python3-dev

# --- Build the pybind11 module (vmtool) ---
# The CMake project is in backend/. This produces a Python extension module named 'vmtool'
# in the backend/build directory (e.g., vmtool.cpython-312-x86_64-linux-gnu.so).

# Configure
# cmake -S backend -B backend/build

# Build
# cmake --build backend/build -j

# --- Run the test without installing Python 'guestfs' ---
# The test script imports the pybind11 module 'vmtool' to query libguestfs version.
# Point PYTHONPATH to the build output so Python can find the module.
# PYTHONPATH=backend/build python3 frontend/test.py

# If you prefer to use the Python guestfs bindings in this repo instead,
# you can try building/installing from the 'guestfs/' folder (requires libguestfs):
#   pip install ./guestfs
# or
#   (cd guestfs && python3 setup.py build && python3 setup.py install)
# However, the recommended path for this project is to use 'vmtool' via pybind11.