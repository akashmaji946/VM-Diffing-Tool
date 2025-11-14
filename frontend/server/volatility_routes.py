from __future__ import annotations

import html
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import importlib.util

from flask import (
    Blueprint,
    jsonify,
    redirect,
    request,
    send_file,
    url_for,
)
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------------
# Paths reused from the legacy volatility3/web Flask server
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
VOL_ROOT = ROOT_DIR / "volatility3"
WEB_DIR = VOL_ROOT / "web"
SHELL_DIR = VOL_ROOT / "shell_scripts"
TEMPLATE_DIR = WEB_DIR / "templates"
PARSERS_DIR = WEB_DIR / "parsers"
REPORT_DIR = WEB_DIR / "reports"
DUMP_DIR = WEB_DIR / "dumps"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)

VOL_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

volatility_bp = Blueprint(
    "volatility",
    __name__,
)


def render_vol_template(template_name: str, **context):
    template = VOL_TEMPLATE_ENV.get_template(template_name)
    return template.render(**context)


def _load_parser(module_name: str):
    module_path = PARSERS_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load parser module {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, module_name)


def _report_filename(dump_name: str, plugin: str) -> str:
    return f"{dump_name}_{plugin}.txt"


def _run_analysis(plugin: str, dumpfile: Path) -> None:
    subprocess.run(
        [
            "bash",
            str(SHELL_DIR / "run_analysis.sh"),
            "--type",
            plugin,
            "--dump",
            str(dumpfile),
            "--out",
            str(REPORT_DIR),
        ],
        check=True,
    )


def _ensure_report_exists(dump_name: str, plugin: str) -> Path:
    report_name = _report_filename(dump_name, plugin)
    report_path = REPORT_DIR / report_name
    if not report_path.exists():
        dumpfile = DUMP_DIR / dump_name
        if not dumpfile.exists():
            raise FileNotFoundError(f"Dump file '{dump_name}' not found")
        _run_analysis(plugin, dumpfile)
    return report_path


# ---------------------------------------------------------------------------
# Helper functions (migrated from volatility3/web/server.py)
# ---------------------------------------------------------------------------
def generate_pdf(filename: str, headers: List[str], rows: Iterable[Tuple[Any, ...]]):
    pdf_path = REPORT_DIR / filename.replace(".txt", ".pdf")

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(name="TableHeader", parent=styles["Title"], fontSize=14)
    header_style = ParagraphStyle(
        name="HeaderCell",
        parent=styles["Heading6"],
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=1,
    )
    body_style = ParagraphStyle(
        name="BodyCell",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        wordWrap="CJK",
        alignment=0,
    )

    elements = [Paragraph(f"<b>Volatility3 Report:</b> {filename}", title_style), Spacer(1, 12)]

    raw_rows = [_normalize_row(headers)] + [_normalize_row(row) for row in rows]
    page_width, _ = landscape(A4)
    available_width = page_width - doc.leftMargin - doc.rightMargin
    column_count = len(headers)
    col_widths = _column_widths(raw_rows, available_width) if column_count else None

    table_data = []
    for idx, row in enumerate(raw_rows):
        style = header_style if idx == 0 else body_style
        table_data.append(_wrap_row(row, style))

    table = Table(table_data, repeatRows=1, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)

    return send_file(pdf_path, as_attachment=True)


def _normalize_row(row: Iterable[Any]) -> List[str]:
    return ["-" if cell in (None, "") else str(cell) for cell in row]


def _wrap_row(row: Iterable[str], style: ParagraphStyle) -> List[Paragraph]:
    wrapped = []
    for cell in row:
        text = html.escape(cell).replace("\n", "<br/>")
        wrapped.append(Paragraph(text, style))
    return wrapped


def _column_widths(rows: List[List[str]], available_width: float):
    if not rows:
        return None

    column_count = len(rows[0])
    max_lengths = [1] * column_count

    for row in rows:
        for idx, cell in enumerate(row):
            if idx >= column_count:
                continue
            max_lengths[idx] = max(max_lengths[idx], len(cell))

    total = sum(max_lengths)
    if total == 0:
        return [available_width / column_count] * column_count

    min_width = 35
    widths = [max(min_width, available_width * (length / total)) for length in max_lengths]

    scale = available_width / sum(widths) if sum(widths) else 1
    return [width * scale for width in widths]


