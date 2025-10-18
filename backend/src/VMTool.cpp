#include "../include/VMTool.hpp"
#include <guestfs.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <ctime>
#include <cstdlib>
#include <stdexcept>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <vector>
#include <unordered_map>
#include <map>
#include <sys/stat.h>
#include <unistd.h>
#include <cstdio>
#include <bitset>

namespace py = pybind11;

namespace vmtool {

// Portable helper to free a NULL-terminated list of C strings
static void free_string_list(char **list) {
    if (!list) return;
    for (size_t i = 0; list[i] != nullptr; ++i) {
        std::free(list[i]);
    }
    std::free(list);
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

// A simple function to test libguestfs and integration
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

// List files with metadata from a VM disk image using libguestfs.
// Returns a Python list of dicts: {size:int|str, perms:str, mtime:str, path:str}
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

        // get mountpoints: returns [mountpoint, device, mountpoint, device, ..., NULL]
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;

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

// Summary metadata for a QCOW2 disk: counts and sizes, including per-user
py::dict get_disk_meta_data(const std::string &disk_path, bool verbose) {
    py::dict out;

    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }

    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }

    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect and mount
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }

    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;
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
            (void) guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str());
        }
    }

    // Parse /etc/passwd for users
    std::unordered_map<long long, std::string> uid_to_user;
    try {
        char *passwd = guestfs_cat(g, "/etc/passwd");
        if (passwd) {
            std::string content(passwd);
            free(passwd);
            std::istringstream iss(content);
            std::string line;
            while (std::getline(iss, line)) {
                if (line.empty() || line[0] == '#') continue;
                // Format: name:x:uid:gid:gecos:home:shell
                std::vector<std::string> fields;
                std::string f;
                std::istringstream ls(line);
                while (std::getline(ls, f, ':')) fields.push_back(f);
                if (fields.size() >= 3) {
                    try {
                        long long uid = std::stoll(fields[2]);
                        uid_to_user[uid] = fields[0];
                    } catch (...) {}
                }
            }
        }
    } catch (...) {
        // ignore parsing errors
    }

    // Parse /etc/group for groups
    std::unordered_map<long long, std::string> gid_to_group;
    try {
        char *group = guestfs_cat(g, "/etc/group");
        if (group) {
            std::string content(group);
            free(group);
            std::istringstream iss(content);
            std::string line;
            while (std::getline(iss, line)) {
                if (line.empty() || line[0] == '#') continue;
                // Format: name:x:gid:members
                std::vector<std::string> fields;
                std::string f;
                std::istringstream ls(line);
                while (std::getline(ls, f, ':')) fields.push_back(f);
                if (fields.size() >= 3) {
                    try {
                        long long gid = std::stoll(fields[2]);
                        gid_to_group[gid] = fields[0];
                    } catch (...) {}
                }
            }
        }
    } catch (...) {
        // ignore parsing errors
    }

    // Traverse filesystem
    char **paths = guestfs_find(g, "/");
    if (!paths) {
        guestfs_umount_all(g);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("guestfs_find failed");
    }

    long long files_count = 0;
    long long dirs_count = 0;
    long long total_file_bytes = 0;
    long long total_dir_bytes = 0;
    std::unordered_map<long long, long long> per_uid_bytes;
    std::unordered_map<long long, long long> per_uid_files;
    std::unordered_map<long long, long long> per_uid_dirs;
    std::unordered_map<long long, long long> per_gid_bytes;
    std::unordered_map<long long, long long> per_gid_files;
    std::unordered_map<long long, long long> per_gid_dirs;

    for (size_t k = 0; paths[k] != nullptr; ++k) {
        std::string path_component = paths[k];
        std::string full_path = (path_component == ".") ? std::string("/") : std::string("/") + path_component;

        struct guestfs_statns *st = guestfs_statns(g, full_path.c_str());
        if (!st) continue;

        uint32_t mode = static_cast<uint32_t>(st->st_mode);
        bool is_dir = (S_ISDIR(mode));
        bool is_reg = (S_ISREG(mode));
        long long uid = static_cast<long long>(st->st_uid);
        long long gid = static_cast<long long>(st->st_gid);
        if (is_dir) {
            dirs_count++;
            long long dsz = static_cast<long long>(st->st_size);
            if (dsz > 0) total_dir_bytes += dsz;
            per_uid_dirs[uid] += 1;
            per_gid_dirs[gid] += 1;
        } else if (is_reg) {
            files_count++;
            long long sz = static_cast<long long>(st->st_size);
            if (sz > 0) total_file_bytes += sz;
            per_uid_bytes[uid] += std::max<long long>(0, sz);
            per_uid_files[uid] += 1;
            per_gid_bytes[gid] += std::max<long long>(0, sz);
            per_gid_files[gid] += 1;
        }
        guestfs_free_statns(st);

        if (verbose && (k % 5000 == 0)) {
            py::print("Processed:", k);
        }
    }

    // Prepare per-user list: include all users from /etc/passwd even if zero; sort by bytes desc
    std::vector<std::pair<long long, long long>> order_users;
    order_users.reserve(per_uid_bytes.size() + uid_to_user.size());
    // Seed with all known users to ensure presence
    for (const auto &kv : uid_to_user) {
        long long uid = kv.first;
        long long bytes = per_uid_bytes.count(uid) ? per_uid_bytes[uid] : 0;
        order_users.emplace_back(uid, bytes);
    }
    // Add any extra uids seen in ownership but not in passwd
    for (const auto &kv : per_uid_bytes) {
        if (!uid_to_user.count(kv.first)) order_users.emplace_back(kv.first, kv.second);
    }
    std::sort(order_users.begin(), order_users.end(), [](auto &a, auto &b){ return a.second > b.second; });

    py::list per_user_list;
    for (const auto &kv : order_users) {
        long long uid = kv.first;
        long long bytes = kv.second;
        long long nfiles = per_uid_files.count(uid) ? per_uid_files[uid] : 0;
        long long ndirs  = per_uid_dirs.count(uid) ? per_uid_dirs[uid] : 0;
        py::dict row;
        row["uid"] = py::int_(uid);
        row["user"] = py::str(uid_to_user.count(uid) ? uid_to_user[uid] : std::string("uid_") + std::to_string(uid));
        row["files"] = py::int_(nfiles);
        row["dirs"]  = py::int_(ndirs);
        row["bytes"] = py::int_(bytes);
        per_user_list.append(row);
    }

    // Prepare per-group list: include all groups from /etc/group even if zero; sort by bytes desc
    std::vector<std::pair<long long, long long>> order_groups;
    order_groups.reserve(per_gid_bytes.size() + gid_to_group.size());
    for (const auto &kv : gid_to_group) {
        long long gid = kv.first;
        long long bytes = per_gid_bytes.count(gid) ? per_gid_bytes[gid] : 0;
        order_groups.emplace_back(gid, bytes);
    }
    for (const auto &kv : per_gid_bytes) {
        if (!gid_to_group.count(kv.first)) order_groups.emplace_back(kv.first, kv.second);
    }
    std::sort(order_groups.begin(), order_groups.end(), [](auto &a, auto &b){ return a.second > b.second; });

    py::list per_group_list;
    for (const auto &kv : order_groups) {
        long long gid = kv.first;
        long long bytes = kv.second;
        long long nfiles = per_gid_files.count(gid) ? per_gid_files[gid] : 0;
        long long ndirs  = per_gid_dirs.count(gid) ? per_gid_dirs[gid] : 0;
        py::dict row;
        row["gid"] = py::int_(gid);
        row["group"] = py::str(gid_to_group.count(gid) ? gid_to_group[gid] : std::string("gid_") + std::to_string(gid));
        row["files"] = py::int_(nfiles);
        row["dirs"]  = py::int_(ndirs);
        row["bytes"] = py::int_(bytes);
        per_group_list.append(row);
    }

    out["files_count"] = py::int_(files_count);
    out["dirs_count"] = py::int_(dirs_count);
    out["total_file_bytes"] = py::int_(total_file_bytes);
    out["total_dir_bytes"] = py::int_(total_dir_bytes);
    out["total_bytes"] = py::int_(total_file_bytes + total_dir_bytes);
    out["users_total"] = py::int_(static_cast<long long>(uid_to_user.size()));
    out["users_with_files"] = py::int_(static_cast<long long>(per_uid_files.size()));
    out["per_user"] = per_user_list;
    out["groups_total"] = py::int_(static_cast<long long>(gid_to_group.size()));
    out["groups_with_files"] = py::int_(static_cast<long long>(per_gid_files.size()));
    out["per_group"] = per_group_list;

    free_string_list(paths);
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);

    if (verbose) {
        py::print("Files:", files_count, "Dirs:", dirs_count, "Total bytes:", total_file_bytes);
    }

    return out;
}


