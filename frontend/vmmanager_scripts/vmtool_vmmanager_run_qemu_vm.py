# file: VM-Diffing-Tool/frontend/vmmanager_scripts/vmtool_vmmanager_run_qemu_vm.py
# author: Akash Maji
# date: 2025-10-22
#!/usr/bin/env python3
# description: Run a QEMU VM via vmtool.vmmanager

import argparse
from vmtool import vmmanager
import sys

def main():
    parser = argparse.ArgumentParser(description="Run a QEMU VM from a disk image")
    parser.add_argument("--disk", required=True, help="Path to disk image (.qcow2/.vdi/.vmdk)")
    parser.add_argument("--cpus", type=int, default=2, help="Number of virtual CPUs (default: 2)")
    parser.add_argument("--memory", type=int, default=2048, help="Memory in MB (default: 2048)")
    parser.add_argument("--name", default="", help="VM display name (default: basename of disk)")
    parser.add_argument("--no-kvm", action="store_true", help="Disable KVM acceleration")
    parser.add_argument("--uefi", action="store_true", help="Boot with OVMF UEFI if available")
    parser.add_argument("--convert", action="store_true", help="If input is .vdi/.vmdk, convert to .qcow2 before running")

    args = parser.parse_args()
    try:
        res = vmmanager.run_qemu_vm(
            disk=args.disk,
            cpus=args.cpus,
            memory_mb=args.memory,
            name=args.name,
            use_kvm=not args.no_kvm,
            use_uefi=args.uefi,
            convert_if_needed=args.convert,
        )
        code = res.get("exit_code", 1)
        print(res.get("output", ""))
        raise SystemExit(code)
    except Exception as e:
        print(f"Error running VM: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

# USAGE
"""
python vmtool_vmmanager_run_qemu_vm.py \
--disk /path/to/disk.qcow2 \
--cpus 2 \
--memory 2048 \
--name my-vm \
--vram 32 \
--ostype Ubuntu_64 \
--bridged-if eth0 \
--convert
"""

# EXAMPLE
"""
python vmtool_vmmanager_run_qemu_vm.py \
--disk /home/akashmaji/Desktop/vm1.qcow2 \
--cpus 2 \
--memory 2048 \
--name vm1 \
--vram 32 \
--ostype Ubuntu_64 \
--bridged-if eth0 \
--convert
"""
