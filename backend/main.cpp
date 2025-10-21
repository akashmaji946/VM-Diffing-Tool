#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "VMTool.hpp"
#include "../include/Converter.hpp"
#include "../include/vmmanager.hpp"

namespace py = pybind11;

PYBIND11_MODULE(vmtool, m) {
    m.doc() = "VM Tool C++ Backend";

    // Public module version
    m.attr("version") = "0.1";

    // Submodule for libguestfs info; expose a version attribute string
    py::module_ libgfs = m.def_submodule("libguestfs", "libguestfs related utilities");
    // Do NOT call into libguestfs at import time; expose a function instead
    libgfs.def("version", &vmtool::get_guestfs_version, "Return the libguestfs version string");

    // Submodule for disk image conversion via qemu-img
    py::module_ convert = m.def_submodule("convert", "Disk image conversion utilities using qemu-img");
    convert.def("is_qemu_img_available",
                &vmtool::Converter::is_qemu_img_available,
                "Return True if qemu-img is available on PATH");
    convert.def("convert",
                [](const std::string &src_img,
                   const std::string &dest_img,
                   const std::string &src_format,
                   const std::string &dest_format) {
                    auto res = vmtool::Converter::convert(src_img, dest_img, src_format, dest_format);
                    py::dict src, dest, out;
                    src["disk"] = res.src_disk;
                    src["format"] = res.src_format;
                    src["size"] = py::int_(res.src_size_bytes);
                    dest["disk"] = res.dest_disk;
                    dest["format"] = res.dest_format;
                    dest["size"] = py::int_(res.dest_size_bytes);
                    out["src"] = src;
                    out["dest"] = dest;
                    out["converted"] = res.converted;
                    out["time"] = res.time_seconds;
                    return out;
                },
                py::arg("src_img"),
                py::arg("dest_img"),
                py::arg("src_format"),
                py::arg("dest_format"),
                "Convert a disk image from src_format to dest_format using qemu-img and return a dict with src/dest/converted/time.");

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

    m.def("list_all_filenames_in_disk",
          &vmtool::list_all_filenames_in_disk,
          py::arg("disk_path"),
          py::arg("verbose") = false,
          "List all files in the disk with serial numbers as keys. Returns dict with '1', '2', ... as keys and file paths as values, sorted alphabetically.");

    m.def("list_all_filenames_in_directory",
          &vmtool::list_all_filenames_in_directory,
          py::arg("disk_path"),
          py::arg("directory"),
          py::arg("verbose") = false,
          "List all files in a directory recursively with serial numbers as keys. Returns dict with '1', '2', ... as keys and file paths as values, sorted alphabetically.");

    m.def("list_blocks_difference_in_disks",
          &vmtool::list_blocks_difference_in_disks,
          py::arg("disk_path1"),
          py::arg("disk_path2"),
          py::arg("block_size") = 4096,
          py::arg("start_block") = 0,
          py::arg("end_block") = -1,
          "Compare two disk images block by block and return differing block numbers.\n"
          "Returns a dict with keys '1', '2', ... mapping to 'Block-N' where N is the block number.\n"
          "start_block: starting block number (default 0)\n"
          "end_block: ending block number (default -1 for last block)\n"
          "Default block size is 4096 bytes.");

    m.def("get_block_data_in_disk",
          &vmtool::get_block_data_in_disk,
          py::arg("disk_path"),
          py::arg("block_number"),
          py::arg("block_size") = 4096,
          py::arg("format") = "hex",
          "Read a specific block from a disk image and return its contents in the specified format.\n"
          "Returns a dict with block number as key and formatted data as value.\n"
          "format: 'hex' (uppercase hex bytes separated by spaces) or 'bits' (continuous bitstring).\n"
          "Default block size is 4096 bytes.");

    // Attach vmmanager as a submodule so users can: from vmtool import vmmanager
    py::module_ vmman = m.def_submodule("vmmanager", "System VM management utilities (QEMU, VirtualBox, VMware)");
    vmmanager::bind_vmmanager(vmman);
}