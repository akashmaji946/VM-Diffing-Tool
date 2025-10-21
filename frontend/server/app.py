from __future__ import annotations

import json
import os
import difflib
import re
import hashlib
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_mail import Mail, Message

# Import the compiled vmtool python module exposed by pybind11
# Ensure you've built and installed it into your environment before running the server.
import vmtool  # type: ignore

from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)
DOCS_BASE_URL = os.environ.get("DOCS_BASE_URL", "https://akashmaji946.github.io/VM-Diffing-Tool/")

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id: int) -> User | None:
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

# Create database tables and seed default admin user
with app.app_context():
    db.create_all()
    try:
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("12345678")
            admin.is_verified = True  # ensure login without email verification
            db.session.add(admin)
            db.session.commit()
            print("[INIT] Seeded default admin user: username='admin', password='12345678'")
        else:
            # Ensure admin is verified to avoid login blockers
            if not admin.is_verified:
                admin.is_verified = True
                db.session.commit()
    except Exception as _e:
        # Avoid crashing server on seed failure; logs will show details
        print(f"[INIT] Admin seed skipped due to error: {_e}")

# Print banner on server start
print("""
'##::::'##:'##::::'##:'########::'#######:::'#######::'##:::::::
 ##:::: ##: ###::'###:... ##..::'##.... ##:'##.... ##: ##:::::::
 ##:::: ##: ####'####:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
 ##:::: ##: ## ### ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
. ##:: ##:: ##. #: ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
:. ## ##::: ##:.:: ##:::: ##:::: ##:::: ##: ##:::: ##: ##:::::::
::. ###:::: ##:::: ##:::: ##::::. #######::. #######:: ########:
:::...:::::..:::::..:::::..::::::.......::::.......:::........::
""")


@app.route("/")
@login_required
def index() -> str:
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    remember = request.form.get("remember") == "on"
    
    if not username or not password:
        flash("Username and password are required", "error")
        return redirect(url_for("login"))
    
    # Try to find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not user.check_password(password):
        flash("Invalid username or password", "error")
        return redirect(url_for("login"))
    
    # Check if email verification is required
    if app.config['EMAIL_VERIFICATION_REQUIRED'] and not user.is_verified:
        flash("Please verify your email before logging in", "error")
        return redirect(url_for("login"))
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    login_user(user, remember=remember)
    flash(f"Welcome back, {user.username}!", "success")
    
    # Redirect to next page or index
    next_page = request.args.get("next")
    if next_page:
        return redirect(next_page)
    return redirect(url_for("index"))


@app.route("/signup", methods=["GET", "POST"])
def signup() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("signup.html")
    
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    # Validation
    if not username or not email or not password:
        flash("All fields are required", "error")
        return redirect(url_for("signup"))
    
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect(url_for("signup"))
    
    if len(password) < 8:
        flash("Password must be at least 8 characters long", "error")
        return redirect(url_for("signup"))
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        flash("Username already exists", "error")
        return redirect(url_for("signup"))
    
    if User.query.filter_by(email=email).first():
        flash("Email already registered", "error")
        return redirect(url_for("signup"))
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    # Explicitly set verification status based on config
    if app.config.get('EMAIL_VERIFICATION_REQUIRED', True):
        user.is_verified = False  # Require email verification
    else:
        user.is_verified = True  # Auto-verify if verification not required
    
    db.session.add(user)
    db.session.commit()
    
    # Send verification email if required
    if app.config['EMAIL_VERIFICATION_REQUIRED']:
        try:
            send_verification_email(user)
            flash("Account created! Please check your email to verify your account.", "success")
        except Exception as e:
            flash(f"Account created but failed to send verification email: {e}", "warning")
    else:
        flash("Account created successfully! You can now log in.", "success")
    
    return redirect(url_for("login"))


