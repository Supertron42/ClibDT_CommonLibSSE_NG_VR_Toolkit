import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone
from colorama import Fore, Style, init

try:
    from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

from modules.utilities.common import VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QCheckBox, QProgressBar, QFrame, QGroupBox, QLineEdit, QFileDialog, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

init(autoreset=True)

# Use config directory from dev root or fallback
from modules.config_utils import get_config_directory
CONFIG_DIR = get_config_directory()
LAST_BACKUP_PATH_FILE = CONFIG_DIR / "clibdt_backup_config.json"

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_input(msg, default=None):
    val = input(f"{msg} ").strip()
    if val.lower() == "m":
        return "M"
    return val or default

def should_copy_by_mtime(src: Path, dst: Path) -> bool:
    return not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime

def collect_files_to_copy(dev_root: Path, backup_root: Path, smart: bool) -> list[tuple[Path, Path]]:
    tasks = []
    for dirpath, _, filenames in os.walk(dev_root):
        for name in filenames:
            src = Path(dirpath) / name
            rel_path = src.relative_to(dev_root)
            dst = backup_root / rel_path
            if not smart or should_copy_by_mtime(src, dst):
                tasks.append((src, dst))
    return tasks

def save_last_backup_info(backup_path: str):
    """Saves the last backup path and timestamp to a JSON file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)  # Ensure config directory exists
    import json
    config_data = {
        "last_backup_path": backup_path,
        "last_backup_timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds'),
        "clibdt_version": VERSION
    }
    with open(LAST_BACKUP_PATH_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

class BackupThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, dev_root, backup_path, smart_backup=True, status_callback=None):
        super().__init__()
        self.dev_root = Path(dev_root)
        self.backup_path = Path(backup_path)
        self.smart_backup = smart_backup
        self.status_callback = status_callback
        
        # Throttling for status updates to reduce CPU usage
        self.last_status_time = 0
        self.status_update_interval = 2.0  # Update every 2 seconds
        self.pending_status_messages = []
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.flush_pending_status)
        self.status_timer.start(2000)  # 2 second timer
    
    def run(self):
        try:
            def status(msg):
                # Always emit progress signal immediately for important messages
                self.progress_signal.emit(msg)
                
                # Throttle status callback to reduce CPU usage
                if self.status_callback:
                    self.status_callback(msg)
            
            def throttled_status(msg):
                """Status function that throttles updates to reduce CPU usage"""
                # Always emit progress signal immediately
                self.progress_signal.emit(msg)
                
                # Add to pending messages for throttled callback
                self.pending_status_messages.append(msg)
            
            status(f"[INFO] Starting backup from {self.dev_root} to {self.backup_path}")
            
            # Create backup directory
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            if self.smart_backup:
                status("[INFO] Smart backup mode: Only copying newer/changed files...")
                tasks = collect_files_to_copy(self.dev_root, self.backup_path, smart=True)
                status(f"[INFO] Found {len(tasks)} files to backup")
            else:
                status("[INFO] Full backup mode: Copying all files...")
                tasks = collect_files_to_copy(self.dev_root, self.backup_path, smart=False)
                status(f"[INFO] Found {len(tasks)} files to backup")
            
            # Copy files with throttled status updates
            copied_count = 0
            for src, dst in tasks:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied_count += 1
                    if copied_count % 100 == 0:  # Update every 100 files
                        throttled_status(f"[INFO] Copied {copied_count}/{len(tasks)} files...")
                except Exception as e:
                    throttled_status(f"[WARN] Failed to copy {src}: {e}")
                    continue
            
            # Stop the timer and flush any remaining messages
            self.status_timer.stop()
            self.flush_pending_status()
            
            # Save backup info
            save_last_backup_info(str(self.backup_path))
            
            status(f"[OK] Backup completed! Copied {copied_count} files.")
            self.finished_signal.emit(True, f"Backup completed! Copied {copied_count} files.")
                
        except Exception as e:
            # Stop the timer and flush any remaining messages
            self.status_timer.stop()
            self.flush_pending_status()
            self.finished_signal.emit(False, f"Backup failed: {e}")
    
    def flush_pending_status(self):
        """Flush pending status messages to reduce CPU usage"""
        if self.pending_status_messages and self.status_callback:
            # Send the most recent message to avoid spam
            latest_message = self.pending_status_messages[-1]
            self.status_callback(latest_message)
            self.pending_status_messages.clear()
    
    def stop(self):
        """Stop the backup thread and clean up"""
        self.status_timer.stop()
        self.flush_pending_status()
        super().stop()

class BackupDevRootPanel(QWidget):
    def __init__(self, parent=None, status_callback=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.backup_thread = None
        self.theme_manager = None
        self.init_ui()
    
    def init_ui(self):
        # Main layout with proper spacing (following AI Theme Instructions pattern)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # 15px margins like create_project.py
        layout.setSpacing(8)  # 8px spacing like create_project.py
        
        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)  # 8px spacing like create_project.py
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Backup Dev Root")
        title.setObjectName("main_title")
        title_row.addWidget(title)
        
        # Add divider line
        title_divider = QLabel()
        title_divider.setObjectName("title_divider")
        title_divider.setFixedHeight(2)  # 2px for main title
        title_divider.setMinimumWidth(120)
        title_row.addWidget(title_divider)
        
        title_row.addStretch()  # Push divider to the left
        layout.addLayout(title_row)
        
        # Description
        desc = QLabel("Create a backup copy of your development environment and projects.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        
        # Backup destination section
        dest_section = QWidget()
        dest_section.setObjectName("dest_section")
        dest_layout = QVBoxLayout(dest_section)
        dest_layout.setContentsMargins(0, 0, 0, 8)  # 8px bottom margin like create_project.py
        dest_layout.setSpacing(8)  # 8px spacing like create_project.py
        
        # Path input row
        path_row = QHBoxLayout()
        path_row.setSpacing(8)  # 8px spacing like create_project.py
        path_row.setContentsMargins(0, 0, 0, 0)
        
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setPlaceholderText("Choose backup destination folder...")
        self.backup_path_edit.setToolTip("Select where to save the backup")
        self.backup_path_edit.setObjectName("backup_path_input")
        self.backup_path_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.backup_path_edit.setMinimumWidth(200)
        self.backup_path_edit.setMinimumHeight(24)  # Compact minimum height
        self.backup_path_edit.setMaximumHeight(32)  # Compact maximum height
        path_row.addWidget(self.backup_path_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setProperty("btnType", "folder")
        browse_btn.setToolTip("Browse for backup destination")
        browse_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        browse_btn.setFixedWidth(80)
        browse_btn.setMinimumHeight(24)  # Compact minimum height
        browse_btn.setMaximumHeight(32)  # Compact maximum height
        browse_btn.clicked.connect(self.browse_backup_path)
        path_row.addWidget(browse_btn)
        
        dest_layout.addLayout(path_row)
        layout.addWidget(dest_section)
        
        # Backup options section
        options_section = QWidget()
        options_section.setObjectName("options_section")
        options_layout = QVBoxLayout(options_section)
        options_layout.setContentsMargins(0, 0, 0, 8)  # 8px bottom margin like create_project.py
        options_layout.setSpacing(8)  # 8px spacing like create_project.py
        
        self.smart_backup_cb = QCheckBox("Smart backup (only copy newer/changed files)")
        self.smart_backup_cb.setChecked(True)
        self.smart_backup_cb.setToolTip("Only copy files that are newer than those in the backup destination")
        self.smart_backup_cb.setObjectName("smart_backup_checkbox")
        options_layout.addWidget(self.smart_backup_cb)
        
        layout.addWidget(options_section)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("backup_progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Button row with responsive sizing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)  # 8px spacing like create_project.py
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        self.backup_btn = QPushButton("Start Backup")
        self.backup_btn.setProperty("btnType", "success")
        self.backup_btn.setToolTip("Start backing up the dev root")
        self.backup_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.backup_btn.setMinimumHeight(24)  # Compact minimum height
        self.backup_btn.setMaximumHeight(32)  # Compact maximum height
        self.backup_btn.clicked.connect(self.start_backup)
        btn_row.addWidget(self.backup_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("btnType", "uninstall")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setMinimumHeight(24)  # Compact minimum height
        self.stop_btn.setMaximumHeight(32)  # Compact maximum height
        self.stop_btn.clicked.connect(self.stop_backup)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)
        
        layout.addLayout(btn_row)
        
        # Add stretch to prevent content from expanding to fill available space
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Apply initial theme
        self.apply_theme()
    
    def set_theme_manager(self, theme_manager):
        """Set the theme manager for this panel"""
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme to the panel"""
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            # Fallback theme
            theme = {
                'window_bg': '#1e1e1e',
                'bg_primary': '#2d2d2d',
                'bg_secondary': '#252525',
                'text_primary': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'text_light': '#ffffff',
                'button_bg': '#0078d4',
                'button_hover': '#106ebe',
                'button_pressed': '#005a9e',
                'input_bg': '#2d2d2d',
                'input_border': '#404040',
                'input_focus': '#0078d4',
                'separator': '#404040',
                'success_color': '#27ae60',
                'warning_color': '#f39c12',
                'error_color': '#e74c3c',
                'info_color': '#3498db'
            }
        
        self.setStyleSheet(f"""
            /* Ultra-compact styling that overrides ALL global styling */
            BackupDevRootPanel,
            BackupDevRootPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            BackupDevRootPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Header elements - ONLY these are bold */
            BackupDevRootPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 2px !important;
                background: transparent !important;
            }}
            
            BackupDevRootPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 8px !important;
                font-weight: normal !important;
            }}
            
            BackupDevRootPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-top: 8px !important;
                margin-bottom: 4px !important;
                background: transparent !important;
            }}
            
            /* Divider lines */
            BackupDevRootPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            BackupDevRootPanel QLabel#section_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Input field styling - responsive resizing */
            BackupDevRootPanel QLineEdit,
            BackupDevRootPanel QLineEdit:hover,
            BackupDevRootPanel QLineEdit:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-height: 24px !important;
                max-height: 32px !important;
            }}
            
            BackupDevRootPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            BackupDevRootPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* CheckBox styling - completely transparent background */
            BackupDevRootPanel QCheckBox {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                spacing: 8px !important;
                padding: 2px 0px !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            /* Override any inherited backgrounds from parent widgets */
            BackupDevRootPanel QCheckBox,
            BackupDevRootPanel QCheckBox:hover,
            BackupDevRootPanel QCheckBox:pressed,
            BackupDevRootPanel QCheckBox:checked {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }}
            
            BackupDevRootPanel QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                border: 2px solid {theme['input_border']} !important;
                background-color: {theme['input_bg']} !important;
                border-radius: 3px !important;
            }}
            
            BackupDevRootPanel QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']} !important;
                border-color: {theme['button_bg']} !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
            }}
            
            BackupDevRootPanel QCheckBox:hover::indicator:unchecked {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            /* Ensure checkbox text area is completely transparent */
            BackupDevRootPanel QCheckBox::text {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Nuclear option: Override ALL possible checkbox backgrounds */
            BackupDevRootPanel QCheckBox * {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }}
            
            /* Progress Bar styling */
            BackupDevRootPanel QProgressBar {{
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                text-align: center !important;
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                min-height: 24px !important;
                max-height: 32px !important;
            }}
            
            BackupDevRootPanel QProgressBar::chunk {{
                background-color: {theme['success_color']} !important;
                border-radius: 2px !important;
            }}
            
            /* Button styling - unified gradient system with responsive sizing */
            BackupDevRootPanel QPushButton,
            BackupDevRootPanel QPushButton:hover,
            BackupDevRootPanel QPushButton:pressed,
            BackupDevRootPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            BackupDevRootPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons - Green theme with bright hover effects */
            BackupDevRootPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Folder buttons - Blue theme with bright hover effects */
            BackupDevRootPanel QPushButton[btnType="folder"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['info_color']}, stop:1 {theme['info_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['info_color']} !important;
                padding: 6px 8px !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="folder"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #85c1e9, stop:0.5 #5dade2, stop:1 #3498db) !important;
                border: 2px solid #a9cce3 !important;
                color: #ffffff !important;
                padding: 7px 9px !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="folder"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c) !important;
                border: 2px solid #1b4f72 !important;
                color: #ffffff !important;
                padding: 8px 10px !important;
            }}
            
            /* Uninstall/Danger buttons - Red theme with bright hover effects */
            BackupDevRootPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            BackupDevRootPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
        """)
    
    def showEvent(self, event):
        """Override showEvent to apply theme when panel becomes visible"""
        super().showEvent(event)
        try:
            main_window = self.window()
            theme_manager = getattr(main_window, 'theme_manager', None)
            if theme_manager:
                self.set_theme_manager(theme_manager)
        except Exception:
            pass
    
    def browse_backup_path(self):
        """Browse for backup destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
        if folder:
            self.backup_path_edit.setText(folder)
    
    def start_backup(self):
        backup_path = self.backup_path_edit.text().strip()
        if not backup_path:
            self.status("[ERROR] Please select a backup destination.")
            return
        
        dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
        if not dev_root:
            self.status("[ERROR] XSE_CLIBDT_DEVROOT is not set.")
            return
        
        self.backup_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        self.status("=== Starting Backup ===")
        
        # Start backup thread
        self.backup_thread = BackupThread(
            dev_root=dev_root,
            backup_path=backup_path,
            smart_backup=self.smart_backup_cb.isChecked(),
            status_callback=self.status
        )
        self.backup_thread.progress_signal.connect(self.status)
        self.backup_thread.finished_signal.connect(self.backup_finished)
        self.backup_thread.start()
    
    def stop_backup(self):
        if self.backup_thread and self.backup_thread.isRunning():
            self.backup_thread.stop()  # Use the new stop method
            self.backup_thread.terminate()
            self.backup_thread.wait()
            self.status("[INFO] Backup stopped by user.")
            self.backup_finished(False, "Backup stopped by user.")
    
    def backup_finished(self, success, message):
        self.backup_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status(f"[SUCCESS] {message}")
        else:
            self.status(f"[ERROR] {message}")
    
    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

def run_backup_dev_root():
    """CLI version for backward compatibility"""
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set.", Fore.RED)
        return

    dev_root = Path(dev_root).resolve()
    if not dev_root.exists():
        cprint(f"[ERROR] Dev root does not exist: {dev_root}", Fore.RED)
        return

    dev_root_name = dev_root.name
    cprint("=== SKSE Dev Backup Utility ===", Fore.CYAN)
    cprint(f"[INFO] Source folder: {dev_root}", Fore.CYAN)

    last_path = None
    if LAST_BACKUP_PATH_FILE.exists():
        try:
            import json
            with open(LAST_BACKUP_PATH_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                last_path = config_data.get("last_backup_path")
        except Exception:
            pass

    dest_base = prompt_input(f"Enter destination base folder [{last_path or 'required'}]:", last_path)
    if dest_base == "M":
        cprint("[CANCELLED] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    if not dest_base:
        cprint("[CANCELLED] No destination provided.", Fore.YELLOW)
        return

    dest_base = Path(dest_base).expanduser().resolve()
    backup_root = dest_base / dev_root_name
    backup_root.mkdir(parents=True, exist_ok=True)

    save_last_backup_info(str(dest_base))

    print()
    mode = prompt_input("Backup mode: Smart (S - only new/diff) or Full (F)? [Default: S]:", "S").upper()
    if mode == "M":
        cprint("[CANCELLED] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    smart = mode != "F"

    cprint("[INFO] Scanning files...", Fore.LIGHTBLACK_EX)
    tasks = collect_files_to_copy(dev_root, backup_root, smart)

    if not tasks:
        cprint("[OK] Nothing to back up. Everything is up to date.", Fore.GREEN)
        input("\nPress Enter to return...")
        return

    print()
    cprint(f"[INFO] Press Ctrl+C to cancel. Total files to copy: {len(tasks)}", Fore.LIGHTBLACK_EX)
    cprint(f"Starting backup ({'Smart' if smart else 'Full'})...\n", Fore.CYAN)

    try:
        if RICH_AVAILABLE:
            console = Console()
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Backing up", total=len(tasks))
                for src, dst in tasks:
                    try:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        time.sleep(0.001)
                    except PermissionError:
                        cprint(f"[SKIPPED] File in use: {src}", Fore.YELLOW)
                    except Exception as e:
                        cprint(f"[ERROR] Failed to copy {src} → {dst}: {e}", Fore.RED)
                    progress.update(task, advance=1)
        else:
            for src, dst in tasks:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    time.sleep(0.001)
                except PermissionError:
                    cprint(f"[SKIPPED] File in use: {src}", Fore.YELLOW)
                except Exception as e:
                    cprint(f"[ERROR] Failed to copy {src} → {dst}: {e}", Fore.RED)

    except KeyboardInterrupt:
        cprint("\n[ABORTED] Backup canceled by user.", Fore.RED)
        return
    
    print()
    cprint(f"[COMPLETE] Backup finished successfully: {backup_root}", Fore.GREEN)
    input("\nPress Enter to return...")

if __name__ == "__main__":
    run_backup_dev_root()
