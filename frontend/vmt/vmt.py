"""
VMT console script entry point.
Dynamically discovers and executes commands from vmtool_scripts directory.
"""
from __future__ import annotations

import sys
import os
import subprocess
from pathlib import Path

VERSION = "0.1"


def get_scripts_dir() -> Path:
    """Get the path to vmtool_scripts directory."""
    # Assuming vmt is installed in frontend/vmt and scripts are in frontend/vmtool_scripts
    current_file = Path(__file__).resolve()
    frontend_dir = current_file.parent.parent  # Go up from vmt/ to frontend/
    scripts_dir = frontend_dir / "vmtool_scripts"
    return scripts_dir


def discover_commands() -> dict[str, Path]:
    """Discover all vmtool_*.py scripts and return them as commands."""
    scripts_dir = get_scripts_dir()
    if not scripts_dir.exists():
        return {}
    
    commands = {}
    for script in scripts_dir.glob("vmtool_*.py"):
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
        print("No commands found in vmtool_scripts directory")
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