@app.route("/signup-success")
def signup_success() -> str:
    """Display signup success page."""
    username = request.args.get("username", "")
    email = request.args.get("email", "")
    password = request.args.get("password", "")
    base_url = app.config.get('BASE_URL', 'http://127.0.0.1:8000')
    
    return render_template(
        "signup_success.html",
        username=username,
        email=email,
        password=password,
        base_url=base_url
    )


@app.route("/logout")
@login_required
def logout() -> Response:
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("login"))


@app.route("/verify-email/<token>")
def verify_email(token: str) -> Response:
    email = User.verify_token(token, app.config['SECRET_KEY'], app.config['EMAIL_VERIFICATION_TOKEN_MAX_AGE'])
    
    if not email:
        flash("Invalid or expired verification link", "error")
        return redirect(url_for("login"))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for("login"))
    
    if user.is_verified:
        flash("Email already verified", "info")
        return redirect(url_for("login"))
    
    user.is_verified = True
    db.session.commit()
    
    # Redirect to signup success page with user details
    # Note: Password is hashed in DB, so we can't show the original password
    return redirect(url_for("signup_success", username=user.username, email=user.email, password="[Your chosen password]"))


def send_verification_email(user: User) -> None:
    """Send verification email to user."""
    token = user.generate_verification_token(app.config['SECRET_KEY'])
    # Use BASE_URL from config instead of url_for to avoid SERVER_NAME issues
    base_url = app.config.get('BASE_URL', 'http://127.0.0.1:8000')
    verify_url = f"{base_url}/verify-email/{token}"
    
    msg = Message(
        'Verify Your Email - VM Tool Server',
        recipients=[user.email]
    )
    msg.body = f'''Hello {user.username},

Thank you for signing up for VM Tool Server!

Please click the link below to verify your email address:
{verify_url}

This link will expire in 1 hour.

If you did not create this account, please ignore this email.

Best regards,
VMTool Server Team
'''
    
    # Check authentication method
    if app.config.get('MAIL_AUTH_METHOD') == 'oauth2':
        # Use OAuth2 authentication
        try:
            from gmail_oauth import send_email_with_oauth2
            sender_email = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
            if not send_email_with_oauth2(mail, msg, sender_email):
                raise Exception("OAuth2 email sending failed")
        except Exception as e:
            raise Exception(f"Failed to send email via OAuth2: {e}")
    else:
        # Use standard SMTP with password
        mail.send(msg)


@app.route("/list-files", methods=["GET", "POST"])
@login_required
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
@login_required
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


@app.route("/convert", methods=["GET", "POST"])
@login_required
def convert_page() -> str | Response:
    """HTML form to convert disk images between formats (qcow2, vdi, vmdk, raw)."""
    if request.method == "GET":
        return render_template("convert.html", result=None)

    # POST
    src_img = (request.form.get("src_img") or "").strip()
    dest_img = (request.form.get("dest_img") or "").strip()
    src_format = (request.form.get("src_format") or "").strip().lower()
    dest_format = (request.form.get("dest_format") or "").strip().lower()

    if not src_img or not dest_img or not src_format or not dest_format:
        flash("All fields are required", "error")
        return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)

    if not os.path.exists(src_img):
        flash(f"Source image not found: {src_img}", "error")
        return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)

    allowed_formats = {"qcow2", "vdi", "vmdk", "raw"}
    if src_format not in allowed_formats or dest_format not in allowed_formats:
        flash(f"Unsupported format. Allowed: {', '.join(sorted(allowed_formats))}", "error")
        return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)

    # Ensure destination directory exists
    dest_dir = os.path.dirname(dest_img) or "."
    if dest_dir and not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            flash(f"Failed to create destination directory: {e}", "error")
            return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)

    try:
        # Perform conversion via vmtool.convert.convert
        out = vmtool.convert.convert(src_img, dest_img, src_format, dest_format)  # type: ignore[attr-defined]
        result = {
            "status": "success",
            "src_img": src_img,
            "dest_img": dest_img,
            "src_format": src_format,
            "dest_format": dest_format,
            "output": out,
        }
        flash("Disk image converted successfully", "success")
        return render_template("convert.html", result=result, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)
    except AttributeError:
        flash("vmtool.convert.convert is not available. Please ensure vmtool was built with conversion support.", "error")
        return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)
    except Exception as e:  # noqa: BLE001
        flash(f"Conversion failed: {e}", "error")
        return render_template("convert.html", result=None, src_img=src_img, dest_img=dest_img, src_format=src_format, dest_format=dest_format)


