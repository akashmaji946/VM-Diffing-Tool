#pragma once

#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace vmtool {

// Returns the libguestfs version string
std::string get_guestfs_version();

// List all files in a VM disk image with metadata using libguestfs
pybind11::list list_files_with_metadata(const std::string& disk_path, bool verbose = false);

// Write the entries returned by list_files_with_metadata to a text file in a formatted table
void write_files_with_metadata(pybind11::list entries, const std::string& output_file);

// Returns a dict with summary stats: files, directories, users, sizes, per-user breakdown
pybind11::dict get_meta_data(const std::string& disk_path, bool verbose = false);

// Returns a dict with numbered string keys mapping to {"Size","Permission","Last Modified","Name"}
pybind11::dict get_files_with_metadata_json(const std::string& disk_path, bool verbose = false);

} // namespace vmtool