def _select_parser(filename: str):
    mapping = {
        "pslist": "parse_pslist",
        "psscan": "parse_psscan",
        "bash": "parse_bash",
        "lsof": "parse_lsof",
        "sockstat": "parse_sockstat",
        "lsmod": "parse_lsmod",
        "pstree": "parse_pstree",
    }

    return next((parser for key, parser in mapping.items() if key in filename), None)


def _formatters():
    return {
        "pslist": {
            "parser": "parse_pslist",
            "headers": [
                "Offset",
                "PID",
                "TID",
                "PPID",
                "Command",
                "UID",
                "GID",
                "EUID",
                "EGID",
                "Creation Time",
                "File Output",
            ],
            "row": lambda p: [
                p["offset"],
                p["pid"],
                p["tid"],
                p["ppid"],
                p["command"],
                p["uid"],
                p["gid"],
                p["euid"],
                p["egid"],
                p["create_time"],
                p["file_output"],
            ],
        },
        "psscan": {
            "parser": "parse_psscan",
            "headers": ["Offset (P)", "PID", "TID", "PPID", "Command", "Exit State"],
            "row": lambda p: [
                p["offset"],
                p["pid"],
                p["tid"],
                p["ppid"],
                p["comm"],
                p["exit_state"],
            ],
        },
        "bash": {
            "parser": "parse_bash",
            "headers": ["PID", "Process", "Timestamp", "Command"],
            "row": lambda p: [p["pid"], p["process"], p["timestamp"], p["command"]],
        },
        "lsof": {
            "parser": "parse_lsof",
            "headers": [
                "PID",
                "TID",
                "Process",
                "FD",
                "Path",
                "Device",
                "Inode",
                "Type",
                "Mode",
                "Changed",
                "Modified",
                "Accessed",
                "Size",
            ],
            "row": lambda p: [
                p["pid"],
                p["tid"],
                p["process"],
                p["fd"],
                p["path"],
                p["device"],
                p["inode"],
                p["type"],
                p["mode"],
                p["changed"],
                p["modified"],
                p["accessed"],
                p["size"],
            ],
        },
        "sockstat": {
            "parser": "parse_sockstat",
            "headers": [
                "NetNS",
                "Process Name",
                "PID",
                "TID",
                "FD",
                "Sock Offset",
                "Family",
                "Type",
                "Proto",
                "Source Addr",
                "Source Port",
                "Destination Addr",
                "Destination Port",
                "State",
                "Filter",
            ],
            "row": lambda p: [
                p["netns"],
                p["process_name"],
                p["pid"],
                p["tid"],
                p["fd"],
                p["sock_offset"],
                p["family"],
                p["type"],
                p["proto"],
                p["source_addr"],
                p["source_port"],
                p["destination_addr"],
                p["destination_port"],
                p["state"],
                p["filter"],
            ],
        },
        "lsmod": {
            "parser": "parse_lsmod",
            "headers": ["Offset", "Module Name", "Code Size", "Taints", "Load Arguments", "File Output"],
            "row": lambda p: [
                p["offset"],
                p["module_name"],
                p["code_size"],
                p["taints"],
                p["load_arguments"],
                p["file_output"],
            ],
        },
        "pstree": {
            "parser": "parse_pstree",
            "headers": ["Offset (V)", "PID", "TID", "PPID", "Command"],
            "row": lambda p: [
                p["offset"],
                p["pid"],
                p["tid"],
                p["ppid"],
                ("  " * p.get("depth", 0)) + (p["comm"] or "-"),
            ],
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@volatility_bp.route("/")
@login_required
def index():
    dumps = sorted(os.listdir(DUMP_DIR))
    return render_vol_template(
        "index.html",
        dumps=dumps,
        dump_url=url_for("volatility.dump_memory"),
        analyze_url=url_for("volatility.analyze_dump"),
    )


@volatility_bp.route("/dump", methods=["POST"])
@login_required
def dump_memory():
    vm_name = request.form.get("vm_name", "").strip()
    dump_name = request.form.get("dump_name", "").strip()

    if not vm_name:
        return "VM name is required", 400

    filename = f"{dump_name}.core" if dump_name else f"{vm_name}.core"
    output_path = DUMP_DIR / filename

    subprocess.run(
        ["bash", str(SHELL_DIR / "create_memory_dump.sh"), vm_name, str(output_path)]
    )

    return redirect(url_for("volatility.index"))


@volatility_bp.route("/analyze", methods=["POST"])
@login_required
def analyze_dump():
    dump_name = request.form.get("dumpfile")
    plugin = request.form.get("plugin")
    dumpfile = DUMP_DIR / dump_name
    subprocess.run(
        [
            "bash",
            str(SHELL_DIR / "run_analysis.sh"),
            "--type",
            plugin,
            "--dump",
            str(dumpfile),
            "--out",
            str(REPORT_DIR),
        ]
    )
    return redirect(url_for("volatility.view_report", filename=f"{dump_name}_{plugin}.txt"))


@volatility_bp.route("/report/<filename>")
@login_required
def view_report(filename: str):
    filepath = REPORT_DIR / filename

    if not filepath.exists():
        return "Report not found", 404

    with filepath.open("r", errors="ignore") as f:
        lines = f.readlines()

    if "pslist" in filename:
        parse_pslist = _load_parser("parse_pslist")
        data = parse_pslist(lines)
        return render_vol_template("result_json.html", filename=filename, data=data)

    if "psscan" in filename:
        parse_psscan = _load_parser("parse_psscan")
        data = parse_psscan(lines)
        return render_vol_template("result_psscan.html", filename=filename, data=data)

    if "bash" in filename:
        parse_bash = _load_parser("parse_bash")
        data = parse_bash(lines)
        return render_vol_template("result_bash.html", filename=filename, data=data)

    if "lsof" in filename:
        parse_lsof = _load_parser("parse_lsof")
        data = parse_lsof(lines)
        return render_vol_template("result_lsof.html", filename=filename, data=data)

    if "sockstat" in filename:
        parse_sockstat = _load_parser("parse_sockstat")
        data = parse_sockstat(lines)
        return render_vol_template("result_sockstat.html", filename=filename, data=data)

    if "lsmod" in filename:
        parse_lsmod = _load_parser("parse_lsmod")
        data = parse_lsmod(lines)
        return render_vol_template("result_lsmod.html", filename=filename, data=data)

    if "pstree" in filename:
        parse_pstree = _load_parser("parse_pstree")
        data = parse_pstree(lines)
        for entry in data:
            depth = entry.get("depth") or 0
            comm = entry.get("comm") or "-"
            entry["formatted_comm"] = f"{'  ' * depth}{comm}"
        return render_vol_template("result_pstree.html", filename=filename, data=data)

    rows = [line.split() for line in lines]
    return render_vol_template("result.html", rows=rows, filename=filename)


@volatility_bp.route("/export/json/<filename>")
@login_required
def export_json(filename: str):
    filepath = REPORT_DIR / filename
    parser = _select_parser(filename)

    if not parser:
        return jsonify({"error": "Unsupported report type"}), 400

    parser_fn = _load_parser(parser)
    with filepath.open("r", errors="ignore") as f:
        data = parser_fn(f.readlines())

    return jsonify(data)


@volatility_bp.route("/export/txt/<filename>")
@login_required
def export_txt(filename: str):
    return send_file(REPORT_DIR / filename, as_attachment=True)


@volatility_bp.route("/export/pdf/<filename>")
@login_required
def export_pdf(filename: str):
    filepath = REPORT_DIR / filename
    if not filepath.exists():
        return "Report not found", 404

    with filepath.open("r", errors="ignore") as f:
        lines = f.readlines()

    formatters = _formatters()
    fmt = next((v for k, v in formatters.items() if k in filename), None)

    if fmt:
        parser_fn = _load_parser(fmt["parser"])
        data = parser_fn(lines)
        headers = fmt["headers"]
        rows = [fmt["row"](entry) for entry in data]
    else:
        headers = ["Line"]
        rows = [[l.strip()] for l in lines]

    return generate_pdf(filename, headers, rows)


def create_standalone_app():
    """Utility to run the volatility blueprint standalone (legacy behavior)."""
    from flask import Flask

    app = Flask(__name__)
    app.config["LOGIN_DISABLED"] = True
    app.register_blueprint(volatility_bp)
    return app