@app.route("/meta", methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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


@app.route("/files-diff", methods=["GET", "POST"])
@login_required
def files_diff() -> str | Response:
    if request.method == "GET":
        return render_template("files_diff.html", result=None)

    disk1 = request.form.get("disk_path_1", "").strip()
    disk2 = request.form.get("disk_path_2", "").strip()

    if not disk1 or not disk2:
        flash("Both disk paths are required", "error")
        return redirect(url_for("files_diff"))

    try:
        # Create cache directory if it doesn't exist
        cache_dir = Path(__file__).parent / ".cache"
        cache_dir.mkdir(exist_ok=True)

        # Generate cache keys for both disks
        cache_key1 = hashlib.sha256(f"{disk1}:files".encode()).hexdigest()
        cache_key2 = hashlib.sha256(f"{disk2}:files".encode()).hexdigest()
        cache_file1 = cache_dir / f"files_diff_{cache_key1}.json"
        cache_file2 = cache_dir / f"files_diff_{cache_key2}.json"

        # Get file lists from both disks (use cache or fetch fresh)
        if cache_file1.exists():
            with open(cache_file1, 'r') as f:
                files1_dict = json.load(f)
        else:
            files1_dict = vmtool.list_all_filenames_in_disk(disk1)
            with open(cache_file1, 'w') as f:
                json.dump(files1_dict, f, indent=2)

        if cache_file2.exists():
            with open(cache_file2, 'r') as f:
                files2_dict = json.load(f)
        else:
            files2_dict = vmtool.list_all_filenames_in_disk(disk2)
            with open(cache_file2, 'w') as f:
                json.dump(files2_dict, f, indent=2)

        # Extract just the file paths (values) and sort them
        files1_set = set(files1_dict.values())
        files2_set = set(files2_dict.values())
        
        # Calculate file categories
        only_in_disk1 = files1_set - files2_set
        only_in_disk2 = files2_set - files1_set
        common_files = files1_set & files2_set

        # Build combined data for AG Grid
        all_files_data = []
        
        # Add files only in disk1
        for filepath in sorted(only_in_disk1):
            all_files_data.append({
                "filename": filepath,
                "status": "Only in VM1",
                "in_vm1": True,
                "in_vm2": False
            })
        
        # Add files only in disk2
        for filepath in sorted(only_in_disk2):
            all_files_data.append({
                "filename": filepath,
                "status": "Only in VM2",
                "in_vm1": False,
                "in_vm2": True
            })
        
        # Add common files
        for filepath in sorted(common_files):
            all_files_data.append({
                "filename": filepath,
                "status": "Common",
                "in_vm1": True,
                "in_vm2": True
            })

        # Build side-by-side diff data
        all_files_sorted = sorted(files1_set | files2_set)
        diff_rows = []
        for filepath in all_files_sorted:
            in_vm1 = filepath in files1_set
            in_vm2 = filepath in files2_set
            diff_rows.append({
                "filename": filepath,
                "in_vm1": in_vm1,
                "in_vm2": in_vm2,
                "status": "Common" if (in_vm1 and in_vm2) else ("Only in VM1" if in_vm1 else "Only in VM2")
            })

        return render_template(
            "files_diff.html",
            result={
                "data": all_files_data,
                "diff_rows": diff_rows,
                "disk1": disk1,
                "disk2": disk2,
                "total_files1": len(files1_set),
                "total_files2": len(files2_set),
                "common_files": len(common_files),
                "only_in_disk1": len(only_in_disk1),
                "only_in_disk2": len(only_in_disk2),
                "cache_file1": str(cache_file1),
                "cache_file2": str(cache_file2),
            },
        )
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("files_diff"))


