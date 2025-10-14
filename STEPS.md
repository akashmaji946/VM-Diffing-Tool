
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