#pragma once

#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace vmtool {

std::string get_guestfs_version();

pybind11::list list_files_with_metadata(const std::string& disk_path, bool verbose = false);

void write_files_with_metadata(pybind11::list entries, const std::string& output_file);

} // namespace vmtool