@app.route("/directory-diff", methods=["GET", "POST"])
@login_required
def directory_diff() -> str | Response:
    if request.method == "GET":
        return render_template("directory_diff.html", result=None)

    disk1 = request.form.get("disk_path_1", "").strip()
    disk2 = request.form.get("disk_path_2", "").strip()
    dir1 = request.form.get("directory_1", "").strip()
    dir2 = request.form.get("directory_2", "").strip()

    if not disk1 or not disk2 or not dir1 or not dir2:
        flash("All fields are required", "error")
        return redirect(url_for("directory_diff"))

    try:
        # Create cache directory if it doesn't exist
        cache_dir = Path(__file__).parent / ".cache"
        cache_dir.mkdir(exist_ok=True)

        # Generate cache keys for both directories
        cache_key1 = hashlib.sha256(f"{disk1}:{dir1}:dir".encode()).hexdigest()
        cache_key2 = hashlib.sha256(f"{disk2}:{dir2}:dir".encode()).hexdigest()
        cache_file1 = cache_dir / f"dir_diff_{cache_key1}.json"
        cache_file2 = cache_dir / f"dir_diff_{cache_key2}.json"

        # Get file lists from both directories (use cache or fetch fresh)
        # if cache_file1.exists():
        #     with open(cache_file1, 'r') as f:
        #         files1_dict = json.load(f)
        # else:
        files1_dict = vmtool.list_all_filenames_in_directory(disk1, dir1)
        with open(cache_file1, 'w') as f:
            json.dump(files1_dict, f, indent=2)

        # if cache_file2.exists():
        #     with open(cache_file2, 'r') as f:
        #         files2_dict = json.load(f)
        # else:
        files2_dict = vmtool.list_all_filenames_in_directory(disk2, dir2)
        with open(cache_file2, 'w') as f:
            json.dump(files2_dict, f, indent=2)

        # Extract just the file paths (values) and sort them
        files1_set = set(files1_dict.values())
        files2_set = set(files2_dict.values())
        
        # Calculate file categories
        only_in_dir1 = files1_set - files2_set
        only_in_dir2 = files2_set - files1_set
        common_files = files1_set & files2_set

        # Build combined data for AG Grid
        all_files_data = []
        
        # Add files only in dir1
        for filepath in sorted(only_in_dir1):
            all_files_data.append({
                "filename": filepath,
                "status": "Only in Dir1",
                "in_dir1": True,
                "in_dir2": False
            })
        
        # Add files only in dir2
        for filepath in sorted(only_in_dir2):
            all_files_data.append({
                "filename": filepath,
                "status": "Only in Dir2",
                "in_dir1": False,
                "in_dir2": True
            })
        
        # Add common files
        for filepath in sorted(common_files):
            all_files_data.append({
                "filename": filepath,
                "status": "Common",
                "in_dir1": True,
                "in_dir2": True
            })

        # Build side-by-side diff data
        all_files_sorted = sorted(files1_set | files2_set)
        diff_rows = []
        for filepath in all_files_sorted:
            in_dir1 = filepath in files1_set
            in_dir2 = filepath in files2_set
            diff_rows.append({
                "filename": filepath,
                "in_dir1": in_dir1,
                "in_dir2": in_dir2,
                "status": "Common" if (in_dir1 and in_dir2) else ("Only in Dir1" if in_dir1 else "Only in Dir2")
            })

        return render_template(
            "directory_diff.html",
            result={
                "data": all_files_data,
                "diff_rows": diff_rows,
                "disk1": disk1,
                "disk2": disk2,
                "dir1": dir1,
                "dir2": dir2,
                "total_files1": len(files1_set),
                "total_files2": len(files2_set),
                "common_files": len(common_files),
                "only_in_dir1": len(only_in_dir1),
                "only_in_dir2": len(only_in_dir2),
                "cache_file1": str(cache_file1),
                "cache_file2": str(cache_file2),
            },
        )
    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return redirect(url_for("directory_diff"))


