# Convertor Script Reference

This document explains how to use the disk image converter script shipped with VM-Diffing-Tool.

- Script path: `frontend/converter_scripts/vmtool_convertor.py`
- vmt command: `convertor`
- Backend tool: `qemu-img`

## Supported formats

Depends on your `qemu-img` installation (commonly: `qcow2`, `raw`, `vdi`, `vmdk`).

## Usage (direct Python)

```bash
python3 frontend/converter_scripts/vmtool_convertor.py \
  --src_img /path/to/src.qcow2 \
  --dest_img /path/to/dest.vdi \
  --src_format qcow2 \
  --dest_format vdi
```

## Usage (via vmt CLI)

```bash
vmt -c convertor \
  --src_img /path/to/src.qcow2 \
  --dest_img /path/to/dest.vdi \
  --src_format qcow2 \
  --dest_format vdi
```

## Notes

- Ensure the destination directory is writable.
- Inside Docker, mount the destination path as read-write. Example when running the app container:
  - `-v "$PWD/.vmtool-data:/app/data:rw"` and use `/app/data/...` as your `--dest_img`.
- Conversions can be large and time-consuming; ensure you have enough disk space.