py::dict get_files_with_metadata_json(const std::string& disk_path, bool verbose) {
    py::list entries = list_files_with_metadata(disk_path, verbose);
    py::dict out;
    const ssize_t n = py::len(entries);
    for (ssize_t i = 0; i < n; ++i) {
        py::dict d = entries[i].cast<py::dict>();

        // Extract fields if present
        py::object size = d.contains(py::str("size")) ? d[py::str("size")] : py::str("-");
        py::object perms = d.contains(py::str("perms")) ? d[py::str("perms")] : py::str("-");
        py::object mtime = d.contains(py::str("mtime")) ? d[py::str("mtime")] : py::str("-");
        py::object path  = d.contains(py::str("path"))  ? d[py::str("path")]  : py::str("-");

        py::dict row;
        row[py::str("Size")] = size;
        row[py::str("Permission")] = perms;
        row[py::str("Last Modified")] = mtime;
        row[py::str("Name")] = path;

        std::string key = std::to_string(static_cast<long long>(i + 1));
        out[py::str(key)] = row;
    }

    return out;
}

// Read file contents from inside the guest image. Uses guestfs_cat to read the file,
// then applies optional stop delimiter and byte limit.
py::object get_file_contents_in_disk(const std::string &disk_path,
                                     const std::string &name,
                                     bool binary,
                                     long long read,
                                     const std::string &stop) {
    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }

    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }
    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect and mount
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }
    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;
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
            (void) guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str());
        }
    }

    // Ensure path is absolute in guest
    std::string guest_path = name;
    if (guest_path.empty() || guest_path[0] != '/') {
        // Interpret as absolute for safety
        guest_path = std::string("/") + guest_path;
    }

    // Download the file to a secure temporary path to preserve exact bytes
    char tmp_template[] = "/tmp/vmtXXXXXX";
    int tfd = mkstemp(tmp_template);
    if (tfd >= 0) close(tfd);
    std::string host_tmp = std::string(tmp_template);

    if (guestfs_download(g, guest_path.c_str(), host_tmp.c_str()) == -1) {
        guestfs_umount_all(g);
        guestfs_shutdown(g);
        guestfs_close(g);
        std::remove(host_tmp.c_str());
        throw std::runtime_error(std::string("Failed to download file: ") + guest_path);
    }

    // Read bytes from temp file
    std::ifstream ifs(host_tmp, std::ios::binary);
    if (!ifs) {
        guestfs_umount_all(g);
        guestfs_shutdown(g);
        guestfs_close(g);
        std::remove(host_tmp.c_str());
        throw std::runtime_error(std::string("Failed to open temp file: ") + host_tmp);
    }

    std::vector<char> data;
    if (read >= 0) {
        data.resize(static_cast<size_t>(read));
        ifs.read(data.data(), static_cast<std::streamsize>(data.size()));
        data.resize(static_cast<size_t>(ifs.gcount()));
    } else {
        // read all
        ifs.seekg(0, std::ios::end);
        std::streamsize sz = ifs.tellg();
        ifs.seekg(0, std::ios::beg);
        if (sz > 0) {
            data.resize(static_cast<size_t>(sz));
            ifs.read(data.data(), sz);
        }
    }
    ifs.close();

    // Cleanup guest and temp
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);
    std::remove(host_tmp.c_str());

    // Apply stop delimiter if provided (search in bytes)
    if (!stop.empty() && !data.empty()) {
        const std::string needle = stop;
        auto it = std::search(data.begin(), data.end(), needle.begin(), needle.end());
        if (it != data.end()) {
            data.resize(static_cast<size_t>(it - data.begin()));
        }
    }

    // If both stop and read were provided, enforce read limit after stop trim
    if (read >= 0 && data.size() > static_cast<size_t>(read)) {
        data.resize(static_cast<size_t>(read));
    }

    if (binary) {
        return py::bytes(data.data(), data.size());
    } else {
        std::string s(data.begin(), data.end());
        return py::str(s);
    }
}

