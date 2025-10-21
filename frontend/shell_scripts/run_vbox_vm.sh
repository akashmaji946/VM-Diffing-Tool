#!/usr/bin/env bash
# Run a VirtualBox VM from an existing disk image (.vdi/.vmdk)
#
# Usage:
#   ./run_vbox_vm.sh --disk /path/to/disk.vdi --cpus 2 --memory 2048 [--name MyVBVM] [--vram 32] [--ostype Ubuntu_64] [--bridged <if>] [--convert]
#
# Requirements:
#   - VirtualBox installed and VBoxManage available in PATH
#   - Disk image must be VDI or VMDK (use --convert to convert qcow2 -> VDI)
#
# Notes:
#   - This script creates a new VM (unless one with the same name exists),
#     attaches the provided disk, applies CPU/RAM settings, and starts it.
#   - Network defaults to NAT; use --bridged <iface> to run in bridged mode.

set -euo pipefail

# ---------- Defaults ----------
DISK=""
CPUS=2
MEMORY=2048     # MB
VRAM=32         # MB
NAME=""
OSTYPE="Ubuntu_64"   # VBox OS type, e.g., Ubuntu_64, Debian_64, Windows10_64
BRIDGED_IF=""        # If non-empty, use bridged networking on this interface
DO_CONVERT=0          # If input is qcow2 and this is set, convert to VDI first

# ---------- Helpers ----------
err() { echo "[ERROR] $*" >&2; }
info() { echo "[INFO]  $*"; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

vm_exists() {
  local name="$1"
  VBoxManage list vms | awk -F '"' '{print $2}' | grep -Fxq "$name"
}

print_usage() {
  cat <<USAGE
Run a VirtualBox VM from a VDI/VMDK disk

Usage:
  $(basename "$0") --disk <path> [--cpus <N>] [--memory <MB>] [--name <NAME>] [--vram <MB>] [--ostype <OSTYPE>] [--bridged <iface>] [--convert]

Options:
  --disk, -d     Path to disk image (.vdi/.vmdk) [required; use --convert if input is .qcow2]
  --cpus, -c     Number of virtual CPUs (default: ${CPUS})
  --memory, -m   Memory in MB (default: ${MEMORY})
  --name, -n     VM name (default: derived from disk filename)
  --vram         Video RAM in MB (default: ${VRAM})
  --ostype       VirtualBox OS type (default: ${OSTYPE})
  --bridged      Use bridged networking on given host interface (default: NAT)
  --convert      If input is .qcow2, convert to .vdi (same name alongside) and use it
  --help, -h     Show this help

Examples:
  $(basename "$0") --disk /vms/alpine.vdi --cpus 2 --memory 2048 --name alpine
  $(basename "$0") -d /vms/win10.vmdk -c 4 -m 8192 --ostype Windows10_64 --vram 64
USAGE
}

# ---------- Parse args ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --disk|-d) DISK="${2:-}"; shift 2;;
    --cpus|-c) CPUS="${2:-}"; shift 2;;
    --memory|-m) MEMORY="${2:-}"; shift 2;;
    --name|-n) NAME="${2:-}"; shift 2;;
    --vram) VRAM="${2:-}"; shift 2;;
    --ostype) OSTYPE="${2:-}"; shift 2;;
    --bridged) BRIDGED_IF="${2:-}"; shift 2;;
    --convert) DO_CONVERT=1; shift;;
    --help|-h) print_usage; exit 0;;
    *) err "Unknown argument: $1"; print_usage; exit 1;;
  esac
done

# ---------- Validate ----------
if ! has_cmd VBoxManage; then
  err "VBoxManage not found. Please install VirtualBox and ensure VBoxManage is in PATH."
  exit 1
fi

if [[ -z "$DISK" ]]; then
  err "--disk is required"
  print_usage
  exit 1
fi

if [[ ! -f "$DISK" ]]; then
  err "Disk not found: $DISK"
  exit 1
fi

# Validate extension and handle optional conversion for qcow2
ATTACH_DISK="$DISK"
case "${DISK,,}" in
  *.vdi|*.vmdk)
    : ;; # ok
  *.qcow2)
    if (( DO_CONVERT == 0 )); then
      err "Input is .qcow2. Provide a .vdi/.vmdk or re-run with --convert to convert to VDI automatically."
      exit 1
    fi
    if ! has_cmd qemu-img; then
      err "qemu-img not found. Install qemu-utils to allow --convert."
      exit 1
    fi
    src="$DISK"
    base="$(basename "$src")"
    dir="$(dirname "$src")"
    name_no_ext="${base%.*}"
    out_vdi="$dir/$name_no_ext.vdi"
    info "Converting '$src' -> '$out_vdi' (VDI)"
    qemu-img convert -O vdi "$src" "$out_vdi"
    ATTACH_DISK="$out_vdi"
    ;;
  *)
    err "Unsupported disk format. Please provide a .vdi or .vmdk file, or use --convert to convert .qcow2."
    exit 1
    ;;
esac

if ! [[ "$CPUS" =~ ^[0-9]+$ ]] || (( CPUS < 1 )); then
  err "--cpus must be a positive integer"
  exit 1
fi

if ! [[ "$MEMORY" =~ ^[0-9]+$ ]] || (( MEMORY < 128 )); then
  err "--memory must be an integer (MB) >= 128"
  exit 1
fi

if ! [[ "$VRAM" =~ ^[0-9]+$ ]] || (( VRAM < 1 )); then
  err "--vram must be a positive integer (MB)"
  exit 1
fi

if [[ -z "$NAME" ]]; then
  base="$(basename "$DISK")"
  NAME="${base%.*}"
fi

if vm_exists "$NAME"; then
  err "A VM named '$NAME' already exists. Please choose a different --name."
  exit 1
fi

# No auto-conversion here; ATTACH_DISK is already handled above

# ---------- Create VM ----------
info "Creating VM '$NAME' (OS type: $OSTYPE)"
VBoxManage createvm --name "$NAME" --ostype "$OSTYPE" --register

# ---------- Configure VM ----------
info "Configuring CPUs=$CPUS, Memory=${MEMORY}MB, VRAM=${VRAM}MB, IOAPIC=on"
VBoxManage modifyvm "$NAME" \
  --memory "$MEMORY" \
  --cpus "$CPUS" \
  --vram "$VRAM" \
  --ioapic on \
  --boot1 disk --boot2 dvd --boot3 none --boot4 none

# Networking
if [[ -n "$BRIDGED_IF" ]]; then
  info "Enabling bridged networking on interface '$BRIDGED_IF'"
  VBoxManage modifyvm "$NAME" --nic1 bridged --bridgeadapter1 "$BRIDGED_IF"
else
  info "Using NAT networking"
  VBoxManage modifyvm "$NAME" --nic1 nat
fi

# ---------- Attach storage ----------
info "Attaching disk: $ATTACH_DISK"
# Create SATA controller and attach disk on port 0
VBoxManage storagectl "$NAME" --name "SATA Controller" --add sata --controller IntelAhci
VBoxManage storageattach "$NAME" \
  --storagectl "SATA Controller" \
  --port 0 --device 0 --type hdd --medium "$ATTACH_DISK"

# ---------- Launch VM ----------
info "Starting VM '$NAME'..."
VBoxManage startvm "$NAME" --type gui

info "VM '$NAME' launched successfully."
