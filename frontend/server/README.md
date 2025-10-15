# VM Tool Flask Server

A lightweight Flask server that wraps the Python `vmtool` module (pybind11 C++ backend) and exposes simple browser forms to run operations on VM disk images.

## Endpoints

- `/` Home
- `/list-files` List files with metadata
- `/files-json` Files with metadata as JSON
- `/meta` Disk summary metadata
- `/file-contents` Read file contents (binary/text)
- `/file-contents-format` Read file contents and render as `hex` or `bits`
- `/check-exists` Check whether a file exists and show file type and metadata

## Setup

1. Ensure the `vmtool` module is built and installed into the active Python environment (your venv). For example:

```bash
# from backend/build
cmake ..
make -j$(nproc)
make install  # might require sudo depending on your CMake config
```

2. Create and activate a virtual environment, then install server deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the server:

```bash
export FLASK_APP=app.py
python app.py
# Open http://localhost:5000
```

## Notes

- The server directly imports `vmtool`. Make sure your environment (e.g., `.vm` or system site-packages) makes it importable.
- The forms assume you provide valid disk image paths and guest file paths.
- For binary reads, the endpoint returns raw bytes as `application/octet-stream`.
