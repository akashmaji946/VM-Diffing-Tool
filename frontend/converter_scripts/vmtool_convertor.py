# file: VM-Diffing-Tool/frontend/converter_scripts/vmtool_convertor.py
# author: Akash Maji
# date: 2025-10-21
# description: Convert disk images using qemu-img

import argparse
import vmtool
from vmtool import convert

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert disk images using qemu-img")
    parser.add_argument("--src_img", required=True, help="Source disk image path")
    parser.add_argument("--dest_img", required=True, help="Destination disk image path")
    parser.add_argument("--src_format", required=True, help="Source disk image format")
    parser.add_argument("--dest_format", required=True, help="Destination disk image format")
    args = parser.parse_args()
    try:
        out = convert.convert(args.src_img, args.dest_img, args.src_format, args.dest_format)
        print("Disk image converted successfully")
        print(out)
    except Exception as e:
        print(f"Error converting disk image: {e}") 

# USAGE
"""
python vmtool_convertor.py \
    --src_img /path/to/src.img \
    --dest_img /path/to/dest.img \
    --src_format qcow2 \
    --dest_format vdi
"""

# EXAMPLE
"""
python vmtool_convertor.py \
    --src_img /home/akashmaji/Desktop/vm1.qcow2 \
    --dest_img /home/akashmaji/Desktop/vm1c.vdi \
    --src_format qcow2 \
    --dest_format vdi
"""



    
