#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>
#include <sys/stat.h>

#include "../include/vmmanager.hpp"

namespace py = pybind11;

namespace {

static bool file_exists(const std::string &p) {
    struct stat st{};
    return ::stat(p.c_str(), &st) == 0;
}

static std::string dirname_of(const std::string &path) {
    auto pos = path.find_last_of("/");
    if (pos == std::string::npos) return ".";
    return path.substr(0, pos);
}

static std::string basename_of(const std::string &path) {
    auto pos = path.find_last_of("/");
    if (pos == std::string::npos) return path;
    return path.substr(pos + 1);
}

static std::string strip_ext(const std::string &name) {
    auto pos = name.find_last_of('.')
            ;
    if (pos == std::string::npos) return name;
    return name.substr(0, pos);
}

static std::string to_lower(std::string s) {
    for (auto &c : s) c = (char)tolower(c);
    return s;
}

static std::string sh_quote(const std::string &s) {
    std::string out;
    out.reserve(s.size() + 2);
    out.push_back('"');
    for (char c : s) {
        if (c == '"' || c == '\\') out.push_back('\\');
        out.push_back(c);
    }
    out.push_back('"');
    return out;
}

} // anonymous

namespace vmmanager {

ExecResult exec_capture(const std::string &cmd) {
    std::string full = cmd + " 2>&1";
    FILE *pipe = ::popen(full.c_str(), "r");
    ExecResult res{0, {}};
    if (!pipe) {
        res.exit_code = -1;
        res.output = "Failed to popen";
        return res;
    }
    char buf[4096];
    while (fgets(buf, sizeof(buf), pipe)) {
        res.output.append(buf);
    }
    int rc = ::pclose(pipe);
    if (WIFEXITED(rc)) {
        res.exit_code = WEXITSTATUS(rc);
    } else {
        res.exit_code = rc;
    }
    return res;
}

ExecResult run_qemu_vm(const std::string &disk,
                       int cpus,
                       int memory_mb,
                       const std::string &name,
                       bool use_kvm,
                       bool use_uefi,
                       bool convert_if_needed) {
    // Optional convert .vdi/.vmdk -> .qcow2
    std::string disk_path = disk;
    std::string low = to_lower(disk);
    if (convert_if_needed && (low.rfind(".vdi") == low.size()-4 || low.rfind(".vmdk") == low.size()-5)) {
        std::string dir = dirname_of(disk);
        std::string base = basename_of(disk);
        std::string out = dir + "/" + strip_ext(base) + ".qcow2";
        std::stringstream ss;
        ss << "qemu-img convert -O qcow2 " << sh_quote(disk) << " " << sh_quote(out);
        auto conv = exec_capture(ss.str());
        if (conv.exit_code != 0) return conv;
        disk_path = out;
    }

    std::stringstream cmd;
    cmd << "qemu-system-x86_64 ";
    cmd << "-name " << sh_quote(name.empty() ? basename_of(disk_path) : name) << " ";
    cmd << "-machine type=q35 ";
    if (use_kvm) {
        cmd << "-accel kvm -cpu host ";
    } else {
        cmd << "-accel tcg -cpu qemu64 ";
    }
    cmd << "-smp " << cpus << " -m " << memory_mb << " ";

    if (use_uefi) {
        std::string ovmf_code = "/usr/share/OVMF/OVMF_CODE.fd";
        std::string ovmf_vars = "/usr/share/OVMF/OVMF_VARS.fd";
        if (file_exists(ovmf_code)) {
            cmd << "-drive if=pflash,format=raw,unit=0,readonly=on,file=" << sh_quote(ovmf_code) << " ";
            cmd << "-drive if=pflash,format=raw,unit=1,file=" << sh_quote(ovmf_vars) << ",readonly=off ";
        }
    }

    // format by extension
    std::string fmt = "auto";
    if (low.rfind(".qcow2") == low.size()-6) fmt = "qcow2";
    else if (low.rfind(".vdi") == low.size()-4) fmt = "vdi";
    else if (low.rfind(".vmdk") == low.size()-5) fmt = "vmdk";

    if (fmt == "auto") {
        cmd << "-drive file=" << sh_quote(disk_path) << ",if=virtio,cache=none,aio=threads,discard=unmap ";
    } else {
        cmd << "-drive file=" << sh_quote(disk_path) << ",if=virtio,format=" << fmt << ",cache=none,aio=threads,discard=unmap ";
    }

    // user networking + SSH forward
    cmd << "-device virtio-net-pci,netdev=n0 -netdev user,id=n0,hostfwd=tcp::2222-:22 ";

    // display
    cmd << "-display gtk";

    return exec_capture(cmd.str());
}

ExecResult run_vbox_vm(const std::string &disk,
                       int cpus,
                       int memory_mb,
                       const std::string &name,
                       int vram_mb,
                       const std::string &ostype,
                       const std::string &bridged_if,
                       bool convert_if_needed) {
    std::string low = to_lower(disk);
    std::string attach_disk = disk;

    if (low.rfind(".qcow2") == low.size()-6) {
        if (!convert_if_needed) {
            return {1, "Input is .qcow2. Provide a .vdi/.vmdk or enable convert."};
        }
        std::string out = dirname_of(disk) + "/" + strip_ext(basename_of(disk)) + ".vdi";
        auto conv = exec_capture(std::string("qemu-img convert -O vdi ") + sh_quote(disk) + " " + sh_quote(out));
        if (conv.exit_code != 0) return conv;
        attach_disk = out;
    } else if (!(low.rfind(".vdi") == low.size()-4 || low.rfind(".vmdk") == low.size()-5)) {
        return {1, "Unsupported disk format. Use .vdi/.vmdk (or .qcow2 with convert)."};
    }

    std::string vm_name = name.empty() ? strip_ext(basename_of(attach_disk)) : name;

    std::stringstream cmd;
    cmd << "VBoxManage createvm --name " << sh_quote(vm_name) << " --ostype " << sh_quote(ostype) << " --register && ";
    cmd << "VBoxManage modifyvm " << sh_quote(vm_name)
        << " --memory " << memory_mb
        << " --cpus " << cpus
        << " --vram " << vram_mb
        << " --ioapic on --boot1 disk --boot2 dvd --boot3 none --boot4 none";
    if (!bridged_if.empty()) {
        cmd << " --nic1 bridged --bridgeadapter1 " << sh_quote(bridged_if);
    } else {
        cmd << " --nic1 nat";
    }
    cmd << " && VBoxManage storagectl " << sh_quote(vm_name) << " --name \"SATA Controller\" --add sata --controller IntelAhci";
    cmd << " && VBoxManage storageattach " << sh_quote(vm_name) << " --storagectl \"SATA Controller\" --port 0 --device 0 --type hdd --medium " << sh_quote(attach_disk);
    cmd << " && VBoxManage startvm " << sh_quote(vm_name) << " --type gui";

    return exec_capture(cmd.str());
}

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
                           bool nogui) {
    std::string d = disk;
    std::string low = to_lower(disk);
    if (low.rfind(".vmdk") != low.size()-5) {
        if (!(low.rfind(".vdi") == low.size()-4 || low.rfind(".qcow2") == low.size()-6)) {
            return {1, "Unsupported disk format. Provide .vmdk or enable --convert for .vdi/.qcow2."};
        }
        if (!convert_if_needed) {
            return {1, "Input is not .vmdk. Re-run with convert to generate VMDK."};
        }
        std::string out = dirname_of(disk) + "/" + strip_ext(basename_of(disk)) + ".vmdk";
        auto conv = exec_capture(std::string("qemu-img convert -O vmdk ") + sh_quote(disk) + " " + sh_quote(out));
        if (conv.exit_code != 0) return conv;
        d = out;
    }

    std::string vmx_dir = vm_dir.empty() ? (std::string(std::getenv("HOME") ? std::getenv("HOME") : "") + "/vmware/" + (name.empty() ? strip_ext(basename_of(d)) : name)) : vm_dir;
    std::string vm_name = name.empty() ? strip_ext(basename_of(d)) : name;
    std::string vmx = vmx_dir + "/" + vm_name + ".vmx";

    // create directory
    std::stringstream mk;
    mk << "mkdir -p " << sh_quote(vmx_dir);
    auto mkres = exec_capture(mk.str());
    if (mkres.exit_code != 0) return mkres;

    // write vmx
    std::ofstream ofs(vmx);
    if (!ofs) {
        return {1, std::string("Failed to write ") + vmx};
    }
    ofs << ".encoding = \"UTF-8\"\n";
    ofs << "config.version = \"8\"\n";
    ofs << "virtualHW.version = \"16\"\n";
    ofs << "displayName = \"" << vm_name << "\"\n";
    ofs << "annotation = \"Autogenerated by vmmanager\"\n";
    ofs << "memsize = \"" << memory_mb << "\"\n";
    ofs << "numvcpus = \"" << cpus << "\"\n";
    ofs << "cpuid.coresPerSocket = \"" << cpus << "\"\n";
    ofs << "guestOS = \"" << guest_os << "\"\n";
    ofs << "scsi0.present = \"TRUE\"\n";
    ofs << "scsi0.virtualDev = \"lsilogic\"\n";
    ofs << "scsi0:0.present = \"TRUE\"\n";
    ofs << "scsi0:0.fileName = \"" << d << "\"\n";
    ofs << "svga.vramSize = \"" << (static_cast<long long>(vram_mb) * 1048576LL) << "\"\n";
    if (!no_net) {
        ofs << "ethernet0.present = \"TRUE\"\n";
        ofs << "ethernet0.connectionType = \"nat\"\n";
        ofs << "ethernet0.virtualDev = \"" << (nic_model.empty() ? "e1000" : nic_model) << "\"\n";
        ofs << "ethernet0.addressType = \"generated\"\n";
    }
    ofs << "bios.bootOrder = \"hdd,cdrom\"\n";
    ofs << "tools.syncTime = \"TRUE\"\n";
    ofs.close();

    // start
    std::stringstream start;
    if (std::system("which vmrun > /dev/null 2>&1") == 0) {
        start << "vmrun start " << sh_quote(vmx) << (nogui ? " nogui" : "");
    } else if (std::system("which vmplayer > /dev/null 2>&1") == 0) {
        start << "vmplayer " << sh_quote(vmx) << " &";
    } else {
        return {1, "Neither vmrun nor vmplayer found in PATH"};
    }
    return exec_capture(start.str());
}

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
                                   const std::string &boot_order) {
    std::string low = to_lower(iso_path);
    if (low.rfind(".iso") != low.size()-4) {
        return {1, "--iso must be a .iso file"};
    }
    std::string vdi_path = vdi_dir + "/" + vm_name + ".vdi";

    std::stringstream cmd;
    cmd << "mkdir -p " << sh_quote(vdi_dir) << " && ";
    cmd << "VBoxManage createvm --name " << sh_quote(vm_name) << " --ostype " << sh_quote(ostype) << " --register && ";
    // boot order parsing
    std::string b1="disk", b2="dvd", b3="none", b4="none";
    {
        // naive split by comma
        std::vector<std::string> parts; parts.reserve(4);
        std::string t; for (char c: boot_order) { if (c==',') { if(!t.empty()) { parts.push_back(t); t.clear(); } } else t.push_back(c);} if(!t.empty()) parts.push_back(t);
        if (parts.size() > 0) b1 = parts[0];
        if (parts.size() > 1) b2 = parts[1];
        if (parts.size() > 2) b3 = parts[2];
        if (parts.size() > 3) b4 = parts[3];
    }
    cmd << "VBoxManage modifyvm " << sh_quote(vm_name)
        << " --memory " << memory_mb
        << " --cpus " << cpus
        << " --vram " << vram_mb
        << " --ioapic on --firmware bios"
        << " --boot1 " << sh_quote(b1)
        << " --boot2 " << sh_quote(b2)
        << " --boot3 " << sh_quote(b3)
        << " --boot4 " << sh_quote(b4);
    if (nic_type == "bridged") {
        cmd << " --nic1 bridged --bridgeadapter1 " << sh_quote(bridge_if);
    } else {
        cmd << " --nic1 nat";
    }
    cmd << " && VBoxManage createhd --filename " << sh_quote(vdi_path) << " --size " << (disk_gb * 1024) << " && ";
    cmd << "VBoxManage storagectl " << sh_quote(vm_name) << " --name \"SATA Controller\" --add sata --controller IntelAhci && ";
    cmd << "VBoxManage storageattach " << sh_quote(vm_name) << " --storagectl \"SATA Controller\" --port 0 --device 0 --type hdd --medium " << sh_quote(vdi_path) << " && ";
    cmd << "VBoxManage storageattach " << sh_quote(vm_name) << " --storagectl \"SATA Controller\" --port 1 --device 0 --type dvddrive --medium " << sh_quote(iso_path) << " && ";
    cmd << "VBoxManage startvm " << sh_quote(vm_name) << " --type gui";

    return exec_capture(cmd.str());
}

} // namespace vmmanager

