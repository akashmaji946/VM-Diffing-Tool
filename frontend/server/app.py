from __future__ import annotations

import json
import os
import difflib
import re
import hashlib
from pathlib import Path
from typing import Any, Dict

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_file,
    Response,
)

# Import the compiled vmtool python module exposed by pybind11
# Ensure you've built and installed it into your environment before running the server.
import vmtool  # type: ignore

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/list-files", methods=["GET", "POST"])
def list_files() -> str | Response:
    if request.method == "GET":
        return render_template("list_files.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    verbose = request.form.get("verbose") == "on"

    if not disk_path:
        flash("Disk path is required", "error")
        return redirect(url_for("list_files"))

    try:
        # Create cache directory if it doesn't exist
        cache_dir = Path(__file__).parent / ".cache"
        cache_dir.mkdir(exist_ok=True)

        # Generate cache key from disk path and verbose flag
        cache_key = hashlib.sha256(f"{disk_path}:{verbose}".encode()).hexdigest()
        cache_file = cache_dir / f"list_files_{cache_key}.json"

        # Always clear cache and fetch fresh data from vmtool
        # Remove existing cache file if it exists
        if cache_file.exists():
            cache_file.unlink()

        # Fetch fresh data from vmtool
        entries = vmtool.list_files_with_metadata(disk_path, verbose)
        # entries is a list of dicts with keys: size, perms, mtime, path

        # Save to cache for potential future use (JSON download, etc.)
        cache_data = {
            "disk_path": disk_path,
            "verbose": verbose,
            "entries": entries,
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return render_template(
            "list_files.html",
            result=entries,
            disk_path=disk_path,
            verbose=verbose,
            cache_file=str(cache_file),
        )
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("list_files"))


@app.route("/files-json", methods=["GET", "POST"])
def files_json() -> str | Response:
    if request.method == "GET":
        return render_template("files_json.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    verbose = request.form.get("verbose") == "on"

    if not disk_path:
        flash("Disk path is required", "error")
        return redirect(url_for("files_json"))

    try:
        data = vmtool.get_files_with_metadata_json(disk_path, verbose)
        # Render nicely, and also allow raw JSON download
        json_str = json.dumps(data, indent=2)
        return render_template("files_json.html", result=json_str, disk_path=disk_path, verbose=verbose)
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("files_json"))


@app.route("/meta", methods=["GET", "POST"])
def meta() -> str | Response:
    if request.method == "GET":
        return render_template("meta_data.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    verbose = request.form.get("verbose") == "on"
    if not disk_path:
        flash("Disk path is required", "error")
        return redirect(url_for("meta"))

    try:
        data = vmtool.get_disk_meta_data(disk_path, verbose)
        # Data is a dict with totals and per_user/per_group lists
        return render_template("meta_data.html", result=data, disk_path=disk_path, verbose=verbose)
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("meta"))


@app.route("/file-contents", methods=["GET", "POST"])
def file_contents() -> str | Response:
    if request.method == "GET":
        return render_template("file_contents.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    name = request.form.get("name", "").strip()
    binary = request.form.get("binary") == "on"
    read_val = request.form.get("read", "-1").strip()
    stop = request.form.get("stop", "")

    try:
        read = int(read_val) if read_val else -1
    except ValueError:
        read = -1

    if not disk_path or not name:
        flash("Disk path and file path are required", "error")
        return redirect(url_for("file_contents"))

    try:
        data = vmtool.get_file_contents_in_disk(disk_path, name, binary, read, stop)
        if binary:
            pass
            # When binary, return a download of bytes
            # if isinstance(data, (bytes, bytearray)):
            #     return Response(data, mimetype="application/octet-stream")
            # Some pybind can still hand us Python bytes-like in str; fall through
        return render_template("file_contents.html", result=data, disk_path=disk_path, name=name, binary=binary, read=read, stop=stop)
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("file_contents"))


@app.route("/file-contents-format", methods=["GET", "POST"])
def file_contents_format() -> str | Response:
    if request.method == "GET":
        return render_template("file_contents_format.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    name = request.form.get("name", "").strip()
    fmt = request.form.get("format", "hex").strip()
    read_val = request.form.get("read", "-1").strip()
    stop = request.form.get("stop", "")

    try:
        read = int(read_val) if read_val else -1
    except ValueError:
        read = -1

    if not disk_path or not name:
        flash("Disk path and file path are required", "error")
        return redirect(url_for("file_contents_format"))

    try:
        data = vmtool.get_file_contents_in_disk_format(disk_path, name, fmt, read, stop)
        return render_template("file_contents_format.html", result=data, disk_path=disk_path, name=name, format=fmt, read=read, stop=stop)
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("file_contents_format"))


@app.route("/file-compare", methods=["GET", "POST"])
def file_compare() -> str | Response:
    if request.method == "GET":
        return render_template("file_compare.html", result=None)

    # Expecting two disks and two file paths
    disk1 = request.form.get("disk_path_1", "").strip()
    path1 = request.form.get("file_path_1", "").strip()
    disk2 = request.form.get("disk_path_2", "").strip()
    path2 = request.form.get("file_path_2", "").strip()
    binary = request.form.get("binary") == "on"

    if not disk1 or not path1 or not disk2 or not path2:
        flash("Please provide both disk paths and file paths.", "error")
        return redirect(url_for("file_compare"))

    try:
        # Check existence
        exists1: Dict[str, Any] = vmtool.check_file_exists_in_disk(disk1, path1)
        exists2: Dict[str, Any] = vmtool.check_file_exists_in_disk(disk2, path2)

        def regroup_hex_into_lines(s: str, per_line: int = 32) -> list[str]:
            # Extract hex byte tokens and regroup into lines of `per_line` bytes
            tokens = re.findall(r"[0-9A-Fa-f]{2}", s)
            if not tokens:
                # Fallback: splitlines if nothing matched (leave as-is)
                return s.splitlines()
            lines: list[str] = []
            for i in range(0, len(tokens), per_line):
                chunk = tokens[i:i+per_line]
                lines.append(" ".join(chunk))
            return lines

        # Prepare contents
        if exists1.get("exists"):
            if binary:
                content1 = vmtool.get_file_contents_in_disk_format(disk1, path1, "hex", -1, "")
            else:
                content1 = vmtool.get_file_contents_in_disk(disk1, path1, False, -1, "")
            if not isinstance(content1, str):
                content1 = str(content1)
            lines1 = regroup_hex_into_lines(content1, 32) if binary else content1.splitlines()
        else:
            lines1 = ["[FILE DOES NOT EXIST]"]

        if exists2.get("exists"):
            if binary:
                content2 = vmtool.get_file_contents_in_disk_format(disk2, path2, "hex", -1, "")
            else:
                content2 = vmtool.get_file_contents_in_disk(disk2, path2, False, -1, "")
            if not isinstance(content2, str):
                content2 = str(content2)
            lines2 = regroup_hex_into_lines(content2, 32) if binary else content2.splitlines()
        else:
            lines2 = ["[FILE DOES NOT EXIST]"]

        # Generate side-by-side HTML diff
        h = difflib.HtmlDiff()
        diff_html = h.make_table(
            lines1,
            lines2,
            fromdesc=f"{disk1}:{path1}",
            todesc=f"{disk2}:{path2}",
            context=False,
            numlines=0,
        )

        return render_template(
            "file_compare.html",
            result={
                "diff_html": diff_html,
                "disk1": disk1,
                "path1": path1,
                "disk2": disk2,
                "path2": path2,
                "exists1": bool(exists1.get("exists")),
                "exists2": bool(exists2.get("exists")),
                "binary": binary,
                "content1": content1 if exists1.get("exists") else "[FILE DOES NOT EXIST]",
                "content2": content2 if exists2.get("exists") else "[FILE DOES NOT EXIST]",
            },
        )
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("file_compare"))


@app.route("/check-exists", methods=["GET", "POST"])
def check_exists() -> str | Response:
    if request.method == "GET":
        return render_template("check_exists.html", result=None)

    disk_path = request.form.get("disk_path", "").strip()
    name = request.form.get("name", "").strip()

    if not disk_path or not name:
        flash("Disk path and file path are required", "error")
        return redirect(url_for("check_exists"))

    try:
        data: Dict[str, Any] = vmtool.check_file_exists_in_disk(disk_path, name)
        return render_template("check_exists.html", result=data, disk_path=disk_path, name=name)
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("check_exists"))


@app.errorhandler(404)
def not_found(_: Exception) -> tuple[str, int]:
    return render_template("404.html"), 404

def create_app() -> Flask:
    return app

if __name__ == "__main__":
    # Export FLASK_APP=app.py and run: python app.py
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
