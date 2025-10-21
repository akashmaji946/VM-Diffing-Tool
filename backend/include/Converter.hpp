#pragma once

#include <string>

namespace vmtool {

struct ConversionResult {
    std::string src_disk;
    std::string src_format;
    unsigned long long src_size_bytes = 0ULL;

    std::string dest_disk;
    std::string dest_format;
    unsigned long long dest_size_bytes = 0ULL;

    bool converted = false;
    double time_seconds = 0.0;
};

class Converter {
public:
    // Supported formats: vmdk, vdi, qcow2 (lowercase)
    // Throws std::runtime_error on any error. Returns ConversionResult with timings and sizes.
    static ConversionResult convert(const std::string &src_img,
                                    const std::string &dest_img,
                                    const std::string &src_format,
                                    const std::string &dest_format);

    // Returns true if qemu-img is available in PATH.
    static bool is_qemu_img_available();

private:
    static std::string to_lower(std::string s);
    static bool is_supported_format(const std::string &fmt);
};

} // namespace vmtool
