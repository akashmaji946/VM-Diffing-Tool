import argparse
import sys
import vmtool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmtool_get_file_contents_in_disk_format",
        description="Read a guest file and return formatted output (hex or bits)",
    )
    parser.add_argument("--disk", required=True, help="Path to qcow2/raw disk image (required)")
    parser.add_argument("--name", required=True, help="Path to file inside the guest (e.g., /etc/hosts)")
    parser.add_argument("--format", required=True, choices=["hex", "bits"], help="Output format")
    parser.add_argument("--read", type=int, default=-1, help="Bytes to read (-1 means all)")
    parser.add_argument("--stop", default="", help="Stop at first occurrence of this delimiter (not included)")
    parser.add_argument("--out", help="Optional output file path; prints to stdout if omitted")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = build_parser().parse_args(argv)

    try:
        data = vmtool.get_file_contents_in_disk_format(
            args.disk, args.name, args.format, read=args.read, stop=args.stop
        )
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"Saved to: {args.out}")
        else:
            print(data)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
print(hline)