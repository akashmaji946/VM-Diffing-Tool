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
pybind11::dict get_disk_meta_data(const std::string& disk_path, bool verbose = false);

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
                                               const std::string& format, // hex, bits
                                               long long read = -1,
                                               const std::string& stop = "");

// check if a file exists in the guest image
pybind11::dict check_file_exists_in_disk(const std::string& disk_path, const std::string& name);

// list all files from a directory in the guest image
pybind11::dict list_files_in_directory_in_disk(const std::string& disk_path, const std::string& directory, bool detailed);

// list all files in the disk with serial numbers as keys
pybind11::dict list_all_filenames_in_disk(const std::string& disk_path, bool verbose = false);

// list all filenames in a directory with serial numbers as keys
pybind11::dict list_all_filenames_in_directory(const std::string& disk_path, const std::string& directory, bool verbose = false);

// Compare two disk images block by block and return differing block numbers
// Returns a dict with string keys "1", "2", etc. mapping to "Block-N" where N is the block number
// start_block: starting block number (default 0)
// end_block: ending block number (default -1 for last block)
pybind11::dict list_blocks_difference_in_disks(const std::string& disk_path1, 
                                                const std::string& disk_path2, 
                                                size_t block_size = 4096,
                                                int64_t start_block = 0,
                                                int64_t end_block = -1);

// Read a specific block from a disk image and return its contents in the specified format
// Returns a dict with block number as key and formatted data as value
// format: "hex" (uppercase hex bytes separated by spaces) or "bits" (continuous bitstring)
pybind11::dict get_block_data_in_disk(const std::string& disk_path,
                                       uint64_t block_number,
                                       size_t block_size = 4096,
                                       const std::string& format = "hex");

} // namespace vmtool