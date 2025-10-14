#include <guestfs.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <sstream>
#include <vector>
#include <algorithm>
#include <ctime>
#include <cstdlib>
#include <stdexcept>
#include <fstream>
#include <iomanip>

namespace py = pybind11;

// Portable helper to free a NULL-terminated list of C strings
static void free_string_list(char **list) {
    if (!list) return;
    for (size_t i = 0; list[i] != nullptr; ++i) {
        std::free(list[i]);
    }
    std::free(list);
}

// Write entries to a file in a formatted table. Expects entries as produced by list_files_with_metadata.
void write_files_with_metadata(py::list entries, const std::string &output_file) {
    std::ofstream ofs(output_file);
    if (!ofs) {
        throw std::runtime_error("Failed to open output file: " + output_file);
    }

    ofs << std::right << std::setw(10) << "Size" << ' '
        << std::setw(10) << "Permission" << ' '
        << std::setw(20) << "Last Modified" << ' '
        << std::setw(20) << "Name" << '\n';
    ofs << std::string(60, '=') << '\n';

    const ssize_t n = py::len(entries);
    for (ssize_t i = 0; i < n; ++i) {
        py::dict d = entries[i].cast<py::dict>();
        std::string size_str = py::str(d[py::str("size")]);
        std::string perms    = py::str(d[py::str("perms")]);
        std::string mtime    = py::str(d[py::str("mtime")]);
        std::string path     = py::str(d[py::str("path")]);

        ofs << std::right << std::setw(10) << size_str << ' '
            << std::setw(10) << perms << ' '
            << std::setw(20) << mtime << ' ' << path << '\n';
    }
}
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

// Convert POSIX mode bits to rwxrwxrwx string (user, group, other)
static std::string perms_string(uint32_t mode) {
    std::string out;
    out.reserve(9);
    const uint32_t flags[9] = {
        0400, 0200, 0100, // user r,w,x
        0040, 0020, 0010, // group r,w,x
        0004, 0002, 0001  // other r,w,x
    };
    const char chars[9] = {'r','w','x','r','w','x','r','w','x'};
    for (int i = 0; i < 9; ++i) {
        out.push_back((mode & flags[i]) ? chars[i] : '-');
    }
    return out;
}

// Helper to format time_t to YYYY-mm-dd HH:MM:SS
static std::string format_time(std::time_t t) {
    if (t <= 0) return std::string("-");
    char buf[32] = {0};
    std::tm tmv;
    // Match Python's datetime.fromtimestamp() which uses local time
    if (!localtime_r(&t, &tmv)) return std::string("-");
    if (std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tmv) == 0) return std::string("-");
    return std::string(buf);
}

// List files with metadata from a VM disk image using libguestfs.
// Returns a Python list of dictionaries: {size:int|str, perms:str, mtime:str, path:str}
py::list list_files_with_metadata(const std::string &disk_path, bool verbose) {
    py::list results;

    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }

    // Add drive read-only and launch
    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }

    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect OSes
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }

    // For each root, get mountpoints and mount read-only.
    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];

        // get mountpoints: returns an array of strings [mountpoint, device, mountpoint, device, ..., NULL]
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;

        // collect pairs and sort by mountpoint length ascending
        struct MP { std::string mountpoint; std::string device; };
        std::vector<MP> mps;
        for (size_t j = 0; mpdev[j] && mpdev[j+1]; j += 2) {
            mps.push_back(MP{mpdev[j], mpdev[j+1]});
        }
        free_string_list(mpdev);

        std::sort(mps.begin(), mps.end(), [](const MP &a, const MP &b){
            return a.mountpoint.size() < b.mountpoint.size();
        });

        for (const auto &p : mps) {
            // Mount read-only
            if (guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str()) == -1) {
                // continue attempting other mounts
                continue;
            }
        }
    }

    // Now find all paths
    char **paths = guestfs_find(g, "/");
    if (!paths) {
        guestfs_umount_all(g);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("guestfs_find failed");
    }

    for (size_t k = 0; paths[k] != nullptr; ++k) {
        std::string path_component = paths[k];
        std::string full_path = (path_component == ".") ? std::string("/") : std::string("/") + path_component;

        // Stat each file
        struct guestfs_statns *st = guestfs_statns(g, full_path.c_str());
        long long size_val = -1;
        std::string perm_str = "-";
        std::string mtime_str = "-";

        if (st) {
            size_val = static_cast<long long>(st->st_size);
            perm_str = perms_string(static_cast<uint32_t>(st->st_mode & 0777));
            mtime_str = format_time(static_cast<std::time_t>(st->st_mtime_sec));
            guestfs_free_statns(st);
        }

        py::dict row;
        if (size_val >= 0) {
            row["size"] = py::int_(size_val);
        } else {
            row["size"] = py::str("-");
        }
        row["perms"] = py::str(perm_str);
        row["mtime"] = py::str(mtime_str);
        row["path"] = py::str(full_path);

        if (verbose) {
            // Print a line similar to the Python script
            std::ostringstream line;
            line << (size_val >= 0 ? std::to_string(size_val) : std::string("-"));
            line << " " << perm_str << " " << mtime_str << " " << full_path;
            py::print(line.str());
        }

        results.append(row);
    }

    free_string_list(paths);
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);

    return results;
}

// This is the binding code that exposes your C++ functions to Python.
// The first argument "vmtool" MUST match the name in your CMakeLists.txt.
PYBIND11_MODULE(vmtool, m) {
    m.doc() = "VM Tool C++ Backend"; // Optional module docstring
    m.def("get_version", &get_guestfs_version, "A function that returns the libguestfs version");
    m.def(
        "list_files_with_metadata",
        &list_files_with_metadata,
        py::arg("disk_path"),
        py::arg("verbose") = false,
        "List all files in a VM disk image with metadata using libguestfs"
    );
    m.def(
        "write_files_with_metadata",
        &write_files_with_metadata,
        py::arg("entries"),
        py::arg("output_file"),
        "Write the entries returned by list_files_with_metadata to a text file in a formatted table"
    );
}