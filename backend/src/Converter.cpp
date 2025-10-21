#include "../include/Converter.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

#if __has_include(<filesystem>)
  #include <filesystem>
  namespace fs = std::filesystem;
#else
  #include <experimental/filesystem>
  namespace fs = std::experimental::filesystem;
#endif

namespace vmtool {

std::string Converter::to_lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::tolower(c); });
    return s;
}

bool Converter::is_supported_format(const std::string &fmt) {
    static const std::vector<std::string> supported = {"vmdk", "vdi", "qcow2"};
    for (const auto &f : supported) {
        if (fmt == f) return true;
    }
    return false;
}

bool Converter::is_qemu_img_available() {
    // Try running qemu-img --version and check exit status.
    int rc = std::system("qemu-img --version > /dev/null 2>&1");
    if (rc == -1) return false;
    // On POSIX, exit code is in high bits; simple check for zero is fine for our usage via system().
    return rc == 0;
}

ConversionResult Converter::convert(const std::string &src_img,
                                    const std::string &dest_img,
                                    const std::string &src_format,
                                    const std::string &dest_format) {
    ConversionResult result;
    result.src_disk = src_img;
    result.dest_disk = dest_img;

    if (!is_qemu_img_available()) {
        throw std::runtime_error("qemu-img is not installed or not found in PATH. Please install qemu-utils/qemu-img.");
    }

    if (!fs::exists(src_img)) {
        throw std::runtime_error("Source image does not exist: " + src_img);
    }

    std::string sfmt = to_lower(src_format);
    std::string dfmt = to_lower(dest_format);
    result.src_format = sfmt;
    result.dest_format = dfmt;

    if (!is_supported_format(sfmt)) {
        throw std::runtime_error("Unsupported source format: " + src_format + ". Supported: vmdk, vdi, qcow2");
    }
    if (!is_supported_format(dfmt)) {
        throw std::runtime_error("Unsupported destination format: " + dest_format + ". Supported: vmdk, vdi, qcow2");
    }

    // Pre-capture source size
    try {
        result.src_size_bytes = fs::file_size(src_img);
    } catch (...) {
        result.src_size_bytes = 0ULL;
    }

    // Build the qemu-img convert command
    std::string cmd = "qemu-img convert -f " + sfmt + " -O " + dfmt +
                      " '" + src_img + "' '" + dest_img + "'";

    auto start = std::chrono::steady_clock::now();
    int rc = std::system(cmd.c_str());
    auto end = std::chrono::steady_clock::now();
    result.time_seconds = std::chrono::duration<double>(end - start).count();

    if (rc == 0 && fs::exists(dest_img)) {
        result.converted = true;
        try {
            result.dest_size_bytes = fs::file_size(dest_img);
        } catch (...) {
            result.dest_size_bytes = 0ULL;
        }
    } else {
        result.converted = false;
        result.dest_size_bytes = 0ULL;
    }

    return result;
}

} // namespace vmtool