@app.route("/guide")
@login_required
def guide_redirect() -> Response:
    """Redirect in-app Docs menu to hosted GitHub Pages docs."""
    return redirect(DOCS_BASE_URL, code=302)


@app.route("/docs")
@app.route("/docs/<path:page>")
@login_required
def docs_redirect(page: str | None = None) -> Response:
    """Redirect legacy docs routes to hosted GitHub Pages docs."""
    return redirect(DOCS_BASE_URL, code=302)

@app.route("/compare")
@login_required
def compare_page() -> str:
    """Block comparison page"""
    return render_template("compare.html")


@app.route("/block-data")
@login_required
def block_data_page() -> str:
    """Block data viewer page"""
    return render_template("block_data.html")


# ---------------- VM Manager (QEMU/VirtualBox/VMware) ----------------
@app.route("/vm/qemu", methods=["GET", "POST"])
@login_required
def vm_qemu() -> str | Response:
    if request.method == "GET":
        return render_template("run_qemu_vm.html", result=None)

    # POST
    disk = (request.form.get("disk") or "").strip()
    cpus = request.form.get("cpus", "2").strip()
    memory = request.form.get("memory", "2048").strip()
    name = (request.form.get("name") or "").strip()
    uefi = request.form.get("uefi") == "on"
    convert = request.form.get("convert") == "on"
    no_kvm = request.form.get("no_kvm") == "on"

    if not disk:
        flash("Disk is required", "error")
        return redirect(url_for("vm_qemu"))

    try:
        res = vmtool.vmmanager.run_qemu_vm(  # type: ignore[attr-defined]
            disk=disk,
            cpus=int(cpus),
            memory_mb=int(memory),
            name=name,
            use_kvm=not no_kvm,
            use_uefi=uefi,
            convert_if_needed=convert,
        )
        return render_template("run_qemu_vm.html", result=res, disk=disk, cpus=cpus, memory=memory, name=name, uefi=uefi, convert=convert, no_kvm=no_kvm)
    except Exception as e:  # noqa: BLE001
        flash(f"Failed to run QEMU VM: {e}", "error")
        return redirect(url_for("vm_qemu"))


@app.route("/vm/vbox", methods=["GET", "POST"])
@login_required
def vm_vbox() -> str | Response:
    if request.method == "GET":
        return render_template("run_vbox_vm.html", result=None)

    disk = (request.form.get("disk") or "").strip()
    cpus = request.form.get("cpus", "2").strip()
    memory = request.form.get("memory", "2048").strip()
    name = (request.form.get("name") or "").strip()
    vram = request.form.get("vram", "32").strip()
    ostype = (request.form.get("ostype") or "Other_64").strip()
    bridged_if = (request.form.get("bridged_if") or "").strip()
    convert = request.form.get("convert") == "on"

    if not disk:
        flash("Disk is required", "error")
        return redirect(url_for("vm_vbox"))

    try:
        res = vmtool.vmmanager.run_vbox_vm(  # type: ignore[attr-defined]
            disk=disk,
            cpus=int(cpus),
            memory_mb=int(memory),
            name=name,
            vram_mb=int(vram),
            ostype=ostype,
            bridged_if=bridged_if,
            convert_if_needed=convert,
        )
        return render_template("run_vbox_vm.html", result=res, disk=disk, cpus=cpus, memory=memory, name=name, vram=vram, ostype=ostype, bridged_if=bridged_if, convert=convert)
    except Exception as e:  # noqa: BLE001
        flash(f"Failed to run VirtualBox VM: {e}", "error")
        return redirect(url_for("vm_vbox"))