py::str get_file_contents_in_disk_format(const std::string &disk_path,
                                         const std::string &name,
                                         const std::string &format,
                                         long long read,
                                         const std::string &stop) {
    // Always fetch raw bytes so we preserve NULs and exact values
    py::object contents = get_file_contents_in_disk(disk_path, name, /*binary=*/true, read, stop);
    // Convert py::bytes to std::string (std::string preserves NULs and length)
    std::string buf = contents.cast<std::string>();

    if (format == "hex") {
        // Uppercase spaced hex: "00 0F 1A ..."
        static const char *hexmap = "0123456789ABCDEF";
        if (buf.empty()) return py::str("");
        std::string out;
        out.reserve(buf.size() * 3 - 1);
        for (size_t i = 0; i < buf.size(); ++i) {
            unsigned char b = static_cast<unsigned char>(buf[i]);
            out.push_back(hexmap[(b >> 4) & 0xF]);
            out.push_back(hexmap[b & 0xF]);
            if (i + 1 < buf.size()) out.push_back(' ');
        }
        return py::str(out);
    } else if (format == "bits") {
        // Continuous bitstring: 8 chars per byte
        if (buf.empty()) return py::str("");
        std::string out;
        out.reserve(buf.size() * 8);
        for (size_t i = 0; i < buf.size(); ++i) {
            unsigned char b = static_cast<unsigned char>(buf[i]);
            std::bitset<8> bs(b);
            out += bs.to_string();
        }
        return py::str(out);
    } else {
        throw std::runtime_error("Invalid format. Supported formats are 'hex' and 'bits'.");
    }
}

