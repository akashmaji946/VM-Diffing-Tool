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
# 2. Find libguestfs manually (Ubuntu doesn't ship guestfs.pc)
find_path(GUESTFS_INCLUDE_DIRS guestfs.h
    PATHS /usr/include /usr/local/include /usr/lib/python3/dist-packages
)

find_library(GUESTFS_LIBRARIES guestfs
    PATHS /usr/lib /usr/lib64 /usr/lib/x86_64-linux-gnu /usr/local/lib /usr/lib/python3/dist-packages
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(GUESTFS DEFAULT_MSG
    GUESTFS_LIBRARIES GUESTFS_INCLUDE_DIRS
)

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


message(STATUS "Installing vmtool to: ${Python_SITEARCH}")
# --- Install the module .so file in Python site-packages ---
# Standard Python path: lib/pythonX.Y/site-packages
install(TARGETS vmtool
    LIBRARY DESTINATION lib/python${Python_VERSION_MAJOR}.${Python_VERSION_MINOR}/site-packages
)

# also install in /usr/lib/pythonX.Y/site-packages
install(TARGETS vmtool
    LIBRARY DESTINATION /usr/lib/python${Python_VERSION_MAJOR}.${Python_VERSION_MINOR}/site-packages
)

# also install in /usr/lib/python3/dist-packages
install(TARGETS vmtool
    LIBRARY DESTINATION /usr/lib/python3/dist-packages
)


# Optional: Install headers for development
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/pybind11/include
    DESTINATION include/pybind11
)

message(STATUS "Python site-packages: ${Python_SITEARCH}")
install(TARGETS vmtool
    LIBRARY DESTINATION ${Python_SITEARCH}
)