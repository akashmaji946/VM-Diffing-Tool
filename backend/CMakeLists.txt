# Minimum CMake version required
cmake_minimum_required(VERSION 3.15)

# Define the project name and language
project(VmToolBackend LANGUAGES CXX)

# Set the C++ standard to 17 for modern features
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find Dependencies ---

# 1. Find Python
# This finds the Python development libraries needed to build the module.
find_package(Python REQUIRED COMPONENTS Interpreter Development)

# 2. Find libguestfs using pkg-config
# This is the standard way to find libraries on Linux.
find_package(PkgConfig REQUIRED)
pkg_check_modules(GUESTFS REQUIRED guestfs)

# 3. Add pybind11
# We assume pybind11 is a subdirectory (added as a git submodule).
add_subdirectory(pybind11)

# --- Create the Python Module ---

# pybind11_add_module is a special function from pybind11.
# It creates a Python module that is properly named and configured.
# The first argument, "vmtool", is the name you will use in Python: import vmtool
pybind11_add_module(vmtool SHARED
    main.cpp
)

# --- Link Libraries ---

# Link your vmtool module against libguestfs.
target_link_libraries(vmtool PRIVATE
    ${GUESTFS_LIBRARIES}
)

# Add the include directory for libguestfs so the compiler can find its headers.
target_include_directories(vmtool PRIVATE
    ${GUESTFS_INCLUDE_DIRS}
)