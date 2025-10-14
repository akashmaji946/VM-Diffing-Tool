#include <guestfs.h>
#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

// A simple function to test libguestfs and pybind11 integration
std::string get_guestfs_version() {
    guestfs_h *g = guestfs_create();
    if (g == nullptr) {
        return std::string("Error: Failed to create guestfs handle.");
    }
    char *version = guestfs_version(g);
    std::string result(version);
    free(version);
    guestfs_close(g);
    return result;
}

// This is the binding code that exposes your C++ functions to Python.
// The first argument "vmtool" MUST match the name in your CMakeLists.txt.
PYBIND11_MODULE(vmtool, m) {
    m.doc() = "VM Tool C++ Backend"; // Optional module docstring
    m.def("get_version", &get_guestfs_version, "A function that returns the libguestfs version");
}