@app.route("/vm/vmware", methods=["GET", "POST"])
@login_required
def vm_vmware() -> str | Response:
    if request.method == "GET":
        return render_template("run_vmware_vmdk.html", result=None)

    disk = (request.form.get("disk") or "").strip()
    cpus = request.form.get("cpus", "2").strip()
    memory = request.form.get("memory", "2048").strip()
    name = (request.form.get("name") or "").strip()
    vram = request.form.get("vram", "32").strip()
    guestos = (request.form.get("guestos") or "otherlinux-64").strip()
    vm_dir = (request.form.get("vm_dir") or "").strip()
    nic_model = (request.form.get("nic_model") or "e1000").strip()
    no_net = request.form.get("no_net") == "on"
    convert = request.form.get("convert") == "on"
    nogui = request.form.get("nogui") == "on"

    if not disk:
        flash("Disk is required", "error")
        return redirect(url_for("vm_vmware"))

    try:
        res = vmtool.vmmanager.run_vmware_vmdk(  # type: ignore[attr-defined]
            disk=disk,
            cpus=int(cpus),
            memory_mb=int(memory),
            name=name,
            vram_mb=int(vram),
            guest_os=guestos,
            vm_dir=vm_dir,
            nic_model=nic_model,
            no_net=no_net,
            convert_if_needed=convert,
            nogui=nogui,
        )
        return render_template("run_vmware_vmdk.html", result=res, disk=disk, cpus=cpus, memory=memory, name=name, vram=vram, guestos=guestos, vm_dir=vm_dir, nic_model=nic_model, no_net=no_net, convert=convert, nogui=nogui)
    except Exception as e:  # noqa: BLE001
        flash(f"Failed to run VMware VM: {e}", "error")
        return redirect(url_for("vm_vmware"))


@app.route("/api/compare", methods=["POST"])
@login_required
def api_compare() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """API endpoint to compare two disk images block by block"""
    try:
        data = request.json
        disk1 = data.get("disk1")
        disk2 = data.get("disk2")
        block_size = int(data.get("block_size", 4096))
        start_block = int(data.get("start_block", 0))
        end_block = int(data.get("end_block", -1))
        
        if not disk1 or not disk2:
            return {"error": "Both disk paths are required"}, 400
        
        if not os.path.exists(disk1):
            return {"error": f"Disk 1 not found: {disk1}"}, 400
        
        if not os.path.exists(disk2):
            return {"error": f"Disk 2 not found: {disk2}"}, 400
        
        # Call vmtool to compare disks
        result = vmtool.list_blocks_difference_in_disks(
            disk1, disk2, block_size, start_block, end_block
        )
        
        return jsonify(result)
    
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}, 500


@app.route("/api/list-files", methods=["POST"])
@login_required
def api_list_files() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """API endpoint to list files with metadata from a disk image.

    Request JSON:
    {
      "disk_path": "/path/to/disk.qcow2",
      "verbose": true
    }
    """
    try:
        data = request.json or {}
        disk_path = (data.get("disk_path") or "").strip()
        verbose = bool(data.get("verbose", False))
        if not disk_path:
            return {"error": "'disk_path' is required"}, 400

        if not os.path.exists(disk_path):
            return {"error": f"Disk not found: {disk_path}"}, 400

        entries = vmtool.list_files_with_metadata(disk_path, verbose)
        # entries: list[ {size, perms, mtime, path} ]
        return {"disk_path": disk_path, "verbose": verbose, "entries": entries}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}, 500


