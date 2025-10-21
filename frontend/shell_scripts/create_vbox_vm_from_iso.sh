#!/usr/bin/env bash
# Create and start a VirtualBox VM from an ISO (non-interactive)
#
# Usage:
#   ./create_vbox_vm_from_iso.sh \
#     --iso /path/to/os.iso \
#     --vdi-dir /path/to/vdis \
#     --vm-name MyVM \
#     --ostype Ubuntu_64 \
#     --memory 2048 \
#     --cpus 2 \
#     --disk-gb 20 \
#     --vram 32 \
#     [--nic nat|bridged] \
#     [--bridge-if <iface>] \
#     [--boot-order disk,dvd]
#
# Notes:
# - Requires VirtualBox (VBoxManage) in PATH.
# - This script ONLY accepts .iso files for --iso.

set -euo pipefail

# ---------- Defaults ----------
ISO_PATH=""
VDI_DIR=""
VM_NAME=""
OSTYPE="Ubuntu_64"
MEM_MB=2048
CPUS=2
DISK_GB=20
VRAM_MB=32
NIC_TYPE="nat"        # nat | bridged
BRIDGED_IF=""         # host interface name for bridged
BOOT_ORDER="disk,dvd" # comma-separated

# ---------- Helpers ----------
err() { echo "[ERROR] $*" >&2; }
info() { echo "[INFO]  $*"; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

print_usage() {
  cat <<USAGE
Create and start a VirtualBox VM from an ISO (non-interactive)

Usage:
  $(basename "$0") --iso <file.iso> --vdi-dir <dir> --vm-name <name> \
    [--ostype <VBoxOSType>] [--memory <MB>] [--cpus <N>] [--disk-gb <GB>] [--vram <MB>] \
    [--nic nat|bridged] [--bridge-if <iface>] [--boot-order disk,dvd]

Required:
  --iso         Path to installer ISO (.iso only)
  --vdi-dir     Directory to create the VDI disk in (will be created)
  --vm-name     Name for the new VM

Optional:
  --ostype      VirtualBox OS type (default: ${OSTYPE})
  --memory      RAM in MB (default: ${MEM_MB})
  --cpus        vCPUs (default: ${CPUS})
  --disk-gb     Disk size in GB (default: ${DISK_GB})
  --vram        Video RAM in MB (default: ${VRAM_MB})
  --nic         nat | bridged (default: ${NIC_TYPE})
  --bridge-if   Host interface name for bridged (required if --nic bridged)
  --boot-order  Comma-separated order (default: ${BOOT_ORDER})

Examples:
  $(basename "$0") --iso ~/isos/ubuntu.iso --vdi-dir ~/vdis --vm-name ubuntu-test --ostype Ubuntu_64
USAGE
}

# ---------- Parse args ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO_PATH="${2:-}"; shift 2;;
    --vdi-dir) VDI_DIR="${2:-}"; shift 2;;
    --vm-name) VM_NAME="${2:-}"; shift 2;;
    --ostype) OSTYPE="${2:-}"; shift 2;;
    --memory) MEM_MB="${2:-}"; shift 2;;
    --cpus) CPUS="${2:-}"; shift 2;;
    --disk-gb) DISK_GB="${2:-}"; shift 2;;
    --vram) VRAM_MB="${2:-}"; shift 2;;
    --nic) NIC_TYPE="${2:-}"; shift 2;;
    --bridge-if) BRIDGED_IF="${2:-}"; shift 2;;
    --boot-order) BOOT_ORDER="${2:-}"; shift 2;;
    --help|-h) print_usage; exit 0;;
    *) err "Unknown argument: $1"; print_usage; exit 1;;
  esac
done

# ---------- Validate ----------
if ! has_cmd VBoxManage; then
  err "VBoxManage not found. Please install VirtualBox and ensure VBoxManage is in PATH."
  exit 1
fi

if [[ -z "$ISO_PATH" || -z "$VDI_DIR" || -z "$VM_NAME" ]]; then
  err "--iso, --vdi-dir, and --vm-name are required"
  print_usage
  exit 1
fi

if [[ ! -f "$ISO_PATH" ]]; then
  err "ISO not found: $ISO_PATH"
  exit 1
fi

case "${ISO_PATH,,}" in
  *.iso) :;;
  *) err "--iso must point to a .iso file"; exit 1;;

esac

mkdir -p "$VDI_DIR"

if ! [[ "$MEM_MB" =~ ^[0-9]+$ ]] || (( MEM_MB < 256 )); then
  err "--memory must be an integer (MB) >= 256"; exit 1
fi
if ! [[ "$CPUS" =~ ^[0-9]+$ ]] || (( CPUS < 1 )); then
  err "--cpus must be a positive integer"; exit 1
fi
if ! [[ "$DISK_GB" =~ ^[0-9]+$ ]] || (( DISK_GB < 1 )); then
  err "--disk-gb must be a positive integer (GB)"; exit 1
fi
if ! [[ "$VRAM_MB" =~ ^[0-9]+$ ]] || (( VRAM_MB < 1 )); then
  err "--vram must be a positive integer (MB)"; exit 1
fi

case "$NIC_TYPE" in
  nat) :;;
  bridged) if [[ -z "$BRIDGED_IF" ]]; then err "--bridge-if is required when --nic bridged"; exit 1; fi ;;
  *) err "--nic must be one of: nat, bridged"; exit 1;;
 esac

# Disk path
VDI_PATH="$VDI_DIR/$VM_NAME.vdi"

# ---------- Create VM ----------
info "Creating VM '$VM_NAME' (OS type: $OSTYPE)"
VBoxManage createvm --name "$VM_NAME" --ostype "$OSTYPE" --register

# ---------- Configure VM ----------
IFS=',' read -r BOOT1 BOOT2 BOOT3 BOOT4 <<< "$BOOT_ORDER"
info "Configuring CPUs=$CPUS, Memory=${MEM_MB}MB, VRAM=${VRAM_MB}MB, NIC=$NIC_TYPE"
VBoxManage modifyvm "$VM_NAME" \
  --memory "$MEM_MB" \
  --cpus "$CPUS" \
  --vram "$VRAM_MB" \
  --ioapic on \
  --firmware bios \
  --boot1 "${BOOT1:-disk}" --boot2 "${BOOT2:-dvd}" --boot3 "${BOOT3:-none}" --boot4 "${BOOT4:-none}"

if [[ "$NIC_TYPE" == "bridged" ]]; then
  VBoxManage modifyvm "$VM_NAME" --nic1 bridged --bridgeadapter1 "$BRIDGED_IF"
else
  VBoxManage modifyvm "$VM_NAME" --nic1 nat
fi

# ---------- Create & attach disk ----------
info "Creating VDI disk at '$VDI_PATH' (${DISK_GB}GB)"
VBoxManage createhd --filename "$VDI_PATH" --size $((DISK_GB * 1024))

VBoxManage storagectl "$VM_NAME" --name "SATA Controller" --add sata --controller IntelAhci

VBoxManage storageattach "$VM_NAME" \
  --storagectl "SATA Controller" \
  --port 0 --device 0 --type hdd --medium "$VDI_PATH"

VBoxManage storageattach "$VM_NAME" \
  --storagectl "SATA Controller" \
  --port 1 --device 0 --type dvddrive --medium "$ISO_PATH"

# ---------- Launch VM ----------
info "Starting VM '$VM_NAME'..."
VBoxManage startvm "$VM_NAME" --type gui

info "VM '$VM_NAME' created and started successfully!"
