# VM Manager Scripts Reference

This document explains how to use the VM launch/management helper scripts shipped with VM-Diffing-Tool.

Scripts are located in `frontend/vmmanager_scripts/` and are also exposed via the `vmt` CLI after installation.

- Start a VBox VM: `vmtool_vmmanager_create_vbox_from_iso.py` → `vmt -c vmmanager_create_vbox_from_iso`
- QEMU: `vmtool_vmmanager_run_qemu_vm.py` → `vmt -c vmmanager_run_qemu_vm`
- VirtualBox: `vmtool_vmmanager_run_vbox_vm.py` → `vmt -c vmmanager_run_vbox_vm`
- VMware: `vmtool_vmmanager_run_vmware_vmdk.py` → `vmt -c vmmanager_run_vmware_vmdk`

> Tip: Run any command with `-h` to see full usage and defaults.

---

## Start a VBox VM

Script: `vmtool_vmmanager_create_vbox_from_iso.py`

```bash
sudo python3 vmtool_vmmanager_create_vbox_from_iso.py [-h] --iso ISO --vdi-dir VDI_DIR --vm-name
                                                VM_NAME [--ostype OSTYPE] [--memory MEMORY]
                                                [--cpus CPUS] [--disk-gb DISK_GB]
                                                [--vram VRAM] [--nic {nat,bridged}]
                                                [--boot-order BOOT_ORDER]
                                                [--bridge-if BRIDGE_IF]
```

## Run a QEMU VM

Script: `vmtool_vmmanager_run_qemu_vm.py`

```bash
sudo python3 vmtool_vmmanager_run_qemu_vm.py [-h] --disk DISK --cpus CPUS --memory MEMORY --name NAME
                                                [--no-kvm] [--uefi] [--convert]
```

---

## Run a VirtualBox VM (VDI)

Script: `vmtool_vmmanager_run_vbox_vm.py`

```bash
sudo python3 vmtool_vmmanager_run_vbox_vm.py [-h] --disk DISK --cpus CPUS --memory MEMORY --name NAME
                                                [--vram VRAM] [--ostype OSTYPE] [--bridged-if BRIDGED_IF]
                                                [--convert] [--nogui]
```

## Run a VMware VM (VMDK)

Script: `vmtool_vmmanager_run_vmware_vmdk.py`

```bash
sudo python3 vmtool_vmmanager_run_vmware_vmdk.py [-h] --disk DISK --cpus CPUS --memory MEMORY --name NAME
                                                [--vram VRAM] [--ostype OSTYPE] [--bridged-if BRIDGED_IF]
                                                [--convert] [--nogui]
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