// check if a file exists in the guest image
pybind11::dict check_file_exists_in_disk(const std::string &disk_path, const std::string &name) {
    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }

    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }
    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect and mount
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }
    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;
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
            (void) guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str());
        }
    }

    // Ensure path is absolute in guest
    std::string guest_path = name;
    if (guest_path.empty() || guest_path[0] != '/') {
        // Interpret as absolute for safety
        guest_path = std::string("/") + guest_path;
    }

    // Check if path exists first
    bool exists = guestfs_exists(g, guest_path.c_str());

    bool dir = false;
    bool file = false;
    bool link = false;
    bool socket = false;
    bool chardev = false;
    bool blockdev = false;
    bool fifo = false;
    bool unknown = false;

    long long owner_uid = -1;
    long long group_gid = -1;
    std::string permissions = "-";
    long long size_val = -1;
    std::string mtime_str = "-";

    if (exists) {
        struct guestfs_statns *st = guestfs_statns(g, guest_path.c_str());
        if (st) {
            uint32_t mode = static_cast<uint32_t>(st->st_mode);
            dir = S_ISDIR(mode);
            file = S_ISREG(mode);
            link = S_ISLNK(mode);
            socket = S_ISSOCK(mode);
            chardev = S_ISCHR(mode);
            blockdev = S_ISBLK(mode);
            fifo = S_ISFIFO(mode);
            unknown = !(dir || file || link || socket || chardev || blockdev || fifo);

            owner_uid = static_cast<long long>(st->st_uid);
            group_gid = static_cast<long long>(st->st_gid);
            permissions = perms_string(static_cast<uint32_t>(mode & 0777));
            size_val = static_cast<long long>(st->st_size);
            mtime_str = format_time(static_cast<std::time_t>(st->st_mtime_sec));

            guestfs_free_statns(st);
        } else {
            // If stat fails despite existence, mark as unknown
            unknown = true;
        }
    }

    // Cleanup guest
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);

    // Build dictionary result
    pybind11::dict out;
    out[pybind11::str("exists")] = pybind11::bool_(exists);
    out[pybind11::str("full_path")] = pybind11::str(guest_path);
    out[pybind11::str("dir")] = pybind11::bool_(dir);
    out[pybind11::str("file")] = pybind11::bool_(file);
    out[pybind11::str("link")] = pybind11::bool_(link);
    out[pybind11::str("socket")] = pybind11::bool_(socket);
    out[pybind11::str("chardev")] = pybind11::bool_(chardev);
    out[pybind11::str("blockdev")] = pybind11::bool_(blockdev);
    out[pybind11::str("fifo")] = pybind11::bool_(fifo);
    out[pybind11::str("unknown")] = pybind11::bool_(unknown);


    // owner/group numeric IDs
    out[pybind11::str("owner")] = pybind11::int_(owner_uid);
    out[pybind11::str("group")] = pybind11::int_(group_gid);
    out[pybind11::str("permissions")] = pybind11::str(permissions);
    if (size_val >= 0) {
        out[pybind11::str("size")] = pybind11::int_(size_val);
    } else {
        out[pybind11::str("size")] = pybind11::str("-");
    }
    out[pybind11::str("mtime")] = pybind11::str(mtime_str);

    return out;
}

