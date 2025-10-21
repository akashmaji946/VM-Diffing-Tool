# Optional conversion for vdi/vmdk -> qcow2 when requested
case "${DISK,,}" in
  *.vdi|*.vmdk)
    if (( DO_CONVERT )); then
      if ! has_cmd qemu-img; then
        err "qemu-img not found. Install qemu-utils to allow --convert."
        exit 1
      fi
      src="$DISK"
      base="$(basename "$src")"
      dir="$(dirname "$src")"
      name_no_ext="${base%.*}"
      out_qcow2="$dir/$name_no_ext.qcow2"
      info "Converting '$src' -> '$out_qcow2' (qcow2)"
      qemu-img convert -O qcow2 "$src" "$out_qcow2"
      DISK="$out_qcow2"
    fi
    ;;
esac
#!/usr/bin/env bash
# Run a disk image (.qcow2/.vdi/.vmdk) with QEMU as a VM
# Usage:
#   ./run_qemu_vm.sh --disk /path/to/disk.qcow2 --cpus 4 --memory 4096 [--name MyVM] [--no-kvm] [--uefi] [--convert]
#
# Notes:
# - Requires qemu-system-x86_64 installed. KVM acceleration is used by default when available.
# - Supports qcow2, vdi, vmdk (auto-selects format based on file extension). Falls back to auto-detect.
# - Optional --convert can transform .vdi/.vmdk to .qcow2 with the same base name next to the source before running.
# - For maximum performance, virtio devices are used by default. Ensure guest has virtio drivers.

set -euo pipefail

# ---------- Defaults ----------
DISK=""
CPUS=2
MEMORY=2048   # MB
NAME=""
USE_KVM=1
USE_UEFI=0
DO_CONVERT=0

# ---------- Helpers ----------
err() { echo "[ERROR] $*" >&2; }
info() { echo "[INFO]  $*"; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

choose_format_by_ext() {
  local f="$1"
  shopt -s nocasematch
  case "$f" in
    *.qcow2) echo qcow2 ;;
    *.vdi)   echo vdi   ;;
    *.vmdk)  echo vmdk  ;;
    *)       echo auto  ;;
  esac
  shopt -u nocasematch
}

kvm_available() {
  # KVM is available if /dev/kvm exists and we can access it
  [[ -e /dev/kvm ]] && [[ -r /dev/kvm ]] && [[ -w /dev/kvm ]]
}

print_usage() {
  cat <<USAGE
Run a disk image with QEMU

Usage:
  $(basename "$0") --disk <path> [--cpus <N>] [--memory <MB>] [--name <NAME>] [--no-kvm] [--uefi] [--convert]

Options:
  --disk, -d     Path to disk image (.qcow2/.vdi/.vmdk) [required]
  --cpus, -c     Number of virtual CPUs (default: ${CPUS})
  --memory, -m   Memory in MB (default: ${MEMORY})
  --name, -n     VM display name (default: derived from disk filename)
  --no-kvm       Disable KVM acceleration even if available
  --uefi         Boot with OVMF UEFI firmware (if available)
  --convert      If input is .vdi/.vmdk, convert to .qcow2 (same name alongside) and use it
  --help, -h     Show this help

Examples:
  $(basename "$0") --disk /vms/debian.qcow2 --cpus 4 --memory 4096
  $(basename "$0") -d /vms/win10.vmdk -c 4 -m 8192 --uefi
USAGE
}

# ---------- Parse args ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --disk|-d) DISK="${2:-}"; shift 2;;
    --cpus|-c) CPUS="${2:-}"; shift 2;;
    --memory|-m) MEMORY="${2:-}"; shift 2;;
    --name|-n) NAME="${2:-}"; shift 2;;
    --no-kvm) USE_KVM=0; shift;;
    --uefi) USE_UEFI=1; shift;;
    --convert) DO_CONVERT=1; shift;;
    --help|-h) print_usage; exit 0;;
    *) err "Unknown argument: $1"; print_usage; exit 1;;
  esac
done

# ---------- Validate ----------
if ! has_cmd qemu-system-x86_64; then
  err "qemu-system-x86_64 not found. Please install QEMU (e.g., sudo apt install qemu-system-x86)."
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

if ! [[ "$CPUS" =~ ^[0-9]+$ ]] || (( CPUS < 1 )); then
  err "--cpus must be a positive integer"
  exit 1
fi

if ! [[ "$MEMORY" =~ ^[0-9]+$ ]] || (( MEMORY < 128 )); then
  err "--memory must be an integer (MB) >= 128"
  exit 1
fi

if [[ -z "$NAME" ]]; then
  NAME="$(basename "$DISK")"
fi

FMT="$(choose_format_by_ext "$DISK")"

# ---------- Acceleration ----------
ACCEL_ARGS=()
CPU_ARGS=("-cpu" "host")
if (( USE_KVM )); then
  if kvm_available; then
    ACCEL_ARGS=("-accel" "kvm")
  else
    info "KVM not available or accessible; running with TCG (software emulation)."
    ACCEL_ARGS=("-accel" "tcg")
    CPU_ARGS=("-cpu" "qemu64")
  fi
else
  ACCEL_ARGS=("-accel" "tcg")
  CPU_ARGS=("-cpu" "qemu64")
fi

# ---------- Firmware (UEFI) ----------
FW_ARGS=()
if (( USE_UEFI )); then
  # Try common OVMF paths; adjust as needed
  OVMF_CODE="/usr/share/OVMF/OVMF_CODE.fd"
  OVMF_VARS="/usr/share/OVMF/OVMF_VARS.fd"
  if [[ -r "$OVMF_CODE" ]]; then
    FW_ARGS=(
      -drive if=pflash,format=raw,unit=0,readonly=on,file="$OVMF_CODE"
      -drive if=pflash,format=raw,unit=1,file="${OVMF_VARS}",readonly=off
    )
  else
    info "OVMF firmware not found at $OVMF_CODE; continuing without UEFI."
  fi
fi

# ---------- Networking ----------
NET_ARGS=(
  -device virtio-net-pci,netdev=n0
  -netdev user,id=n0,hostfwd=tcp::2222-:22
)

# ---------- Storage ----------
# Prefer virtio-blk for performance; fall back to SATA if needed.
if [[ "$FMT" == "auto" ]]; then
  DRIVE_FORMAT_OPT=""
else
  DRIVE_FORMAT_OPT=",format=$FMT"
fi

DRIVE_ARGS=(
  -drive file="$DISK",if=virtio${DRIVE_FORMAT_OPT},cache=none,aio=threads,discard=unmap
)

# ---------- Display ----------
DISPLAY_ARGS=( -display gtk )

# ---------- Assemble QEMU command ----------
CMD=(
  qemu-system-x86_64
  -name "$NAME"
  -machine type=q35
  "${ACCEL_ARGS[@]}"
  "${CPU_ARGS[@]}"
  -smp "$CPUS"
  -m "$MEMORY"
  "${FW_ARGS[@]}"
  "${DRIVE_ARGS[@]}"
  "${NET_ARGS[@]}"
  "${DISPLAY_ARGS[@]}"
)

info "Launching VM: $NAME"
info "Disk: $DISK (format: $FMT)"
info "CPUs: $CPUS, Memory: ${MEMORY}MB"
info "KVM: $([[ ${ACCEL_ARGS[*]} == *kvm* ]] && echo enabled || echo disabled)"

# Exec QEMU
exec "${CMD[@]}"
