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
    // Do NOT call into libguestfs at import time; expose a function instead
    libgfs.def("version", &vmtool::get_guestfs_version, "Return the libguestfs version string");

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

    m.def("get_meta_data",
          &vmtool::get_meta_data,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "Return aggregated metadata for the disk image: counts (files/dirs), total sizes, and per-user breakdown");

    m.def("get_files_with_metadata_json",
          &vmtool::get_files_with_metadata_json,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "Return file listing as a dict keyed by '1','2',... with fields: Size, Permission, Last Modified, Name");
}