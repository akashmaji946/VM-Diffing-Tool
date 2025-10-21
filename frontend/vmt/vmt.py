"""
VMT console script entry point.
Dynamically discovers and executes commands from vmtool_scripts directory.
"""
from __future__ import annotations

import sys
import os
import subprocess
from pathlib import Path

VERSION = "0.2.0"


def get_package_frontend_dir() -> Path:
    """Return the frontend directory root near the installed package (parent of vmt/).

    When running from source, this points to <repo>/frontend.
    When installed system-wide, this points inside site-packages and may
    not contain the script folders; in that case we'll fall back to other roots.
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent  # vmt/ -> frontend/


def get_candidate_roots() -> list[Path]:
    """Return candidate roots to search for script folders.

    Priority order:
    1) The package-adjacent frontend directory (near vmt module).
    2) Current working directory.
    3) Parent of current working directory (useful if run inside frontend/).
    4) Common install-time data prefixes like /usr/local/share/vmt.
    """
    roots: list[Path] = []
    roots.append(get_package_frontend_dir())
    roots.append(Path.cwd())
    roots.append(Path.cwd().parent)
    # Add common install-time data prefixes
    try:
        import sys as _sys
        prefixes = {
            Path(getattr(_sys, "prefix", "/usr/local")),
            Path(getattr(_sys, "base_prefix", "/usr")),
            Path("/usr/local"),
            Path("/usr"),
        }
        for p in prefixes:
            roots.append(p / "share" / "vmt")
    except Exception:
        pass
    # Deduplicate while preserving order
    uniq: list[Path] = []
    seen = set()
    for r in roots:
        try:
            rp = r.resolve()
        except Exception:
            rp = r
        if rp not in seen:
            uniq.append(rp)
            seen.add(rp)
    return uniq


def get_script_dirs() -> list[Path]:
    """Return a list of directories to scan for vmtool CLI scripts.

    We support the following directories under frontend/:
    - vmtool_scripts/
    - vmmanager_scripts/
    - converter_scripts/
    """
    script_dirs: list[Path] = []
    for root in get_candidate_roots():
        script_dirs.append(root / "vmtool_scripts")
        script_dirs.append(root / "vmmanager_scripts")
        script_dirs.append(root / "converter_scripts")
    return script_dirs


def discover_commands() -> dict[str, Path]:
    """Discover all vmtool_*.py scripts across supported directories.

    Returns a mapping of command_name -> script_path.
    If duplicate command names are found, later directories override earlier ones.
    """
    commands: dict[str, Path] = {}
    for directory in get_script_dirs():
        if not directory.exists():
            continue
        for script in directory.glob("vmtool_*.py"):
            # Convert vmtool_check_file_exists_in_disk.py -> check_file_exists_in_disk
            command_name = script.stem.replace("vmtool_", "")
            commands[command_name] = script
    return commands


def print_welcome() -> None:
    """Print welcome banner."""
    print(f"Welcome to VMT {VERSION}")
    print("VM Diffing Tool - Utilities for inspecting VM disk images")


def list_commands() -> int:
    """List all available commands."""
    commands = discover_commands()

    if not commands:
        print("No commands found in any known scripts directory.")
        print("Searched under:")
        for root in get_candidate_roots():
            print(f"  - {root}")
        return 1
    
    print("\nAvailable commands:")
    print("=" * 60)
    for cmd_name in sorted(commands.keys()):
        print(f"  {cmd_name}")
    print("=" * 60)
    print(f"\nTotal: {len(commands)} commands")
    print("\nUsage: vmt -c <command> [arguments...]")
    print("       vmt -c <command> -h  (for command-specific help)")
    return 0


def execute_command(command_name: str, args: list[str]) -> int:
    """Execute a specific command script."""
    commands = discover_commands()
    
    if command_name not in commands:
        print(f"Error: Unknown command '{command_name}'")
        print(f"\nRun 'vmt list' to see available commands.")
        return 1
    
    script_path = commands[command_name]
    
    # Execute the script with sudo and pass remaining arguments
    cmd = ["sudo", "python3", str(script_path)] + args
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nCommand interrupted by user")
        return 130
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1


def print_help() -> None:
    """Print help message."""
    print(f"vmt - VM Tool CLI version {VERSION}")

    print("\nUsage:")
    print("  vmt                     Show welcome message")
    print("  vmt -h, --help          Show this help message")
    print("  vmt -v, --version       Show version")
    print("  vmt list                List all available commands")
    print("  vmt -c <command> [...]  Execute a specific command")

    print("\nExamples:")
    print("  vmt list")
    print("  vmt -c check_file_exists_in_disk --disk /path/to/disk.qcow2 --name /etc/hosts")
    print("  vmt -c vmmanager_run_qemu_vm --disk /path/to/disk.qcow2 --cpus 2 --memory 2048")
    print("  vmt -c convertor --src_img /path/to/src.qcow2 --dest_img /path/to/dest.vdi --src_format qcow2 --dest_format vdi")
    
    list_commands()

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    
    # No arguments - show welcome
    if len(argv) == 0:
        print_welcome()
        print("Use -h for help.")
        return 0
    
    # Handle flags
    if argv[0] in ["-h", "--help"]:
        print_help()
        return 0
    
    if argv[0] in ["-v", "--version"]:
        print(f"vmt version {VERSION}")
        return 0
    
    # List commands
    if argv[0] == "list":
        return list_commands()
    
    # Execute command with -c
    if argv[0] == "-c":
        if len(argv) < 2:
            print("Error: -c requires a command name")
            print("Usage: vmt -c <command> [arguments...]")
            print("\nRun 'vmt list' to see available commands.")
            return 1
        
        command_name = argv[1]
        command_args = argv[2:]
        return execute_command(command_name, command_args)
    
    # Unknown argument
    print(f"Error: Unknown argument '{argv[0]}'")
    print("\nRun 'vmt -h' for help.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


# pip install -e .