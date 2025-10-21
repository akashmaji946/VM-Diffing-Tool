#!/usr/bin/env python3
# file: VM-Diffing-Tool/frontend/vmmanager_scripts/vmtool_vmmanager_run_vbox_vm.py
# author: Akash Maji
# date: 2025-10-22
# description: Run a VirtualBox VM via vmtool.vmmanager

import argparse
from vmtool import vmmanager


def main():
    parser = argparse.ArgumentParser(description="Run a VirtualBox VM from a disk image")
    parser.add_argument("--disk", required=True, help="Path to disk image (.vdi/.vmdk or .qcow2 with --convert)")
    parser.add_argument("--cpus", type=int, default=2, help="Number of virtual CPUs (default: 2)")
    parser.add_argument("--memory", type=int, default=2048, help="Memory in MB (default: 2048)")
    parser.add_argument("--name", default="", help="VM name (default: derived from disk)")
    parser.add_argument("--vram", type=int, default=32, help="VRAM in MB (default: 32)")
    parser.add_argument("--ostype", default="Ubuntu_64", help="VirtualBox OS type (e.g., Ubuntu_64, Debian_64, Windows10_64)")
    parser.add_argument("--bridged-if", default="", help="Use bridged networking on the given host interface (default: NAT)")
    parser.add_argument("--convert", action="store_true", help="If input is .qcow2, convert to .vdi before running")

    args = parser.parse_args()
    try:
        res = vmmanager.run_vbox_vm(
            disk=args.disk,
            cpus=args.cpus,
            memory_mb=args.memory,
            name=args.name,
            vram_mb=args.vram,
            ostype=args.ostype,
            bridged_if=args.bridged_if,
            convert_if_needed=args.convert,
        )
        print(res.get("output", ""))
        exit(res.get("exit_code", 1))
    except Exception as e:
        print(f"Error running VirtualBox VM: {e}")
        exit(1)


if __name__ == "__main__":
    main()
