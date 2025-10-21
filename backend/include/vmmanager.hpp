#pragma once

#include <string>

namespace vmmanager {

// A tiny result struct representing a command invocation
struct ExecResult {
    int exit_code;
    std::string output; // combined stdout/stderr
};

// Execute a shell command via /bin/bash -c and capture combined stdout+stderr
ExecResult exec_capture(const std::string &cmd);

// QEMU: run a disk image
ExecResult run_qemu_vm(const std::string &disk,
                       int cpus,
                       int memory_mb,
                       const std::string &name,
                       bool use_kvm,
                       bool use_uefi,
                       bool convert_if_needed);

// VirtualBox: run a VM from an existing VDI/VMDK (optionally convert qcow2 -> vdi)
ExecResult run_vbox_vm(const std::string &disk,
                       int cpus,
                       int memory_mb,
                       const std::string &name,
                       int vram_mb,
                       const std::string &ostype,
                       const std::string &bridged_if,
                       bool convert_if_needed);

// VMware: run from VMDK (optionally convert qcow2/vdi -> vmdk)
ExecResult run_vmware_vmdk(const std::string &disk,
                           int cpus,
                           int memory_mb,
                           const std::string &name,
                           int vram_mb,
                           const std::string &guest_os,
                           const std::string &vm_dir,
                           const std::string &nic_model,
                           bool no_net,
                           bool convert_if_needed,
                           bool nogui);

// VirtualBox: create a VM from ISO (non-interactive)
ExecResult create_vbox_vm_from_iso(const std::string &iso_path,
                                   const std::string &vdi_dir,
                                   const std::string &vm_name,
                                   const std::string &ostype,
                                   int memory_mb,
                                   int cpus,
                                   int disk_gb,
                                   int vram_mb,
                                   const std::string &nic_type,
                                   const std::string &bridge_if,
                                   const std::string &boot_order);

} // namespace vmmanager

// Forward declare pybind11 module to avoid including pybind headers here
namespace pybind11 { class module_; }

namespace vmmanager {
// Bind all vmmanager functions into the given submodule
void bind_vmmanager(pybind11::module_ &m);
}
