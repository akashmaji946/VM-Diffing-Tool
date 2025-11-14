# Memory Analysis

Once your VM is running (either manually or via the VM Manager scripts), the **Volatility** section of the web UI lets you capture RAM snapshots and run Volatility3 plugins without leaving the browser.

## 1. Create a Memory Dump

1. Navigate to `https://<server_ip:port>/volatility/` (requires login).
2. Under **Dump VM Memory** enter the VirtualBox VM name exactly as it appears in `VBoxManage list vms`.
3. (Optional) Provide a custom dump filename; otherwise the server stores it as `<vm_name>.core` inside `volatility3/web/dumps/`.
4. Click **Create Dump**. The server pauses the VM, calls `volatility3/shell_scripts/create_memory_dump.sh`, waits for `VBoxManage debugvm ... dumpguestcore` to finish, then resumes the VM.

> Tip: Avoid launching multiple dumps simultaneously; VirtualBox will complain that the guest is already paused. Resume the VM (or wait for the UI to finish) before triggering another dump.

## 2. Run Volatility Plugins

Below the dump form, select:

1. **Dump file** – any `.core` file detected in `volatility3/web/dumps`.
2. **Plugin** – choose one of the Linux plugins wired into the blueprint.
3. Click **Run Analysis**. The backend executes `volatility3/shell_scripts/run_analysis.sh` with the selected plugin and writes the report to `volatility3/web/reports/<dump>_<plugin>.txt`, then opens the parsed HTML table.

### Supported Plugins

| Plugin | Description |
| --- | --- |
| `linux.pslist` | Enumerates active processes, showing PID/TID/PPID, UID/GID, command name, start time, and backing file. Great first glance at what was running when the snapshot was taken. |
| `linux.psscan` | Carves process structures from memory, catching hidden or terminated processes that no longer appear in `pslist`. Useful for rootkit detection. |
| `linux.pstree` | Displays the parent/child hierarchy. The UI indents the command column to visually highlight process trees. |
| `linux.sockstat` | Lists open sockets (AF_INET, AF_UNIX, AF_NETLINK, etc.) with process ownership, addresses, ports, state, and BPF filters. |
| `linux.lsof` | Classic "list open files" view with PID/TID, FD, path, inode, timestamps, and file size, helping correlate file usage with processes. |
| `linux.lsmod` | Shows loaded kernel modules with offsets, taints, and load arguments to spot suspicious modules. |
| `linux.bash` | Dumps bash history with PID/process name, timestamp, and command text for quick triage of interactive activity. |

Each result page offers quick export buttons (TXT/JSON/PDF). JSON uses the same parser output that powers the tables, while PDF renders a landscape table for reporting.

## Automation & CLI

- **Shell scripts:** `volatility3/shell_scripts/create_memory_dump.sh` and `run_analysis.sh` can be invoked directly if you prefer cron/CLI workflows. Pass `--type <plugin>` and `--dump /path/to/dump.core` to `run_analysis.sh`.
- **vmt CLI:** Future releases will expose dump/analysis helpers as `vmt -c volatility_dump` and `vmt -c volatility_analyze` commands to integrate with existing VM manager flows.