namespace vmmanager {
void bind_vmmanager(py::module_ &m) {
    m.doc() = "VM Manager: pybind11 bridge to system VM tools (QEMU, VirtualBox, VMware)";

    m.def("exec_capture", [](const std::string &cmd){
        auto r = vmmanager::exec_capture(cmd);
        py::dict d; d["exit_code"] = r.exit_code; d["output"] = r.output; return d;
    }, py::arg("cmd"), "Execute a shell command and capture combined stdout/stderr.");

    m.def("run_qemu_vm", [](const std::string &disk, int cpus, int memory_mb, const std::string &name, bool use_kvm, bool use_uefi, bool convert_if_needed){
        auto r = vmmanager::run_qemu_vm(disk, cpus, memory_mb, name, use_kvm, use_uefi, convert_if_needed);
        py::dict d; d["exit_code"] = r.exit_code; d["output"] = r.output; return d;
    }, py::arg("disk"), py::arg("cpus")=2, py::arg("memory_mb")=2048, py::arg("name")="",
       py::arg("use_kvm")=true, py::arg("use_uefi")=false, py::arg("convert_if_needed")=false,
       "Run a disk image with QEMU. Optionally convert vdi/vmdk to qcow2 before running.");

    m.def("run_vbox_vm", [](const std::string &disk, int cpus, int memory_mb, const std::string &name, int vram_mb, const std::string &ostype, const std::string &bridged_if, bool convert_if_needed){
        auto r = vmmanager::run_vbox_vm(disk, cpus, memory_mb, name, vram_mb, ostype, bridged_if, convert_if_needed);
        py::dict d; d["exit_code"] = r.exit_code; d["output"] = r.output; return d;
    }, py::arg("disk"), py::arg("cpus")=2, py::arg("memory_mb")=2048, py::arg("name")="",
       py::arg("vram_mb")=32, py::arg("ostype")="Ubuntu_64", py::arg("bridged_if")="",
       py::arg("convert_if_needed")=false,
       "Run a VirtualBox VM from VDI/VMDK. If disk is qcow2 and convert_if_needed, it will convert to VDI then attach.");

    m.def("run_vmware_vmdk", [](const std::string &disk, int cpus, int memory_mb, const std::string &name, int vram_mb, const std::string &guest_os, const std::string &vm_dir, const std::string &nic_model, bool no_net, bool convert_if_needed, bool nogui){
        auto r = vmmanager::run_vmware_vmdk(disk, cpus, memory_mb, name, vram_mb, guest_os, vm_dir, nic_model, no_net, convert_if_needed, nogui);
        py::dict d; d["exit_code"] = r.exit_code; d["output"] = r.output; return d;
    }, py::arg("disk"), py::arg("cpus")=2, py::arg("memory_mb")=2048, py::arg("name")="",
       py::arg("vram_mb")=32, py::arg("guest_os")="otherlinux-64", py::arg("vm_dir")="",
       py::arg("nic_model")="e1000", py::arg("no_net")=false, py::arg("convert_if_needed")=false, py::arg("nogui")=true,
       "Run a VMDK with VMware (vmrun/vmplayer). If disk is vdi/qcow2 and convert_if_needed, it will convert to VMDK.");

    m.def("create_vbox_vm_from_iso", [](const std::string &iso_path, const std::string &vdi_dir, const std::string &vm_name, const std::string &ostype, int memory_mb, int cpus, int disk_gb, int vram_mb, const std::string &nic_type, const std::string &bridge_if, const std::string &boot_order){
        auto r = vmmanager::create_vbox_vm_from_iso(iso_path, vdi_dir, vm_name, ostype, memory_mb, cpus, disk_gb, vram_mb, nic_type, bridge_if, boot_order);
        py::dict d; d["exit_code"] = r.exit_code; d["output"] = r.output; return d;
    }, py::arg("iso_path"), py::arg("vdi_dir"), py::arg("vm_name"), py::arg("ostype")="Ubuntu_64",
       py::arg("memory_mb")=2048, py::arg("cpus")=2, py::arg("disk_gb")=20, py::arg("vram_mb")=32,
       py::arg("nic_type")="nat", py::arg("bridge_if")="", py::arg("boot_order")="disk,dvd",
       "Create and start a VirtualBox VM from an ISO.");
}
} // namespace vmmanager
