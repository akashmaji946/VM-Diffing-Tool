# VM Manager Scripts Reference

This document explains how to use the VM launch/management helper scripts shipped with VM-Diffing-Tool.

Scripts are located in `frontend/vmmanager_scripts/` and are also exposed via the `vmt` CLI after installation.

- QEMU: `vmtool_vmmanager_run_qemu_vm.py` → `vmt -c vmmanager_run_qemu_vm`
- VirtualBox: `vmtool_vmmanager_run_vbox_vm.py` → `vmt -c vmmanager_run_vbox_vm`
- VMware: `vmtool_vmmanager_run_vmware_vmdk.py` → `vmt -c vmmanager_run_vmware_vmdk`

> Tip: Run any command with `-h` to see full usage and defaults.

---

## Run a QEMU VM

Script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_qemu_vm.py`

```bash
# via vmt
vmt -c vmmanager_run_qemu_vm \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048 \
  --name my-vm [--no-kvm] [--uefi] [--convert]

# direct
python3 frontend/vmmanager_scripts/vmtool_vmmanager_run_qemu_vm.py \
  --disk /path/to/disk.qcow2 \
  --cpus 2 \
  --memory 2048 \
  --name my-vm
```

---

## Run a VirtualBox VM (VDI)

Script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_vbox_vm.py`

```bash
# via vmt
vmt -c vmmanager_run_vbox_vm \
  --disk /path/to/disk.vdi \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --ostype Ubuntu_64 [--bridged-if eth0] [--convert]

# direct
python3 frontend/vmmanager_scripts/vmtool_vmmanager_run_vbox_vm.py \
  --disk /path/to/disk.vdi \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --ostype Ubuntu_64
```

Notes:
- VirtualBox requires host kernel modules (`vboxdrv`, `vboxnetctl`).
- Running VBox fully inside Docker is not recommended; prefer running on the host.

---

## Run a VMware VM (VMDK)

Script: `frontend/vmmanager_scripts/vmtool_vmmanager_run_vmware_vmdk.py`

```bash
# via vmt
vmt -c vmmanager_run_vmware_vmdk \
  --disk /path/to/disk.vmdk \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --guestos ubuntu22-64 \
  [--vm-dir ~/vmware/my-vm] \
  [--nic-model e1000|e1000e|vmxnet3] \
  [--no-net] [--convert] [--nogui]

# direct
python3 frontend/vmmanager_scripts/vmtool_vmmanager_run_vmware_vmdk.py \
  --disk /path/to/disk.vmdk \
  --cpus 2 \
  --memory 2048 \
  --name my-vm \
  --vram 32 \
  --guestos ubuntu22-64
```

Notes:
- VMware is a host hypervisor. `vmrun`/`vmplayer` and kernel modules (`vmmon`, `vmnet*`) must be installed on the host.
- Using VMware inside Docker is not recommended. Use the script to prepare the VM and run the displayed host command.

If you get error `Failed to open /dev/vboxdrv: No such file or directory`, install VirtualBox kernel modules:

```bash
sudo apt-get install virtualbox-dkms
```

## Install VirtualBox and VMware on Ubuntu
Refer official docs for more details:
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- [VMware](https://www.vmware.com)