pybind11::dict list_files_in_directory_in_disk(const std::string& disk_path, const std::string& directory, bool detailed = false) {
    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }
    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }
    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect and mount
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }   
    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;
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
            (void) guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str());
        }
    }

    // Ensure path is absolute in guest but don't include last /
    std::string guest_path = directory;
    if (guest_path.empty() || guest_path[0] != '/') {
        // Interpret as absolute for safety
        guest_path = std::string("/") + guest_path;
    }
    if (guest_path.back() == '/') {
        guest_path.pop_back();
    }

    // List files in directory
    char **files = guestfs_ls(g, guest_path.c_str());
    if (!files) {
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("guestfs_ls failed");
    }
    
    // Cleanup guest
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);
    
    // Build dictionary result
    pybind11::dict out;
    for (size_t i = 0; files[i] != nullptr; ++i) {
        if (detailed) {
            // check_file_exists_in_disk
            pybind11::dict file_info = check_file_exists_in_disk(disk_path, guest_path + "/" + files[i]);
            out[pybind11::str(files[i])] = file_info;
        }else{
            out[pybind11::str(files[i])] = pybind11::str(files[i]);
        }
    }
    free_string_list(files);
    return out;
}

pybind11::dict list_all_filenames_in_disk(const std::string& disk_path, bool verbose) {
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

    // For each root, get mountpoints and mount read-only
    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];

        // get mountpoints: returns [mountpoint, device, mountpoint, device, ..., NULL]
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;

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

    // Collect all file paths in a vector
    std::vector<std::string> file_paths;
    for (size_t k = 0; paths[k] != nullptr; ++k) {
        std::string path_component = paths[k];
        std::string full_path = (path_component == ".") ? std::string("/") : std::string("/") + path_component;
        file_paths.push_back(full_path);
    }

    free_string_list(paths);
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);

    // Sort the file paths alphabetically
    std::sort(file_paths.begin(), file_paths.end());

    // Build dictionary with serial numbers as keys
    pybind11::dict out;
    for (size_t i = 0; i < file_paths.size(); ++i) {
        std::string key = std::to_string(i + 1);
        out[py::str(key)] = py::str(file_paths[i]);

        if (verbose && (i % 5000 == 0)) {
            py::print("Processed:", i + 1, "files");
        }
    }

    return out;
}

pybind11::dict list_all_filenames_in_directory(const std::string& disk_path, const std::string& directory, bool verbose) {
    guestfs_h *g = guestfs_create();
    if (!g) {
        throw std::runtime_error("Failed to create guestfs handle");
    }

    if (guestfs_add_drive_ro(g, disk_path.c_str()) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_add_drive_ro failed");
    }

    if (guestfs_launch(g) == -1) {
        guestfs_close(g);
        throw std::runtime_error("guestfs_launch failed");
    }

    // Inspect and mount
    char **roots = guestfs_inspect_os(g);
    if (!roots || !roots[0]) {
        if (roots) free_string_list(roots);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("No OS found in image");
    }

    for (size_t i = 0; roots[i] != nullptr; ++i) {
        const char *root = roots[i];
        char **mpdev = guestfs_inspect_get_mountpoints(g, root);
        if (!mpdev) continue;
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
            (void) guestfs_mount_ro(g, p.device.c_str(), p.mountpoint.c_str());
        }
    }

    // Ensure path is absolute in guest
    std::string guest_path = directory;
    if (guest_path.empty() || guest_path[0] != '/') {
        guest_path = std::string("/") + guest_path;
    }
    if (!guest_path.empty() && guest_path.back() == '/') {
        guest_path.pop_back();
    }

    // Use guestfs_find to recursively list all files in directory
    char **paths = guestfs_find(g, guest_path.c_str());
    if (!paths) {
        guestfs_umount_all(g);
        guestfs_shutdown(g);
        guestfs_close(g);
        throw std::runtime_error("guestfs_find failed for directory: " + guest_path);
    }

    // Collect all file paths in a vector
    std::vector<std::string> file_paths;
    for (size_t k = 0; paths[k] != nullptr; ++k) {
        std::string path_component = paths[k];
        std::string full_path = (path_component == ".") ? guest_path : guest_path + "/" + path_component;
        file_paths.push_back(full_path);
    }

    free_string_list(paths);
    guestfs_umount_all(g);
    guestfs_shutdown(g);
    guestfs_close(g);

    // Sort the file paths alphabetically
    std::sort(file_paths.begin(), file_paths.end());

    // Build dictionary with serial numbers as keys
    pybind11::dict out;
    for (size_t i = 0; i < file_paths.size(); ++i) {
        std::string key = std::to_string(i + 1);
        out[py::str(key)] = py::str(file_paths[i]);

        if (verbose && (i % 1000 == 0)) {
            py::print("Processed:", i + 1, "files");
        }
    }

    return out;
}

} // namespace vmtool