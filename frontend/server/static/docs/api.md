# CLI API

- This page documents the command-line tools (`vmt`) that wrap the native `vmtool` backend.
- They live under `frontend/` and use `argparse` for options.
- Tool `vmt` is a wrapper for `vmtool` and provides a more user-friendly CLI interface.
- It uses `frontend/vmtool_scripts` for the actual functionality.
- Many operations require elevated privileges due to libguestfs—run with `sudo` if you encounter permission issues.
- You can either use `vmt` or `frontend/vmtool_scripts/<script_name>.py` files directly.

Prerequisites
- Python 3.10+ and the native extension `vmtool` built and importable
- libguestfs installed (and `/dev/kvm` available for best performance)

Conventions
- Replace paths with your absolute disk image path, e.g. `/home/you/vm.qcow2`
- Add `--verbose` on supported commands to print progress/details

## vmt setup
Install vmt using pip
```bash
# go to root of the repository
cd .....


# create virtual environment
python3 -m venv .vm
source .vm/bin/activate

# install requirements
pip install -r requirements.txt

# go to frontend
cd frontend

# install vmt
pip3 install -e .

```
Use `vmt` tool:
```bash
vmt --help
vmt list
vmt -c <command> -h
```


### vmtool_list_all_filenames_in_disk.py
- Description: List all files in a VM disk image
- Options:
  - `--disk <path>` (required) qcow2/raw image
  - `--json <file>` optional output file
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_list_all_filenames_in_disk.py \
  --disk /path/to/disk.qcow2 \
  --json files.json
```

### vmtool_list_all_files_in_disk.py
- Description: List all files with metadata (size, perms, mtime)
- Options:
  - `--file <path>` (required) image path
  - `--out <file>` (required) write human-readable table
  - `--verbose` also print to console
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_list_all_files_in_disk.py \
  --file /path/to/disk.qcow2 \
  --out listing.txt \
  --verbose
```

### vmtool_get_all_files_in_disk_json.py
- Description: Get full file listing as JSON (numbered keys)
- Options:
  - `--disk <path>` (required)
  - `--json <file>` optional output file (stdout if omitted)
  - `--verbose`
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_get_all_files_in_disk_json.py \
  --disk /path/to/disk.qcow2 \
  --json files.json \
  --verbose
```

### vmtool_get_disk_meta_data.py
- Description: Aggregated disk metadata (totals, per-user, per-group)
- Options:
  - `--disk <path>` (required)
  - `--json <file>` save JSON
  - `--out <file>` save human-readable text report
  - `--verbose` print summary if no outputs provided
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_get_disk_meta_data.py \
  --disk /path/to/disk.qcow2 \
  --json meta.json \
  --out meta.txt \
  --verbose
```

### vmtool_check_file_exists_in_disk.py
- Description: Check if a specific file exists in the guest
- Options:
  - `--disk <path>` (required)
  - `--name <guest_path>` (required)
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_check_file_exists_in_disk.py \
  --disk /path/to/disk.qcow2 \
  --name /etc/hosts
```

### vmtool_get_file_contents_in_disk.py
- Description: Read a file (text or binary) from inside the guest
- Options:
  - `--disk <path>` (required)
  - `--name <guest_path>` (required)
  - `--binary` output raw bytes
  - `--read <N>` bytes to read (-1 all)
  - `--stop <delimiter>` stop before delimiter
  - `--out <file>` optional output path
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_get_file_contents_in_disk.py \
  --disk /path/to/disk.qcow2 \
  --name /bin/bash \
  --binary \
  --out bash.bin
```

### vmtool_get_file_contents_in_disk_format.py
- Description: Read a file and return formatted output
- Options:
  - `--disk <path>` (required)
  - `--name <guest_path>` (required)
  - `--format {hex|bits}` (required)
  - `--read <N>` bytes (-1 all)
  - `--stop <delimiter>`
  - `--out <file>` write text output
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_get_file_contents_in_disk_format.py \
  --disk /path/to/disk.qcow2 \
  --name /bin/bash \
  --format hex \
  --out bash_hex.txt
```

### vmtool_get_block_data_in_disk.py
- Description: Read a specific block and print hex/bits view; can save JSON
- Options:
  - `--disk <path>` (required)
  - `--block <N>` (required)
  - `--block-size <N>` default 4096
  - `--format {hex|bits}` default hex
  - `--json <file>` save JSON result
  - `--verbose`
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_get_block_data_in_disk.py \
  --disk /path/to/disk.qcow2 \
  --block 12 \
  --block-size 4096 \
  --format hex \
  --json block_12.json \
  --verbose
```

### vmtool_list_blocks_difference_in_disks.py
- Description: Compare two images block-by-block and list differing blocks
- Options:
  - `--disk1 <path>` (required)
  - `--disk2 <path>` (required)
  - `--block-size <N>` default 4096
  - `--start <N>` default 0
  - `--end <N>` default -1 (last)
  - `--json <file>` save JSON result
  - `--verbose`
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_list_blocks_difference_in_disks.py \
  --disk1 /path/to/disk1.qcow2 \
  --disk2 /path/to/disk2.qcow2 \
  --block-size 4096 \
  --start 0 \
  --end 1000 \
  --json diff.json \
  --verbose
```

### vmtool_list_files_in_directory_in_disk.py
- Description: List all files within a guest directory
- Options:
  - `--disk <path>` (required)
  - `--directory <guest_dir>` (required)
  - `--detailed` include detailed info
- Example:
```bash
sudo python3 frontend/vmtool_scripts/vmtool_list_files_in_directory_in_disk.py \
  --disk /path/to/disk.qcow2 \
  --directory /etc \
  --detailed
