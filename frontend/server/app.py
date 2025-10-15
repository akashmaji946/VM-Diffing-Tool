from __future__ import annotations

import json
import os
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
        entries = vmtool.list_files_with_metadata(disk_path, verbose)
        # entries is a list of dicts with keys: size, perms, mtime, path
        return render_template("list_files.html", result=entries, disk_path=disk_path, verbose=verbose)
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
