#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "VMTool.hpp"

namespace py = pybind11;

PYBIND11_MODULE(vmtool, m) {
    m.doc() = "VM Tool C++ Backend";

    // Public module version
    m.attr("version") = "0.1";

    // Submodule for libguestfs info; expose a version attribute string
    py::module_ libgfs = m.def_submodule("libguestfs", "libguestfs related utilities");
    libgfs.attr("version") = vmtool::get_guestfs_version();

    // Functions
    m.def("get_version", &vmtool::get_guestfs_version,
          "Return the libguestfs version string");

    m.def("list_files_with_metadata",
          &vmtool::list_files_with_metadata,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "List all files in a VM disk image with metadata using libguestfs");

    m.def("write_files_with_metadata",
          &vmtool::write_files_with_metadata,
          py::arg("entries"),
          py::arg("output_file"),
          "Write the entries returned by list_files_with_metadata to a text file in a formatted table");
}