#!/usr/bin/env bash
# ================================================================
#  analyze_vm_state.sh
#  Automatically extract and compare process list from a VM dump
# ================================================================

# ---- Configuration ----
DUMP_FILE="${1:-dumps/ubuntu.core}"    # Default memory dump
VMLINUX_DIR="vmlinux"                  # Local directory for symbol files
VOL_CMD="vol"        # Command name (adjust if needed)

# ---- Ensure required tools ----
if ! command -v $VOL_CMD &> /dev/null; then
    echo "[!] Volatility3 not found. Installing via pip..."
    pip install volatility3 || { echo "[-] Failed to install Volatility3"; exit 1; }
fi

mkdir -p "$VMLINUX_DIR"

# ---- Step 1: Extract kernel version banner ----
echo "[+] Detecting kernel version from $DUMP_FILE ..."
BANNER_OUT=$($VOL_CMD -f "$DUMP_FILE" banners.Banners 2>/dev/null | grep "Linux version" | head -n1)

if [ -z "$BANNER_OUT" ]; then
    echo "[-] Failed to detect kernel version from dump."
    exit 1
fi

# Extract kernel version safely
KERNEL_VERSION=$(echo "$BANNER_OUT" | sed -n 's/.*Linux version \([0-9.-]*-generic\).*/\1/p')
echo "[+] Detected kernel: $KERNEL_VERSION"

# ---- Step 2: Prepare paths ----
VMLINUX_FILE="$VMLINUX_DIR/vmlinux-$KERNEL_VERSION"
SYMBOL_FILE="$VMLINUX_DIR/vmlinux-$KERNEL_VERSION.json"

# ---- Step 3: Download or locate vmlinux ----
if [ ! -f "$VMLINUX_FILE" ]; then
    echo "[+] Downloading vmlinux for $KERNEL_VERSION ..."
    UBUNTU_MIRROR="https://ddebs.ubuntu.com/pool/main/l/linux"
    FILE_NAME="vmlinux-$KERNEL_VERSION"
    
    wget -q "$UBUNTU_MIRROR/${FILE_NAME}_amd64.deb" -O /tmp/vmlinux.deb 2>/dev/null || {
        echo "[-] Could not auto-download vmlinux from ddebs.ubuntu.com."
        echo "    Please manually copy /usr/lib/debug/boot/vmlinux-$KERNEL_VERSION to $VMLINUX_FILE"
        exit 1
    }

    echo "[+] Extracting vmlinux..."
    dpkg-deb -x /tmp/vmlinux.deb /tmp/vmlinux_extract
    find /tmp/vmlinux_extract -type f -name "vmlinux-$KERNEL_VERSION" -exec cp {} "$VMLINUX_FILE" \;
fi

if [ ! -f "$VMLINUX_FILE" ]; then
    echo "[-] vmlinux file not found. Cannot continue."
    exit 1
fi

# ---- Step 4: Build symbol file if missing ----
if [ ! -f "$SYMBOL_FILE" ]; then
    echo "[+] Building Volatility3 symbol table..."
    $VOL_CMD --build-symbol-table "$VMLINUX_FILE"
    mv vmlinux-$KERNEL_VERSION.json "$VMLINUX_DIR/" 2>/dev/null || true
fi

# ---- Step 5: Run pslist ----
echo "[+] Running linux.pslist..."
$VOL_CMD -f "$DUMP_FILE" --symbol-file "$SYMBOL_FILE" linux.pslist > "$VMLINUX_DIR/pslist_$KERNEL_VERSION.txt"

echo "[+] Process list saved to: $VMLINUX_DIR/pslist_$KERNEL_VERSION.txt"
echo "[✓] Done."

# run as:
# ./analyze_vm_state.sh dumps/ubuntu.core