@app.route("/block-contents-compare", methods=["GET", "POST"])
@login_required
def block_contents_compare():
    """Form to accept two images, block size, block number, and format. Displays side-by-side contents."""
    try:
        if request.method == "GET":
            # Support direct navigation with query params from /compare
            q = request.args
            disk1_q = (q.get("disk1") or "").strip()
            disk2_q = (q.get("disk2") or "").strip()
            block_q = q.get("block")
            size_q = q.get("size")
            format_q = (q.get("format") or "hex").strip().lower()

            if disk1_q and disk2_q and block_q is not None and size_q is not None:
                # Attempt to compute directly and render
                try:
                    block_number = int(block_q)
                    block_size = int(size_q)
                    format_type = format_q if format_q in ("hex", "bits") else "hex"

                    if not os.path.exists(disk1_q):
                        flash(f"Disk 1 not found: {disk1_q}", "error")
                        return render_template("block_contents_compare.html", result=None)
                    if not os.path.exists(disk2_q):
                        flash(f"Disk 2 not found: {disk2_q}", "error")
                        return render_template("block_contents_compare.html", result=None)

                    data1 = vmtool.get_block_data_in_disk(disk1_q, block_number, block_size, format_type)
                    data2 = vmtool.get_block_data_in_disk(disk2_q, block_number, block_size, format_type)

                    key = str(block_number)
                    content1 = data1.get(key, "")
                    content2 = data2.get(key, "")

                    def format_hex(s: str) -> str:
                        bytes_list = [b for b in s.strip().split() if b]
                        lines = []
                        for i in range(0, len(bytes_list), 16):
                            row = bytes_list[i:i+16]
                            offset = format(i, '04X')
                            lines.append(f"{offset}: {' '.join(row)}")
                        return "\n".join(lines)

                    def format_bits(s: str) -> str:
                        lines = []
                        for i in range(0, len(s), 64):
                            row = s[i:i+64]
                            offset = format((i//8), '04X')
                            lines.append(f"{offset}: {row}")
                        return "\n".join(lines)

                    formatted1 = format_hex(content1) if format_type == "hex" else format_bits(content1)
                    formatted2 = format_hex(content2) if format_type == "hex" else format_bits(content2)

                    result = {
                        "disk1": disk1_q,
                        "disk2": disk2_q,
                        "block_number": block_number,
                        "block_size": block_size,
                        "format": format_type,
                        "content1": formatted1,
                        "content2": formatted2,
                    }
                    return render_template("block_contents_compare.html", result=result)
                except Exception as _e:  # noqa: BLE001
                    # Fallback to form if parsing/processing fails
                    pass

            # Default GET: show empty form
            return render_template("block_contents_compare.html", result=None)

        # POST
        disk1 = request.form.get("disk_path_1", "").strip()
        disk2 = request.form.get("disk_path_2", "").strip()
        block_number = int(request.form.get("block_number", "0"))
        block_size = int(request.form.get("block_size", "4096"))
        format_type = request.form.get("format", "hex")

        if not disk1 or not disk2:
            flash("Both disk paths are required", "error")
            return render_template("block_contents_compare.html", result=None)

        if not os.path.exists(disk1):
            flash(f"Disk 1 not found: {disk1}", "error")
            return render_template("block_contents_compare.html", result=None)

        if not os.path.exists(disk2):
            flash(f"Disk 2 not found: {disk2}", "error")
            return render_template("block_contents_compare.html", result=None)

        # Fetch data via vmtool
        data1 = vmtool.get_block_data_in_disk(disk1, block_number, block_size, format_type)
        data2 = vmtool.get_block_data_in_disk(disk2, block_number, block_size, format_type)

        key = str(block_number)
        content1 = data1.get(key, "")
        content2 = data2.get(key, "")

        # Helper formatters mirroring JS formatting
        def format_hex(s: str) -> str:
            bytes_list = [b for b in s.strip().split() if b]
            lines = []
            for i in range(0, len(bytes_list), 16):
                row = bytes_list[i:i+16]
                offset = format(i, '04X')
                lines.append(f"{offset}: {' '.join(row)}")
            return "\n".join(lines)

        def format_bits(s: str) -> str:
            lines = []
            for i in range(0, len(s), 64):
                row = s[i:i+64]
                offset = format((i//8), '04X')
                lines.append(f"{offset}: {row}")
            return "\n".join(lines)

        formatted1 = format_hex(content1) if format_type == "hex" else format_bits(content1)
        formatted2 = format_hex(content2) if format_type == "hex" else format_bits(content2)

        result = {
            "disk1": disk1,
            "disk2": disk2,
            "block_number": block_number,
            "block_size": block_size,
            "format": format_type,
            "content1": formatted1,
            "content2": formatted2,
        }

        return render_template("block_contents_compare.html", result=result)

    except Exception as e:  # noqa: BLE001
        flash(f"Error: {e}", "error")
        return render_template("block_contents_compare.html", result=None)


# Documentation routes
@app.route("/docs")
@app.route("/docs/<page>")
def docs(page: str | None = None):
    """Serve static 'Coming soon' docs pages from static/docs_html"""
    filename = "index.html" if not page else f"{page}.html"
    try:
        return send_from_directory("static/docs_html", filename)
    except Exception:
        return send_from_directory("static/docs_html", "index.html")

@app.route("/guide")
def guide():
    """GitBook-like SPA docs served statically"""
    return send_from_directory("static/guide", "index.html")

@app.route("/api/block-data", methods=["POST"])
@login_required
def api_block_data() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """API endpoint to get block data from a disk"""
    try:
        data = request.json
        disk = data.get("disk")
        block_number = int(data.get("block_number"))
        block_size = int(data.get("block_size", 4096))
        format_type = data.get("format", "hex")
        
        if not disk:
            return {"error": "Disk path is required"}, 400
        
        if not os.path.exists(disk):
            return {"error": f"Disk not found: {disk}"}, 400
        
        # Call vmtool to get block data
        result = vmtool.get_block_data_in_disk(
            disk, block_number, block_size, format_type
        )
        
        return jsonify(result)
    
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}, 500


@app.route("/api/convert", methods=["POST"])
@login_required
def api_convert() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """API endpoint to convert disk images between formats (qcow2, vdi, vmdk).

    Request JSON:
    {
      "src_img": "/path/to/src.img",
      "dest_img": "/path/to/dest.img",
      "src_format": "qcow2",
      "dest_format": "vmdk"
    }
    """
    try:
        data = request.json or {}
        src_img = (data.get("src_img") or "").strip()
        dest_img = (data.get("dest_img") or "").strip()
        src_format = (data.get("src_format") or "").strip().lower()
        dest_format = (data.get("dest_format") or "").strip().lower()

        if not src_img or not dest_img or not src_format or not dest_format:
            return {"error": "'src_img', 'dest_img', 'src_format', and 'dest_format' are required"}, 400

        if not os.path.exists(src_img):
            return {"error": f"Source image not found: {src_img}"}, 400

        allowed_formats = {"qcow2", "vdi", "vmdk", "raw"}
        if src_format not in allowed_formats:
            return {"error": f"Unsupported src_format: {src_format}. Allowed: {sorted(allowed_formats)}"}, 400
        if dest_format not in allowed_formats:
            return {"error": f"Unsupported dest_format: {dest_format}. Allowed: {sorted(allowed_formats)}"}, 400

        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest_img) or "."
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        # Perform conversion via vmtool.convert.convert
        # vmtool exposes a submodule 'convert' with function 'convert'
        try:
            out = vmtool.convert.convert(src_img, dest_img, src_format, dest_format)  # type: ignore[attr-defined]
        except AttributeError:
            return {"error": "vmtool.convert.convert is not available. Please ensure the vmtool module was built with conversion support."}, 500

        return {
            "status": "success",
            "src_img": src_img,
            "dest_img": dest_img,
            "src_format": src_format,
            "dest_format": dest_format,
            "output": out,
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}, 500


@app.errorhandler(404)
def not_found(_: Exception) -> tuple[str, int]:
    return render_template("404.html"), 404

def create_app() -> Flask:
    return app

if __name__ == "__main__":
    # Export FLASK_APP=app.py and run: python app.py
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
