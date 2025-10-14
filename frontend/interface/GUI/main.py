import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QElapsedTimer, QTimer
from PyQt6.QtWidgets import QProgressDialog
import vmtool


class ImageSaverWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QCOW2 File Lister (PyQt6)")
        self.resize(900, 600)

        self.current_disk_path: str | None = None
        self.save_dir: str = os.getcwd()

        # Global stylesheet (dark theme with accent buttons)
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0d1117; color: #e6edf3; }
            QLabel, QLineEdit, QTextEdit { color: #e6edf3; }
            QLineEdit, QTextEdit { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 8px; }
            QLabel#pathLabel { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 6px; }
            QGroupBox { border: 1px solid #30363d; border-radius: 8px; margin-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #8b949e; }
            QPushButton { background-color: #238636; color: #ffffff; border: 1px solid #2ea043; border-radius: 8px; padding: 8px 14px; font-weight: 600; }
            QPushButton:hover { background-color: #2ea043; }
            QPushButton#secondary { background-color: #30363d; color: #e6edf3; border: 1px solid #484f58; }
            QPushButton#secondary:hover { background-color: #3b424b; }
            QCheckBox { color: #e6edf3; }
            """
        )

        # --- Widgets ---
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 6)
        title = QLabel("QCOW2 File Lister")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel(f"vmtool {vmtool.version}  •  libguestfs {vmtool.libguestfs.version}")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # Top control row
        self.btn_open = QPushButton("Open QCOW2")
        self.le_filename = QLineEdit()
        self.le_filename.setPlaceholderText("Enter output filename (e.g., listing.txt)")
        self.btn_choose_dir = QPushButton("Choose Save Directory")
        self.btn_choose_dir.setObjectName("secondary")
        self.lbl_dir = QLabel(self.save_dir)
        self.lbl_dir.setObjectName("pathLabel")
        self.lbl_dir.setWordWrap(True)
        self.cb_verbose = QCheckBox("Verbose logs")

        # Selected file info / status
        self.lbl_preview = QLabel("No qcow2 selected")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("QLabel { background: #161b22; border: 1px dashed #30363d; border-radius: 8px; padding: 16px; color: #8b949e; }")

        # Save button
        self.btn_save = QPushButton("Save Listing")

        # Logs
        logs_group = QWidget()
        logs_layout = QVBoxLayout(logs_group)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setPlaceholderText("Logs will appear here...")
        # lighter background box for logs while staying in dark theme
        self.txt_logs.setStyleSheet("QTextEdit { background-color: #1f242d; border: 1px solid #30363d; border-radius: 8px; }")
        logs_layout.addWidget(self.txt_logs)

        # --- Layouts ---
        top_row1 = QHBoxLayout()
        top_row1.setSpacing(10)
        top_row1.addWidget(self.btn_open, 0)
        top_row1.addWidget(self.le_filename, 1)

        top_row2 = QHBoxLayout()
        top_row2.setSpacing(10)
        top_row2.addWidget(self.btn_choose_dir, 0)
        top_row2.addWidget(self.lbl_dir, 1)
        top_row2.addWidget(self.cb_verbose, 0)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        main_layout.addWidget(header)
        main_layout.addLayout(top_row1)
        main_layout.addLayout(top_row2)
        main_layout.addWidget(self.lbl_preview, stretch=1)
        main_layout.addWidget(self.btn_save)
        main_layout.addWidget(logs_group, stretch=1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Signals ---
        self.btn_open.clicked.connect(self.on_open_image)
        self.btn_choose_dir.clicked.connect(self.on_choose_dir)
        self.btn_save.clicked.connect(self.on_save_image)

        # Runtime helpers
        self._worker_thread: QThread | None = None
        self._progress: QProgressDialog | None = None
        self._elapsed_timer: QElapsedTimer | None = None
        self._elapsed_ui_timer: QTimer | None = None

    # --- Helpers / Logging ---
    def log(self, msg: str, verbose_only: bool = False):
        if verbose_only and not self.cb_verbose.isChecked():
            return
        self.txt_logs.append(msg)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # --- Slots ---
    def on_open_image(self):
        filters = "QCOW2 Images (*.qcow *.qcow2);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a QCOW2 image", "", filters)
        if not file_path:
            self.log("Open image canceled.", verbose_only=True)
            return
        self.current_disk_path = file_path
        base_name = os.path.basename(file_path)
        name_no_ext, _ = os.path.splitext(base_name)

        # Set default output filename if empty
        if not self.le_filename.text().strip():
            self.le_filename.setText(f"{name_no_ext}_listing.txt")

        self.lbl_preview.setText(f"Selected QCOW2: {file_path}")
        self.log(f"Selected qcow2: {file_path}")

    def on_choose_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Choose Save Directory", self.save_dir)
        if not dir_path:
            self.log("Choose directory canceled.", verbose_only=True)
            return
        self.save_dir = dir_path
        self.lbl_dir.setText(dir_path)
        self.log(f"Save directory set to: {dir_path}")

    def on_save_image(self):
        if not self.current_disk_path:
            QMessageBox.information(self, "No QCOW2", "Please open a qcow2 image first.")
            self.log("Save aborted: no qcow2 selected.")
            return

        raw_name = self.le_filename.text().strip()
        if not raw_name:
            QMessageBox.information(self, "Missing Filename", "Please enter an output filename.")
            self.log("Save aborted: missing filename.")
            return

        # Ensure extension exists; if missing, use .txt
        name, ext = os.path.splitext(raw_name)
        if not ext:
            ext = ".txt"
            raw_name = name + ext

        # Sanitize save directory and ensure it exists
        target_dir = self.save_dir or os.getcwd()
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Directory Error", f"Failed to ensure directory:\n{target_dir}\n\n{e}")
            self.log(f"Failed to ensure directory '{target_dir}': {e}")
            return

        target_path = os.path.join(target_dir, raw_name)
        self.log(f"Saving listing to: {target_path}")
        verbose_flag = self.cb_verbose.isChecked()
        self.log(f"Verbose flag is {'ON' if verbose_flag else 'OFF'}", verbose_only=True)

        # Start background worker with loader and elapsed time
        self.start_save_worker(disk_path=self.current_disk_path, target_path=target_path, verbose=verbose_flag)


    # --- Background worker management ---
    def start_save_worker(self, disk_path: str, target_path: str, verbose: bool):
        # Progress dialog (indeterminate)
        self._progress = QProgressDialog("Saving listing...", None, 0, 0, self)
        self._progress.setWindowTitle("Working")
        self._progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._progress.setCancelButton(None)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        # Elapsed timers
        self._elapsed_timer = QElapsedTimer()
        self._elapsed_timer.start()
        self._elapsed_ui_timer = QTimer(self)
        self._elapsed_ui_timer.setInterval(100)
        self._elapsed_ui_timer.timeout.connect(self.update_progress_elapsed)
        self._elapsed_ui_timer.start()

        # Worker thread
        self._worker_thread = QThread(self)
        self._worker = SaveWorker(disk_path=disk_path, target_path=target_path, verbose=verbose)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    def update_progress_elapsed(self):
        if self._progress and self._elapsed_timer:
            secs = self._elapsed_timer.elapsed() / 1000.0
            self._progress.setLabelText(f"Saving listing... {secs:.1f}s")

    def on_worker_finished(self, success: bool, count: int, error: str, duration_ms: int, sample_entries: list):
        # Stop timers and close progress
        if self._elapsed_ui_timer:
            self._elapsed_ui_timer.stop()
            self._elapsed_ui_timer = None
        if self._progress:
            self._progress.close()
            self._progress = None

        duration_sec = duration_ms / 1000.0
        if success:
            self.log(f"Completed in {duration_sec:.2f}s. Wrote {count} entries.")
            if sample_entries:
                self.log("Sample entries:")
                for d in sample_entries:
                    self.log(f"  {d['size']} {d['perms']} {d['mtime']} {d['path']}")
            QMessageBox.information(self, "Saved", f"Listing completed in {duration_sec:.2f}s")
        else:
            QMessageBox.critical(self, "Save Failed", f"Failed after {duration_sec:.2f}s.\n\n{error}")
            self.log(f"Save failed: {error}")


class SaveWorker(QObject):
    finished = pyqtSignal(bool, int, str, int, list)  # success, count, error, duration_ms, sample_entries

    def __init__(self, disk_path: str, target_path: str, verbose: bool):
        super().__init__()
        self.disk_path = disk_path
        self.target_path = target_path
        self.verbose = verbose

    def run(self):
        timer = QElapsedTimer()
        timer.start()
        try:
            entries = vmtool.list_files_with_metadata(self.disk_path, verbose=self.verbose)
            vmtool.write_files_with_metadata(entries, self.target_path)
            # Prepare small sample to emit
            count = len(entries)
            sample = []
            for i in range(min(5, count)):
                d = entries[i]
                sample.append({
                    'size': d['size'],
                    'perms': d['perms'],
                    'mtime': d['mtime'],
                    'path': d['path']
                })
            self.finished.emit(True, count, "", timer.elapsed(), sample)
        except Exception as e:
            self.finished.emit(False, 0, str(e), timer.elapsed(), [])

def main():
    app = QApplication(sys.argv)
    win = ImageSaverWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()