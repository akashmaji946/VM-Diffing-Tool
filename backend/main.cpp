#include <guestfs.h>
#include <pybind11/pybind11.h>
#include <string>
#include <sstream>

namespace py = pybind11;

// A simple function to test libguestfs and pybind11 integration
std::string get_guestfs_version() {
    guestfs_h *g = guestfs_create();
    if (g == nullptr) {
        return std::string("Error: Failed to create guestfs handle.");
    }
    struct guestfs_version *v = guestfs_version(g);
    if (v == nullptr) {
        guestfs_close(g);
        return std::string("Error: Failed to get libguestfs version.");
    }
    std::ostringstream oss;
    oss << v->major << "." << v->minor << "." << v->release;
    if (v->extra && v->extra[0] != '\0') {
        oss << v->extra;
    }
    std::string result = oss.str();
    guestfs_free_version(v);
    guestfs_close(g);
    return result;
}

// This is the binding code that exposes your C++ functions to Python.
// The first argument "vmtool" MUST match the name in your CMakeLists.txt.
PYBIND11_MODULE(vmtool, m) {
    m.doc() = "VM Tool C++ Backend"; // Optional module docstring
    m.def("get_version", &get_guestfs_version, "A function that returns the libguestfs version");
}