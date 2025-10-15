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

    m.def("get_disk_meta_data",
          &vmtool::get_disk_meta_data,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "Return aggregated metadata for the disk image: counts (files/dirs), total sizes, and per-user breakdown");

    m.def("get_files_with_metadata_json",
          &vmtool::get_files_with_metadata_json,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "Return file listing as a dict keyed by '1','2',... with fields: Size, Permission, Last Modified, Name");

    m.def("get_file_contents_in_disk",
          &vmtool::get_file_contents_in_disk,
          py::arg("disk_path"),
          py::arg("name"),
          py::arg("binary") = false,
          py::arg("read") = -1,
          py::arg("stop") = "",
          "Read contents of a file inside the guest. If binary is true returns bytes, else str.\n"
          "read=-1 reads all bytes, otherwise reads up to N bytes. If stop is non-empty, reading\n"
          "stops at the first occurrence of 'stop' (exclusive).");

    m.def("get_file_contents_in_disk_format",
          &vmtool::get_file_contents_in_disk_format,
          py::arg("disk_path"),
          py::arg("name"),
          py::arg("format"),
          py::arg("read") = -1,
          py::arg("stop") = "",
          "Read contents and return formatted output. format: 'hex' (uppercase spaced hex) or 'bits' (bitstring).\n"
          "read/stop behave like get_file_contents_in_disk.");

    m.def("check_file_exists_in_disk",    
          &vmtool::check_file_exists_in_disk,
          py::arg("disk_path"),
          py::arg("name"),
          "Check if a file exists in the guest image.");    

    m.def("list_files_in_directory_in_disk",    
          &vmtool::list_files_in_directory_in_disk,
          py::arg("disk_path"),
          py::arg("directory"),
          py::arg("detailed") = false,
          "List all files in a directory in the guest image.");    
}