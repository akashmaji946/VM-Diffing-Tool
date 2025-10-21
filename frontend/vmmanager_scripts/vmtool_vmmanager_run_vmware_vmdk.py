#!/usr/bin/env python3
# file: VM-Diffing-Tool/frontend/vmmanager_scripts/vmtool_vmmanager_run_vmware_vmdk.py
# author: Akash Maji
# date: 2025-10-22
# description: Run a VMware VM from a VMDK via vmtool.vmmanager

import argparse
from vmtool import vmmanager
from sys import exit


def main():
    parser = argparse.ArgumentParser(description="Run a VMware VM from a VMDK")
    parser.add_argument("--disk", required=True, help="Path to disk image (.vmdk, or .vdi/.qcow2 with --convert)")
    parser.add_argument("--cpus", type=int, default=2, help="Number of virtual CPUs (default: 2)")
    parser.add_argument("--memory", type=int, default=2048, help="Memory in MB (default: 2048)")
    parser.add_argument("--name", default="", help="VM name (default: derived from disk)")
    parser.add_argument("--vram", type=int, default=32, help="VRAM in MB (default: 32)")
    parser.add_argument("--guestos", default="otherlinux-64", help="VMware guestOS ID (e.g., ubuntu-64, windows10-64)")
    parser.add_argument("--vm-dir", default="", help="Directory for generated .vmx (default: ~/vmware/<name>)")
    parser.add_argument("--nic-model", choices=["e1000","e1000e","vmxnet3"], default="e1000", help="NIC model")
    parser.add_argument("--no-net", action="store_true", help="Do not attach a virtual NIC")
    parser.add_argument("--convert", action="store_true", help="If input is .vdi/.qcow2, convert to .vmdk before running")
    parser.add_argument("--nogui", action="store_true", help="Start with vmrun nogui (if available)")

    args = parser.parse_args()
    try:
        res = vmmanager.run_vmware_vmdk(
            disk=args.disk,
            cpus=args.cpus,
            memory_mb=args.memory,
            name=args.name,
            vram_mb=args.vram,
            guest_os=args.guestos,
            vm_dir=args.vm_dir,
            nic_model=args.nic_model,
            no_net=args.no_net,
            convert_if_needed=args.convert,
            nogui=args.nogui,
        )
        print(res.get("output", ""))
        exit(res.get("exit_code", 1))
    except Exception as e:
        print(f"Error running VMware VM: {e}")
        exit(1)


if __name__ == "__main__":
    main()
