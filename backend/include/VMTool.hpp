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

// Read contents of a file inside the guest image.
// If binary is true, returns Python bytes; otherwise returns Python str (UTF-8 best effort).
// If read < 0, reads all; otherwise reads up to 'read' bytes.
// If stop is non-empty, reading stops at the first occurrence of 'stop' (inclusive=false).
pybind11::object get_file_contents_in_disk(const std::string& disk_path,
                                           const std::string& name,
                                           bool binary = false,
                                           long long read = -1,
                                           const std::string& stop = "");

// Read contents and return a formatted string based on format:
//  - format == "hex": returns uppercase hex bytes separated by spaces, e.g. "00 0F 1A 2B"
//  - format == "bits": returns a continuous bitstring, e.g. "00000001..."
// The read and stop parameters behave the same as in get_file_contents_in_disk.
pybind11::str get_file_contents_in_disk_format(const std::string& disk_path,
                                               const std::string& name,
                                               const std::string& format,
                                               long long read = -1,
                                               const std::string& stop = "");

} // namespace vmtool