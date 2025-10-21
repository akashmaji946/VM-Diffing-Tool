# file: VM-Diffing-Tool/frontend/vmmanager_scripts/vmtool_vmmanager_create_vbox_from_iso.py
# author: Akash Maji
# date: 2025-10-21
# description: Create a VirtualBox VM from an ISO file

import argparse
from vmtool import vmmanager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a VirtualBox VM from an ISO file")
    parser.add_argument("--iso", required=True, help="Path to ISO file")
    parser.add_argument("--vdi-dir", required=True, help="Path to directory where VDI will be created")
    parser.add_argument("--vm-name", required=True, help="Name of the VM")

    parser.add_argument("--ostype", required=False, default="Ubuntu_64", help="VirtualBox OS type (e.g., Ubuntu_64, Debian_64, Windows10_64)")
    parser.add_argument("--memory", required=False, type=int, default=2048, help="Memory in MB")
    parser.add_argument("--cpus", required=False, type=int, default=2, help="Number of CPUs")
    parser.add_argument("--disk-gb", required=False, type=int, default=20, help="Disk size in GB")
    parser.add_argument("--vram", required=False, type=int, default=32, help="VRAM in MB")

    parser.add_argument("--nic", required=False, choices=["nat","bridged"], default="nat", help="NIC type for VirtualBox")
    parser.add_argument("--boot-order", required=False, default="disk,dvd", help="Boot order (comma-separated, e.g., disk,dvd)")
    parser.add_argument("--bridge-if", required=False, default="", help="Bridge interface (required if --nic bridged)")
    
    args = parser.parse_args()
    # Validate bridged interface requirement
    if args.nic == "bridged" and not args.bridge_if:
        raise SystemExit("--bridge-if is required when --nic bridged")

    try:
        res = vmmanager.create_vbox_vm_from_iso(
            iso_path=args.iso,
            vdi_dir=args.vdi_dir,
            vm_name=args.vm_name,
            ostype=args.ostype,
            memory_mb=args.memory,
            cpus=args.cpus,
            disk_gb=args.disk_gb,
            vram_mb=args.vram,
            nic_type=args.nic,
            bridge_if=args.bridge_if,
            boot_order=args.boot_order,
        )
        if res.get("exit_code", 1) == 0:
            print("VM created successfully")
        else:
            print("Error creating VM:")
            print(res.get("output", ""))
    except Exception as e:
        print(f"Error creating VM: {e}")


# USAGE
"""
python vmtool_vmmanager_create_vbox_from_iso.py \
--iso /path/to/iso.iso \
--vdi-dir /path/to/vdi-dir \
--vm-name my-vm \
--ostype Ubuntu_64 \
--memory 2048 \
--cpus 2 \
--disk-gb 20 \
--vram 32 \
--nic nat \
--boot-order disk,dvd \
--bridge-if eth0 \
--convert \
--nogui
"""

# EXAMPLE
"""
python vmtool_vmmanager_create_vbox_from_iso.py \
--iso /home/akashmaji/Desktop/ubuntu.iso \
--vdi-dir /home/akashmaji/Desktop/vdi-dir \
--vm-name vm1 \
--ostype Ubuntu_64 \
--memory 2048 \
--cpus 2 \
--disk-gb 20 \
--vram 32 \
--nic nat \
--boot-order disk,dvd \
--bridge-if eth0 \
--convert \
--nogui
"""
