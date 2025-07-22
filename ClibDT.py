# ------------------ Standard Library ----------------------
import os
import sys
import re
import subprocess
import atexit
import builtins
import webbrowser
from datetime import datetime
from pathlib import Path
import argparse
from colorama import init, Fore, Style, AnsiToWin32
init(autoreset=True) 

# ------------------ Panel Imports (must be before usage) ----------------------
from modules.create_project import CreateProjectPanel
from modules.build_project import BuildProjectPanel
from modules.update_project_deps import UpdateProjectDepsPanel
from modules.detach_remove_git import DetachGitPanel
from modules.refresh_project import RefreshProjectPanel
from modules.explorer import ExplorerPanel
from modules.quick_launch import QuickLaunchManager
from modules.theme_manager import ThemeManager
from modules.progress_widget import ProgressWidget, ActivityIndicator


parser = argparse.ArgumentParser()
parser.add_argument('--no-pause', action='store_true', help='Disable input pauses for automation')
args, unknown = parser.parse_known_args()
NO_PAUSE = args.no_pause

# ------------------ Add to Module Path --------------------
sys.path.append(str(Path(__file__).parent.resolve()))

# ------------------ Utility Functions ----------------------
# from modules.utilities.logger import cprint # This line is removed as per the edit hint.

# ------------------ Theme System ----------------------
# Theme management moved to modules/theme_manager.py

#----------requests----------
try:
    import requests
except ImportError:
    requests = None

#----------version----------
from modules.utilities.common import VERSION, NEXUS_URL
_version_checked = False
_version_message = ""

#----------env var call----------
from modules.env_var_call import check_required_env_vars

#----------project picker----------
def project_picker(require_existing_xmake=True):
    root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not root:
        return None
    root_path = Path(root)
    scan_base = root_path / "projects" if (root_path / "projects").exists() else root_path
    if not scan_base.exists():
        return None
    
    # Import the new project detection module
    try:
        from modules.generate_clib_project import is_valid_clib_project
    except ImportError:
        # Fallback to old xmake.lua detection if module not available
        def is_valid_clib_project(project_path):
            return (project_path / "xmake.lua").exists()
    
    projects = []
    for subdir in scan_base.iterdir():
        if subdir.is_dir():
            if require_existing_xmake:
                if is_valid_clib_project(subdir):
                    projects.append(subdir)
            else:
                projects.append(subdir)
    if not projects:
        return None
    print("\n=========================================")
    print("    Select a Project Folder")
    print("=========================================")
    for i, p in enumerate(projects, start=1):
        print(f"{i}. {p.relative_to(scan_base)}")
    print("M. Return to main menu\n")
    userInput = input("Enter project number: ").strip()
    if userInput.lower() == "m":
        return None
    if not userInput.isdigit():
        return None
    idx = int(userInput)
    if not (1 <= idx <= len(projects)):
        return None
    return str(projects[idx - 1])

#----------run py file----------
from contextlib import contextmanager
@contextmanager
def preserve_cwd():
    old_cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_cwd)

def run_py_file(path):
        # Always resolve relative to the main script's directory
        base_dir = Path(__file__).parent.resolve()
        abs_path = (base_dir / path).resolve() if not Path(path).is_absolute() else Path(path)
        if not abs_path.exists():
            input("Press Enter to continue...")
            return
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                code = compile(f.read(), str(abs_path), 'exec')
                exec(code, {"__name__": "__main__", "__file__": str(abs_path)})
        except Exception as e:
            print(e)
            input("Press Enter to continue...")

#----------download----------
import urllib.request
import ssl
def download_with_progress(url, dest_path, fallback_url=None):
    try:
        with urllib.request.urlopen(url) as response, open(dest_path, 'wb') as out_file:
            file_size = int(response.info().get("Content-Length", -1))
            downloaded = 0
            block_size = 8192

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                percent = downloaded * 100 // file_size if file_size > 0 else 0
                print(f"\r[DL] {percent:3d}% - {dest_path.name}", end="", flush=True)
        print()
        return True
    except Exception as e:
        #----------If it's an SSL error, try again with unverified context----------
        if isinstance(e, ssl.SSLError) or 'CERTIFICATE_VERIFY_FAILED' in str(e):
            print("[WARN] SSL certificate verification failed. Retrying insecurely...")
            try:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(url, context=context) as response, open(dest_path, 'wb') as out_file:
                    file_size = int(response.info().get("Content-Length", -1))
                    downloaded = 0
                    block_size = 8192

                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        percent = downloaded * 100 // file_size if file_size > 0 else 0
                        print(f"\r[DL] {percent:3d}% - {dest_path.name}", end="", flush=True)
                print()
                print("[WARN] Downloaded insecurely. Please fix your Python certificates!")
                return True
            except Exception as e2:
                print(f"[ERROR] Download failed (even insecurely): {e2}")
                if fallback_url:
                    print(f"[INFO] Try downloading manually from: {fallback_url}")
                return False
        print(f"[ERROR] Download failed: {e}")
        if fallback_url:
            print(f"[INFO] Try downloading manually from: {fallback_url}")
        return False


#----------env----------
def verify_env_before_continue():
    try:
        check_required_env_vars()
    except Exception:
        print("[WARN] Could not validate required environment variables")


#----------banner----------
def print_banner():
    print()
    print(r"       ██████╗██╗     ██╗██████╗     ██████╗ ████████╗")
    print(r"      ██╔════╝██║     ██║██╔══██╗    ██╔══██╗╚══██╔══╝")
    print(r"      ██║     ██║     ██║██████╔╝    ██║  ██║   ██║   ")
    print(r"      ██║     ██║     ██║██╔══██╗    ██║  ██║   ██║   ")
    print(r"       ██████╗███████╗██║██████╔╝    ██████╔╝   ██║   ")
    print(r"       ╚═════╝╚══════╝╚═╝╚═════╝     ╚═════╝    ╚═╝   ")
    print(r"             CommonLibSSE-NG Developers Toolkit ")

#----------version----------
def print_version_status():
    global _version_checked, _version_message

    if not _version_checked:
        print()
        msg = f"           Supertron 2025 © -- v{VERSION}"
        color = Fore.LIGHTBLUE_EX

        if not requests:
            _version_message = f"{msg} (requests module missing)"
            _version_checked = True
            print(_version_message)
            return

        try:
            res = requests.get(NEXUS_URL, timeout=5)
            if "<div class=\"stat\">" in res.text:
                match = re.search(r'<div class="stat">([\d\.]+)</div>', res.text)
                if match:
                    online = match.group(1)
                    if online != VERSION:
                        msg += f" (update available: v{online})"
                        color = Fore.RED
                    else:
                        msg += " (up to date)"
                else:
                    msg += " (version check failed)"
                    color = Fore.RED
            else:
                msg += " (parse failed)"
                color = Fore.RED
        except:
            msg += " (network error)"
            color = Fore.RED

        _version_message = msg
        _version_checked = True
        print(_version_message)
    else:
        print(_version_message)



#----------last backup----------
def print_last_backup_info():
    # Check config folder in dev root or fallback for clibdt_backup_config.json
    from modules.config_utils import get_config_directory
    config_dir = get_config_directory()
    backup_config_file = config_dir / "clibdt_backup_config.json"

    best_timestamp = None
    if backup_config_file.exists():
        try:
            import json
            with open(backup_config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                timestamp_str = config_data.get("last_backup_timestamp")
                if timestamp_str:
                    # Try parsing as ISO format
                    try:
                        dt = datetime.fromisoformat(timestamp_str)
                        best_timestamp = dt
                    except Exception:
                        pass
        except Exception:
            pass
    
    if best_timestamp:
        # Convert to local time for display
        if best_timestamp.tzinfo is not None:
            local_time = best_timestamp.astimezone()
            now = datetime.now(local_time.tzinfo)
        else:
            local_time = best_timestamp
            now = datetime.now()
        days_old = (now - best_timestamp).days
        if days_old < 7:
            color = Fore.GREEN
        elif days_old < 30:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        # Always use 24-hour clock
        print(f"Last Backup: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Last Backup: Never")



#----------logger----------

import tempfile, shutil
import io
def atomic_write(path, data, mode='w', encoding='utf-8'):
    dirpath = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(mode=mode, encoding=encoding, dir=dirpath, delete=False) as tf:
        tf.write(data)
        tempname = tf.name
    shutil.move(tempname, path)

class FullTeeLogger(io.TextIOBase):
    def __init__(self, log_path):
        self.terminal_out = sys.stdout
        self.terminal_err = sys.stderr
        try:
            self.logfile = open(log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            self.logfile = None
        self.original_input = __builtins__.input  # Always use the real input
        self._encoding = getattr(self.terminal_out, 'encoding', 'utf-8')

    @property
    def encoding(self):
        return self._encoding

    def write(self, message):
        self.terminal_out.write(message)
        if self.logfile:
            try:
                self.logfile.write(message)
            except Exception:
                pass
        return len(message)

    def flush(self):
        self.terminal_out.flush()
        if self.logfile:
            try:
                self.logfile.flush()
            except Exception:
                pass

    def isatty(self):
        return True

    def writable(self):
        return True

    def readable(self):
        return False

    def seekable(self):
        return False

    def fileno(self):
        return self.terminal_out.fileno() if hasattr(self.terminal_out, 'fileno') else 1

    def input(self, prompt=""):
        self.write(prompt)
        user_input = self.original_input(prompt)
        #----------Do not log user keystrokes----------
        return user_input

    def close(self):
        if self.logfile:
            try:
                self.logfile.write("\n--- LOG CLOSED ---\n")
                self.logfile.close()
            except Exception:
                pass


def setup_full_logger():
    if getattr(sys, 'frozen', False):
        log_path = Path(sys.executable).resolve().parent / "ClibDT.log"
    else:
        log_path = Path(__file__).resolve().parent / "ClibDT.log"

    logger = FullTeeLogger(log_path)
    #----------Do NOT wrap logger with AnsiToWin32: it is not a true file object and will cause linter/runtime errors.----------
    sys.stdout = logger
    sys.stderr = logger
    atexit.register(logger.close)
    print(f"[LOGGING] Output is being saved to: {log_path}")


def safe_input(prompt):
    if NO_PAUSE:
        print(prompt)
        return ''
    return input(prompt)


# -------------------- GUI Imports --------------------
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QPushButton, QFileDialog, QMessageBox, QPlainTextEdit, QTextEdit, QSizePolicy)
import threading
import requests
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor, QFont, QIcon
# If the file is named '@set_environment_variables.py', rename it to 'set_environment_variables.py' and import as:
from modules.set_environment_variables import EnvVarsPanel, EnvSetupWizard
# If Python cannot import from a file starting with '@', rename '@set_environment_variables.py' to 'set_environment_variables.py' and import as:
# from set_environment_variables import EnvVarsPanel

# Remove the EnvVarsPanel class and setx function from this file.
# In the MainWindow class, use EnvVarsPanel from @set_environment_variables.py instead of the local definition.

class MiniTerminal(QTextEdit):
    append_text_signal = pyqtSignal(str)
    append_html_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(120)  # Reduced minimum height for better proportions
        self.setMaximumHeight(300)  # Add maximum height to prevent excessive expansion
        self.append_text_signal.connect(self._append_text)
        self.append_html_signal.connect(self._append_html)
        
        # Set default font with better proportions
        font = QFont("Consolas", 10)  # Slightly smaller font
        self.setFont(font)
        
        # Color mapping for ANSI colors
        self.color_map = {
            'black': '#000000',
            'red': '#e74c3c',
            'green': '#27ae60',
            'yellow': '#f39c12',
            'blue': '#3498db',
            'magenta': '#9b59b6',
            'cyan': '#1abc9c',
            'white': '#ffffff',
            'bright_black': '#7f8c8d',
            'bright_red': '#e74c3c',
            'bright_green': '#2ecc71',
            'bright_yellow': '#f1c40f',
            'bright_blue': '#3498db',
            'bright_magenta': '#9b59b6',
            'bright_cyan': '#1abc9c',
            'bright_white': '#ecf0f1'
        }
        
        # Add line limit to prevent memory issues
        self.max_lines = 1000
        self.current_lines = 0

    def write(self, text):
        """Handle raw text output with color parsing"""
        self.append_text(text)

    def append_text(self, text):
        """Append text with color parsing"""
        if text:
            # Parse ANSI color codes and convert to HTML
            html_text = self._parse_ansi_colors(str(text))
            self.append_html_signal.emit(html_text)

    def _parse_ansi_colors(self, text):
        """Convert ANSI color codes to HTML"""
        import re
        
        # Reset color
        text = text.replace('\033[0m', '</span>')
        text = text.replace('\033[39m', '</span>')
        
        # Foreground colors
        color_patterns = [
            (r'\033\[30m', 'black'),
            (r'\033\[31m', 'red'),
            (r'\033\[32m', 'green'),
            (r'\033\[33m', 'yellow'),
            (r'\033\[34m', 'blue'),
            (r'\033\[35m', 'magenta'),
            (r'\033\[36m', 'cyan'),
            (r'\033\[37m', 'white'),
            (r'\033\[90m', 'bright_black'),
            (r'\033\[91m', 'bright_red'),
            (r'\033\[92m', 'bright_green'),
            (r'\033\[93m', 'bright_yellow'),
            (r'\033\[94m', 'bright_blue'),
            (r'\033\[95m', 'bright_magenta'),
            (r'\033\[96m', 'bright_cyan'),
            (r'\033\[97m', 'bright_white'),
        ]
        
        for pattern, color in color_patterns:
            if color in self.color_map:
                text = re.sub(pattern, f'<span style="color: {self.color_map[color]}">', text)
        
        # Handle bold text
        text = text.replace('\033[1m', '<span style="font-weight: bold;">')
        text = text.replace('\033[22m', '</span>')
        
        # Handle italic text
        text = text.replace('\033[3m', '<span style="font-style: italic;">')
        text = text.replace('\033[23m', '</span>')
        
        # Handle underline
        text = text.replace('\033[4m', '<span style="text-decoration: underline;">')
        text = text.replace('\033[24m', '</span>')
        
        return text

    def _append_text(self, text):
        """Append plain text"""
        if text:
            self.moveCursor(QTextCursor.MoveOperation.End)
            self.insertPlainText(str(text).rstrip("\n") + "\n")
            self._auto_scroll()

    def _append_html(self, html_text):
        """Append HTML formatted text with line limiting"""
        if html_text:
            self.moveCursor(QTextCursor.MoveOperation.End)
            self.insertHtml(html_text.rstrip("\n") + "<br>")
            self.current_lines += 1
            
            # Limit lines to prevent memory issues
            if self.current_lines > self.max_lines:
                self._trim_lines()
            
            self._auto_scroll()

    def _trim_lines(self):
        """Remove old lines to stay within limit"""
        try:
            # Get the document
            doc = self.document()
            if doc.blockCount() > self.max_lines:
                # Remove blocks from the beginning
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, 
                                  doc.blockCount() - self.max_lines)
                cursor.removeSelectedText()
                self.current_lines = doc.blockCount()
        except Exception:
            # Fallback: clear all content if trimming fails
            self.clear()
            self.current_lines = 0

    def _auto_scroll(self):
        """Auto-scroll to bottom with smooth behavior"""
        sb = self.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def flush(self):
        """Flush output buffer"""
        pass

    def clear(self):
        """Clear terminal content"""
        super().clear()
        self.current_lines = 0
        self._auto_scroll()

    def set_verbose_mode(self, enabled=True):
        """Enable/disable verbose output mode"""
        if enabled:
            self.max_lines = 2000  # Allow more lines in verbose mode
        else:
            self.max_lines = 1000  # Normal mode with fewer lines

from modules.install_vstudio_xmake_git import InstallToolsPanel
from modules.create_project import CreateProjectPanel
from modules.quick_launch import QuickLaunchManager
from modules.theme_manager import ThemeManager
from modules.progress_widget import ProgressWidget, ActivityIndicator
from modules.build_project import BuildProjectPanel
from modules.update_project_deps import UpdateProjectDepsPanel
from modules.detach_remove_git import DetachGitPanel
from modules.refresh_project import RefreshProjectPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ClibDT GUI v{VERSION}")
        
        # Set application icon
        icon_path = Path(__file__).parent / "ClibDT_logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Size for comfortable fit on 1080p screen (1920x1080)
        # Account for taskbar (~40px) and window decorations (~30px)
        # Leave some margin from top and sides
        # Center the window on screen
        self.setGeometry(100, 50, 800, 740)
        # Set minimum window size to prevent horizontal scrollbars in menu
        self.setMinimumSize(100, 100)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

        # Initialize progress widget
        self.progress_widget = ProgressWidget(self, "Operation in Progress")
        self.progress_widget.set_theme_manager(self.theme_manager)
        self.progress_widget.completed.connect(self.on_progress_completed)
        self.progress_widget.cancelled.connect(self.on_progress_cancelled)


        self.menu = QListWidget()
        self.menu.setMinimumWidth(160)
        self.menu.setMaximumWidth(250)
        
        # Add a non-selectable divider for required setup
        initial_setup_divider = QListWidgetItem("REQUIRED SETUP")
        initial_setup_divider.setFlags(Qt.ItemFlag.NoItemFlags)
        initial_setup_divider.setForeground(Qt.GlobalColor.white)
        initial_setup_divider.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.menu.addItem(initial_setup_divider)
        
        # Add the first two setup options with emojis
        setup_actions = [
            ("📁 Set Paths", "Set Paths"),
            ("⚙️ Install Tools", "Install Tools")
        ]
        for display_text, action in setup_actions:
            item = QListWidgetItem(display_text, self.menu)
            item.setData(Qt.ItemDataRole.UserRole, action)
        
        # Add a non-selectable divider for Creation
        creation_divider = QListWidgetItem("CREATION")
        creation_divider.setFlags(Qt.ItemFlag.NoItemFlags)
        creation_divider.setForeground(Qt.GlobalColor.white)
        creation_divider.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.menu.addItem(creation_divider)
        
        # Add Create Project, Compile Project, and Git & Updates to Creation section
        creation_actions = [
            ("🚀 Create Project", "Create Project"),
            ("⚡ Compile Project", "Compile Project"),
            ("🔄 Git & Updates", "Git & Updates")
        ]
        for display_text, action in creation_actions:
            item = QListWidgetItem(display_text, self.menu)
            item.setData(Qt.ItemDataRole.UserRole, action)
        
        # Add a non-selectable divider for Additional Tools
        additional_tools_divider = QListWidgetItem("ADDITIONAL TOOLS")
        additional_tools_divider.setFlags(Qt.ItemFlag.NoItemFlags)
        additional_tools_divider.setForeground(Qt.GlobalColor.white)
        additional_tools_divider.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.menu.addItem(additional_tools_divider)
        
        # Add the additional tools with emojis
        additional_actions = [
            ("🔓 Detach Git", "Detach Git"),
            ("💿 Backup Dev Root", "Backup Dev Root"),
            ("🔄 Refresh Project", "Refresh Project"),
            ("📂 Explorer", "Explorer")
        ]
        for display_text, action in additional_actions:
            item = QListWidgetItem(display_text, self.menu)
            item.setData(Qt.ItemDataRole.UserRole, action)
        
        # Add settings to Additional Tools section
        settings_item = QListWidgetItem("⚙️ Settings")
        settings_item.setData(Qt.ItemDataRole.UserRole, "Settings")
        self.menu.addItem(settings_item)
        
        self.stack = QStackedWidget()
        self.terminal = MiniTerminal()
        
        # Initialize quick launch manager
        self.quick_launch_manager = QuickLaunchManager(self, self.terminal.append_text)
        self.stack.addWidget(EnvVarsPanel(status_callback=self.terminal.append_text))         # 0
        self.stack.addWidget(InstallToolsPanel(status_callback=self.terminal.append_text))    # 1
        self.create_project_panel = CreateProjectPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.create_project_panel)                                       # 2
        self.build_project_panel = BuildProjectPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.build_project_panel)                                        # 3
        self.update_deps_panel = UpdateProjectDepsPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.update_deps_panel)                                          # 4
        self.detach_git_panel = DetachGitPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.detach_git_panel)                                           # 5
        from modules.backup_dev_root import BackupDevRootPanel
        self.backup_dev_root_panel = BackupDevRootPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.backup_dev_root_panel)                                      # 6
        self.refresh_project_panel = RefreshProjectPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.refresh_project_panel)                                      # 7
        from modules.settings import SettingsPanel
        self.settings_panel = SettingsPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.settings_panel)                                             # 8
        self.explorer_panel = ExplorerPanel(status_callback=self.terminal.append_text)
        self.stack.addWidget(self.explorer_panel)                                             # 9
        
        # Additional tools pages - create functional panels
        # from modules.backup_dev_root import BackupDevRootPanel # This line is now redundant as it's added above
        
        # Detach Git panel
        # self.stack.addWidget(DetachGitPanel(status_callback=self.terminal.append_text)) # This line is now redundant as it's added above
        
        # Backup Dev Root
        # self.stack.addWidget(BackupDevRootPanel(status_callback=self.terminal.append_text)) # This line is now redundant as it's added above
        
        # Refresh Project
        # self.stack.addWidget(RefreshProjectPanel(status_callback=self.terminal.append_text)) # This line is now redundant as it's added above

        # Create top toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(12)
        # Store pinned tool icon buttons
        self.pinned_tool_buttons = []
        self.pinned_tools = []  # List of file paths
        # Quick Launch toolbar
        self.quick_launch_bar = self.quick_launch_manager.create_quick_launch_bar()
        toolbar_layout.addWidget(self.quick_launch_bar)
        toolbar_layout.addStretch()  # Push controls to the left
        self.toolbar_layout = toolbar_layout  # Save for later use

        # Editor button above tool selection panel (menu)
        from PyQt6.QtWidgets import QVBoxLayout, QPushButton
        editor_path = self.quick_launch_manager.get_editor_path()
        editor_name = Path(editor_path).stem.capitalize() if editor_path else "Editor"
        editor_btn = QPushButton(editor_name)
        editor_btn.setToolTip(f"Launch {editor_name}" + (f"\n{editor_path}" if editor_path else ""))
        editor_btn.setFixedSize(110, 32)
        editor_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c2d91;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 12px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #4b1c7a;
            }
        """)
        def launch_or_pick_editor():
            path = self.quick_launch_manager.get_editor_path()
            if path and Path(path).exists():
                import subprocess, sys
                creationflags = 0
                if sys.platform.startswith("win"):
                    creationflags = subprocess.CREATE_NO_WINDOW
                subprocess.Popen([path], shell=True, creationflags=creationflags)
            else:
                from PyQt6.QtWidgets import QFileDialog
                dlg = QFileDialog(self)
                dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
                dlg.setNameFilter("Executables (*.exe *.bat *.cmd *.sh);;All Files (*.*)")
                if dlg.exec():
                    file_path = dlg.selectedFiles()[0]
                    self.quick_launch_manager.save_editor_path(file_path)
                    editor_btn.setText(Path(file_path).stem.capitalize())
                    editor_btn.setToolTip(f"Launch {Path(file_path).stem.capitalize()}\n{file_path}")
                    import subprocess, sys
                    creationflags = 0
                    if sys.platform.startswith("win"):
                        creationflags = subprocess.CREATE_NO_WINDOW
                    subprocess.Popen([file_path], shell=True, creationflags=creationflags)
        editor_btn.clicked.connect(launch_or_pick_editor)
        editor_panel = QWidget()
        editor_panel_layout = QVBoxLayout(editor_panel)
        editor_panel_layout.setContentsMargins(0, 0, 0, 0)
        editor_panel_layout.setSpacing(0)
        editor_panel_layout.addWidget(self.menu)
        editor_panel_layout.addWidget(editor_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.addLayout(toolbar_layout)
        # Remove previous main_layout.addWidget(editor_container)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.addWidget(editor_panel)  # Add editor+menu as the left panel
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)
        
        # Progress widget (initially hidden)
        main_layout.addWidget(self.progress_widget)
        
        # Terminal toggle button row with better spacing
        terminal_toggle_row = QHBoxLayout()
        terminal_toggle_row.setContentsMargins(12, 8, 12, 8)  # More generous margins
        terminal_toggle_row.setSpacing(12)
        
        # Add stretch to push button to the right
        terminal_toggle_row.addStretch()
        
        # Terminal toggle button with improved styling
        self.terminal_toggle_btn = QPushButton("Show Terminal")
        self.terminal_toggle_btn.setProperty("btnType", "secondary")
        self.terminal_toggle_btn.setFixedSize(130, 28)  # Slightly larger button
        self.terminal_toggle_btn.clicked.connect(self.toggle_terminal)
        terminal_toggle_row.addWidget(self.terminal_toggle_btn)
        
        main_layout.addLayout(terminal_toggle_row)
        
        # Set up terminal with better integration
        self.terminal_visible = False
        self.terminal_height = 180  # Slightly smaller default height
        
        # Create a container for the terminal with proper spacing
        terminal_container = QWidget()
        terminal_container.setObjectName("terminal_container")
        terminal_layout = QVBoxLayout(terminal_container)
        terminal_layout.setContentsMargins(12, 0, 12, 12)  # Top margin 0 to connect with toggle row
        terminal_layout.setSpacing(0)
        terminal_layout.addWidget(self.terminal)
        
        main_layout.addWidget(terminal_container)
        
        # Set size policies for resizable behavior
        self.menu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.terminal.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        terminal_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Initialize terminal container as hidden
        terminal_container.setVisible(False)
        terminal_container.setMaximumHeight(0)
        terminal_container.setMinimumHeight(0)
        
        # Store reference to terminal container
        self.terminal_container = terminal_container

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.menu.currentRowChanged.connect(self.handle_menu_change)
        # Context menu functionality moved to QuickLaunchManager
        self.menu.setCurrentRow(1)  # First selectable item
        
        # Load quick launch items on startup
        self.quick_launch_manager.load_pinned_tools()
        
        # Connect settings panel with theme manager
        self.connect_settings_panel()
        
        # Apply initial theme
        self.apply_theme()

        # Add version update notification
        self.setup_version_notification()

        # Connect project_created signal to all panels with project pickers
        self.create_project_panel.project_created.connect(self.build_project_panel.load_projects)
        if hasattr(self.build_project_panel, 'load_project_names_for_regenerate'):
            self.create_project_panel.project_created.connect(self.build_project_panel.load_project_names_for_regenerate)
        self.create_project_panel.project_created.connect(self.update_deps_panel.load_projects)
        self.create_project_panel.project_created.connect(self.detach_git_panel.load_projects)
        self.create_project_panel.project_created.connect(self.refresh_project_panel.load_projects)


    def setup_version_notification(self):
        """Setup version update notification in tool selection panel"""
        # Create a small notification widget for the menu panel
        from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
        from PyQt6.QtCore import Qt, QTimer
        
        # Create notification widget
        self.version_notification = QLabel()
        self.version_notification.setVisible(False)
        self.version_notification.setMinimumHeight(20)
        self.version_notification.setMaximumHeight(25)
        self.version_notification.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create container widget to add to the menu layout
        self.notification_container = QWidget()
        self.notification_container.setFixedHeight(25)
        self.notification_container.setVisible(False)
        
        layout = QVBoxLayout(self.notification_container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(0)
        layout.addWidget(self.version_notification)
        
        # Don't add to menu initially - only add when notification is shown
        self.notification_menu_item = None
        
        print(f"[DEBUG] Version notification widget created in menu panel")
        
        # Check for updates in background
        self.check_for_updates()
    
    def check_for_updates(self):
        """Check for version updates in background thread"""
        import threading
        import re
        
        def check_update():
            try:
                # Check if version checking is enabled in settings
                if hasattr(self, 'settings_panel') and self.settings_panel:
                    if not self.settings_panel.get_version_check_enabled():
                        print("[DEBUG] Version checking disabled in settings")
                        return
                
                if not requests:
                    print("[DEBUG] No requests module available")
                    return
                
                print(f"[DEBUG] Checking for updates... Local version: {VERSION}")
                res = requests.get(NEXUS_URL, timeout=5)
                print(f"[DEBUG] Got response from Nexus")
                
                if "<div class=\"stat\">" in res.text:
                    print("[DEBUG] Found version div in page")
                    match = re.search(r'<div class="stat">([\d\.]+)</div>', res.text)
                    if match:
                        online_version = match.group(1)
                        print(f"[DEBUG] Online version: {online_version}")
                        if online_version != VERSION:
                            print(f"[DEBUG] Version mismatch! Showing notification")
                            # Show update notification - simple approach like the original
                            self.show_update_notification(online_version)
                        else:
                            print(f"[DEBUG] Versions match - no notification needed")
                    else:
                        print("[DEBUG] Could not parse version from div")
                else:
                    print("[DEBUG] Version div not found in page")
            except Exception as e:
                print(f"[DEBUG] Version check error: {e}")
                # Silently fail - don't show errors for version check
                pass
        
        # Run in background thread
        threading.Thread(target=check_update, daemon=True).start()
    
    def show_update_notification(self, online_version):
        """Show update notification in main window"""
        print(f"[DEBUG] show_update_notification called with online_version: {online_version}")
        
        # Store the online version and call update method directly
        self.pending_online_version = online_version
        
        # Use a simple timer to ensure we're on the main thread
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._update_notification_ui)
    
    def _update_notification_ui(self):
        """Update notification UI on main thread"""
        if not hasattr(self, 'pending_online_version'):
            return
            
        online_version = self.pending_online_version
        print(f"[DEBUG] _update_notification_ui called with version: {online_version}")
        print(f"[DEBUG] Version notification widget: {self.version_notification}")
        print(f"[DEBUG] Notification container: {self.notification_container}")
        
        self.version_notification.setText(f"⬆️ Update Available: v{online_version}")
        print(f"[DEBUG] Notification text set to: {self.version_notification.text()}")
        
        # Style the notification container and label for menu panel (no background)
        self.notification_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                margin: 2px;
            }
        """)
        
        self.version_notification.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-weight: bold;
                font-size: 10px;
                padding: 2px 4px;
                background-color: transparent;
            }
        """)
        
        # Add to menu if not already added
        if self.notification_menu_item is None:
            self.menu.addItem("")
            self.notification_menu_item = self.menu.item(self.menu.count() - 1)
            self.menu.setItemWidget(self.notification_menu_item, self.notification_container)
        
        # Show the notification
        self.notification_container.setVisible(True)
        self.version_notification.setVisible(True)
        print(f"[DEBUG] Notification container visible: {self.notification_container.isVisible()}")
        print(f"[DEBUG] Notification label visible: {self.version_notification.isVisible()}")
        
        # Add click handler to open Nexus page and hide notification
        def on_notification_click(event):
            self.open_nexus_page()
            self.hide_update_notification()
        
        self.notification_container.mousePressEvent = on_notification_click
        self.notification_container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Clear the pending version
        delattr(self, 'pending_online_version')
    
    def hide_update_notification(self):
        """Hide the update notification and remove from menu"""
        if hasattr(self, 'notification_container') and self.notification_container:
            self.notification_container.setVisible(False)
            self.version_notification.setVisible(False)
            
            # Remove from menu if it exists
            if hasattr(self, 'notification_menu_item') and self.notification_menu_item:
                try:
                    # Find the menu item and remove it
                    for i in range(self.menu.count()):
                        if self.menu.item(i) == self.notification_menu_item:
                            self.menu.takeItem(i)
                            break
                    self.notification_menu_item = None
                except Exception:
                    pass

    def open_nexus_page(self):
        """Open Nexus mods page for ClibDT"""
        try:
            import webbrowser
            webbrowser.open(NEXUS_URL)
        except Exception:
            pass

    def switch_theme(self, theme_name):
        if self.theme_manager.set_theme(theme_name):
            self.apply_theme()
    
    def on_theme_changed(self, theme_name):
        """Handle theme change from settings panel"""
        self.apply_theme()
    
    def on_progress_completed(self):
        """Handle progress operation completion"""
        self.terminal.append_text("[OK] Operation completed successfully")
    
    def on_progress_cancelled(self):
        """Handle progress operation cancellation"""
        self.terminal.append_text("[INFO] Operation was cancelled by user")
    
    def start_progress_operation(self, title, operation_func, *args, **kwargs):
        """Start a progress operation with the given function"""
        try:
            # Ensure we're on the main thread for UI updates
            from PyQt6.QtCore import QMetaObject, Qt
            
            # Set title on main thread
            self.progress_widget.title_label.setText(title)
            
            # Start the operation
            self.progress_widget.start_operation(operation_func, *args, **kwargs)
            
        except Exception as e:
            # Log the error and show a user-friendly message
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[MAIN WINDOW PROGRESS ERROR] {error_details}")
            self.terminal.append_text(f"[ERROR] Failed to start progress operation: {e}")
            self.terminal.append_text("The operation could not be started. Please try again.")
    
    def connect_settings_panel(self):
        """Connect settings panel with theme manager for proper integration"""
        if hasattr(self, 'settings_panel') and self.settings_panel:
            # Connect theme change signals from settings panel to theme manager
            self.settings_panel.theme_changed.connect(self.theme_manager.set_theme)
    

    
    def toggle_terminal(self):
        """Toggle terminal visibility with smooth animation"""
        if not hasattr(self, 'terminal'):
            return
            
        self.terminal_visible = not self.terminal_visible
        
        if self.terminal_visible:
            self.terminal_toggle_btn.setText("Hide Terminal")
            self.animate_terminal_show()
        else:
            self.terminal_toggle_btn.setText("Show Terminal")
            self.animate_terminal_hide()
    
    def animate_terminal_show(self):
        """Smoothly show the terminal"""
        try:
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
            
            # Show terminal container first
            self.terminal_container.setVisible(True)
            
            # Animate the terminal container height
            self.terminal_animation = QPropertyAnimation(self.terminal_container, b"maximumHeight")
            self.terminal_animation.setDuration(300)  # Faster, more responsive
            self.terminal_animation.setStartValue(0)
            self.terminal_animation.setEndValue(self.terminal_height)
            self.terminal_animation.setEasingCurve(QEasingCurve.Type.OutCubic)  # Smooth easing
            
            # Also animate the terminal container's minimum height
            self.terminal_animation_min = QPropertyAnimation(self.terminal_container, b"minimumHeight")
            self.terminal_animation_min.setDuration(300)
            self.terminal_animation_min.setStartValue(0)
            self.terminal_animation_min.setEndValue(self.terminal_height)
            self.terminal_animation_min.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # Start both animations
            self.terminal_animation.start()
            self.terminal_animation_min.start()
            
        except Exception as e:
            # Fallback: just show terminal without animation
            self.terminal_container.setVisible(True)
            self.terminal_container.setMaximumHeight(self.terminal_height)
            self.terminal_container.setMinimumHeight(self.terminal_height)
            print(f"Terminal show animation error: {e}")
    
    def animate_terminal_hide(self):
        """Smoothly hide the terminal"""
        try:
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
            
            # Animate the terminal container height to 0
            self.terminal_animation = QPropertyAnimation(self.terminal_container, b"maximumHeight")
            self.terminal_animation.setDuration(250)  # Slightly faster for hiding
            self.terminal_animation.setStartValue(self.terminal_height)
            self.terminal_animation.setEndValue(0)
            self.terminal_animation.setEasingCurve(QEasingCurve.Type.InCubic)  # Smooth easing
            
            # Also animate the minimum height
            self.terminal_animation_min = QPropertyAnimation(self.terminal_container, b"minimumHeight")
            self.terminal_animation_min.setDuration(250)
            self.terminal_animation_min.setStartValue(self.terminal_height)
            self.terminal_animation_min.setEndValue(0)
            self.terminal_animation_min.setEasingCurve(QEasingCurve.Type.InCubic)
            
            # Hide terminal container after animation completes
            self.terminal_animation.finished.connect(self._on_terminal_hide_finished)
            
            # Start both animations
            self.terminal_animation.start()
            self.terminal_animation_min.start()
            
        except Exception as e:
            # Fallback: just hide terminal without animation
            self.terminal_container.setVisible(False)
            self.terminal_container.setMaximumHeight(0)
            self.terminal_container.setMinimumHeight(0)
            print(f"Terminal hide animation error: {e}")
    
    def _on_terminal_hide_finished(self):
        """Handle terminal hide animation completion"""
        self.terminal_container.setVisible(False)
        # Disconnect the signal to prevent memory leaks
        if hasattr(self, 'terminal_animation') and self.terminal_animation:
            try:
                self.terminal_animation.finished.disconnect()
            except Exception:
                pass  # Signal might already be disconnected
    


    def apply_theme(self):
        theme = self.theme_manager.get_theme()
        
        # Apply theme to main window and global styles - LESS AGGRESSIVE
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['window_bg']};
            }}
            QWidget {{
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
            }}
            /* Global fallback styles - only apply if no specific styling exists */
            QLabel:not([objectName*="title"]):not([objectName*="header"]) {{
                background-color: transparent;
                color: {theme['text_primary']};
                font-size: 11px;
                font-weight: normal;
            }}
            QPushButton:not([btnType]) {{
                background-color: {theme['button_bg']};
                color: {theme['text_light']};
                border: 1px solid {theme['button_bg']};
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: normal;
            }}
            QPushButton:not([btnType]):hover {{
                background-color: {theme['button_hover']};
                border-color: {theme['button_hover']};
            }}
            QPushButton:not([btnType]):pressed {{
                background-color: {theme['button_pressed']};
                border-color: {theme['button_pressed']};
            }}
            QLineEdit:not([objectName*="custom"]) {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
                font-weight: normal;
            }}
            QLineEdit:not([objectName*="custom"]):focus {{
                border-color: {theme['input_focus']};
            }}
            QTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }}
            QTextEdit:focus {{
                border-color: {theme['input_focus']};
            }}
            QPlainTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }}
            QPlainTextEdit:focus {{
                border-color: {theme['input_focus']};
            }}
        """)
        
        # Apply theme to menu
        self.menu.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: {theme['text_primary']};
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                margin: 1px 0px;
                font-weight: normal;
            }}
            QListWidget::item:hover {{
                background-color: {theme['bg_secondary']};
            }}
            QListWidget::item:selected {{
                background-color: {theme['menu_item_selected']};
                color: {theme['text_light']};
                font-weight: bold;
            }}
            QListWidget::item:selected:active {{
                background-color: {theme['button_pressed']};
                color: {theme['text_light']};
            }}
            QScrollBar:vertical {{
                background-color: {theme['bg_secondary']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['text_secondary']};
                border-radius: 3px;
                min-height: 16px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['text_primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        

        
        # Apply theme to terminal container and terminal
        self.terminal_container.setStyleSheet(f"""
            QWidget#terminal_container {{
                background-color: {theme['bg_primary']};
                border-top: 1px solid {theme['separator']};
                border-radius: 0px;
            }}
        """)
        
        self.terminal.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['terminal_bg']} !important;
                color: {theme['terminal_text']} !important;
                border: 1px solid {theme['input_border']};
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
                selection-background-color: {theme['menu_item_selected']};
                line-height: 1.2;
            }}
            QTextEdit QScrollBar:vertical {{
                background-color: {theme['scrollbar_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QTextEdit QScrollBar::handle:vertical {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QTextEdit QScrollBar::handle:vertical:hover {{
                background-color: {theme['scrollbar_handle_hover']};
            }}
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Apply theme to terminal toggle button
        self.terminal_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['input_border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {theme['input_border']};
                border-color: {theme['text_primary']};
            }}
            QPushButton:pressed {{
                background-color: {theme['button_pressed']};
                border-color: {theme['button_pressed']};
            }}
        """)
        
        # Apply theme to dropdown (Windows XP style)
        dropdown_style = f"""
            QComboBox {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {theme['button_hover']};
            }}
            QComboBox:focus {{
                border-color: {theme['input_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {theme['text_primary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 3px;
                selection-background-color: {theme['menu_item_selected']};
                selection-color: {theme['text_light']};
            }}
        """
        
        # Apply theme to CreateProjectPanel if it exists
        try:
            create_project_panel = self.stack.widget(2)  # CreateProjectPanel is at index 2
            if create_project_panel and hasattr(create_project_panel, 'set_theme_manager'):
                # Use the set_theme_manager method to properly connect the theme manager
                set_theme_manager_method = getattr(create_project_panel, 'set_theme_manager', None)
                if set_theme_manager_method:
                    set_theme_manager_method(self.theme_manager)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to EnvVarsPanel if it exists
        try:
            env_vars_panel = self.stack.widget(0)  # EnvVarsPanel is at index 0
            if env_vars_panel and hasattr(env_vars_panel, 'apply_theme'):
                # Use getattr to avoid type checking issues
                apply_theme_method = getattr(env_vars_panel, 'apply_theme', None)
                if apply_theme_method:
                    apply_theme_method(theme)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to InstallToolsPanel if it exists
        try:
            install_tools_panel = self.stack.widget(1)  # InstallToolsPanel is at index 1
            if install_tools_panel and hasattr(install_tools_panel, 'apply_theme'):
                # Use getattr to avoid type checking issues
                apply_theme_method = getattr(install_tools_panel, 'apply_theme', None)
                if apply_theme_method:
                    apply_theme_method(theme)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to BuildProjectPanel if it exists
        try:
            build_project_panel = self.stack.widget(3)  # BuildProjectPanel is at index 3
            if build_project_panel and hasattr(build_project_panel, 'apply_theme'):
                # Use getattr to avoid type checking issues
                apply_theme_method = getattr(build_project_panel, 'apply_theme', None)
                if apply_theme_method:
                    apply_theme_method(theme)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to SettingsPanel if it exists
        try:
            settings_panel = self.stack.widget(8)  # SettingsPanel is at index 8
            if settings_panel and hasattr(settings_panel, 'apply_theme'):
                # Use getattr to avoid type checking issues
                apply_theme_method = getattr(settings_panel, 'apply_theme', None)
                if apply_theme_method:
                    apply_theme_method(theme)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to UpdateProjectDepsPanel if it exists
        try:
            update_deps_panel = self.stack.widget(4)  # UpdateProjectDepsPanel is at index 4
            if update_deps_panel and hasattr(update_deps_panel, 'apply_theme'):
                # Use getattr to avoid type checking issues
                apply_theme_method = getattr(update_deps_panel, 'apply_theme', None)
                if apply_theme_method:
                    apply_theme_method(theme)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to BackupDevRootPanel if it exists
        try:
            backup_dev_root_panel = self.stack.widget(6)  # BackupDevRootPanel is at index 6
            if backup_dev_root_panel and hasattr(backup_dev_root_panel, 'set_theme_manager'):
                # Use the set_theme_manager method to properly connect the theme manager
                set_theme_manager_method = getattr(backup_dev_root_panel, 'set_theme_manager', None)
                if set_theme_manager_method:
                    set_theme_manager_method(self.theme_manager)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to DetachGitPanel if it exists
        try:
            detach_git_panel = self.stack.widget(5)  # DetachGitPanel is at index 5
            if detach_git_panel and hasattr(detach_git_panel, 'set_theme_manager'):
                # Use the set_theme_manager method to properly connect the theme manager
                set_theme_manager_method = getattr(detach_git_panel, 'set_theme_manager', None)
                if set_theme_manager_method:
                    set_theme_manager_method(self.theme_manager)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to RefreshProjectPanel if it exists
        try:
            refresh_project_panel = self.stack.widget(7)  # RefreshProjectPanel is at index 7
            if refresh_project_panel and hasattr(refresh_project_panel, 'set_theme_manager'):
                # Use the set_theme_manager method to properly connect the theme manager
                set_theme_manager_method = getattr(refresh_project_panel, 'set_theme_manager', None)
                if set_theme_manager_method:
                    set_theme_manager_method(self.theme_manager)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Apply theme to ExplorerPanel if it exists
        try:
            explorer_panel = self.stack.widget(9)  # ExplorerPanel is at index 9
            if explorer_panel and hasattr(explorer_panel, 'set_theme_manager'):
                # Use the set_theme_manager method to properly connect the theme manager
                set_theme_manager_method = getattr(explorer_panel, 'set_theme_manager', None)
                if set_theme_manager_method:
                    set_theme_manager_method(self.theme_manager)
        except Exception:
            pass  # Panel might not be loaded yet
        
        # Update version notification styling if it exists and is visible
        if hasattr(self, 'notification_container') and hasattr(self, 'version_notification'):
            if self.notification_container.isVisible():
                # Update notification styling to match current theme for menu panel (no background)
                self.notification_container.setStyleSheet(f"""
                    QWidget {{
                        background-color: transparent;
                        border: none;
                        margin: 2px;
                    }}
                """)
                
                self.version_notification.setStyleSheet(f"""
                    QLabel {{
                        color: {theme['success_color']};
                        font-weight: bold;
                        font-size: 10px;
                        padding: 2px 4px;
                        background-color: transparent;
                    }}
                """)
                print(f"[DEBUG] Version notification theme updated - visible: {self.notification_container.isVisible()}")
            else:
                print(f"[DEBUG] Version notification exists but not visible")
        else:
            print(f"[DEBUG] Version notification widgets not found")
        
        # Update menu divider colors
        for i in range(self.menu.count()):
            item = self.menu.item(i)
            if item and item.flags() == Qt.ItemFlag.NoItemFlags:  # Divider items
                item.setForeground(Qt.GlobalColor.white if self.theme_manager.current_theme == 'dark' else Qt.GlobalColor.black)



    def handle_menu_change(self, row):
        # Menu structure:
        # Row 0: "REQUIRED SETUP" (divider)
        # Row 1: "📁 Set Paths" → Stack index 0
        # Row 2: "⚙️ Install Tools" → Stack index 1  
        # Row 3: "CREATION" (divider)
        # Row 4: "🚀 Create Project" → Stack index 2
        # Row 5: "⚡ Compile Project" → Stack index 3
        # Row 6: "🔄 Git & Updates" → Stack index 4
        # Row 7: "ADDITIONAL TOOLS" (divider)
        # Row 8: "🔓 Detach Git" → Stack index 5
        # Row 9: "💿 Backup Dev Root" → Stack index 6
        # Row 10: "🔄 Refresh Project" → Stack index 7
        # Row 11: "📂 Explorer" → Stack index 9
        # Row 12: "⚙️ Settings" → Stack index 8 (Settings panel)
        
        # Handle dividers
        if row in (0, 3, 7):
            # Move to first selectable after the divider
            if row == 0:
                self.menu.setCurrentRow(1)
            elif row == 3:
                self.menu.setCurrentRow(4)
            elif row == 7:
                self.menu.setCurrentRow(8)
            return
        
        # Check if this is the settings item
        item = self.menu.item(row)
        if item and item.data(Qt.ItemDataRole.UserRole) == "Settings":
            self.stack.setCurrentIndex(8)  # Settings panel is at index 8
            return
        
        # Check if this is the explorer item
        if item and item.data(Qt.ItemDataRole.UserRole) == "Explorer":
            self.stack.setCurrentIndex(9)  # Explorer panel is at index 9
            return
        
        # Map menu rows to stack indices
        if row < 3:
            # Setup items (rows 1-2)
            self.stack.setCurrentIndex(row - 1)
        elif row == 4:
            # Create Project (row 4)
            self.stack.setCurrentIndex(2)
        elif row == 5:
            # Compile Project (row 5)
            self.stack.setCurrentIndex(3)
        elif row == 6:
            # Git & Updates (row 6)
            self.stack.setCurrentIndex(4)
        elif row == 8:
            # Detach Git (row 8)
            self.stack.setCurrentIndex(5)
        elif row == 9:
            # Backup Dev Root (row 9)
            self.stack.setCurrentIndex(6)
        elif row == 10:
            # Refresh Project (row 10)
            self.stack.setCurrentIndex(7)

    def pin_tool_as_icon(self, file_path):
        """Add a pinned tool icon button to the toolbar for quick launching."""
        # Avoid duplicates
        if file_path in self.pinned_tools:
            return
        self.pinned_tools.append(file_path)
        btn = QPushButton()
        btn.setToolTip(str(Path(file_path).name))
        # Try to set an icon based on file type
        ext = Path(file_path).suffix.lower()
        if ext == '.exe':
            btn.setIcon(QIcon(file_path))
        elif ext == '.py':
            btn.setIcon(QIcon.fromTheme('application-python'))
        elif ext == '.bat' or ext == '.cmd':
            btn.setIcon(QIcon.fromTheme('utilities-terminal'))
        elif ext == '.msi':
            btn.setIcon(QIcon.fromTheme('application-x-msi'))
        else:
            btn.setIcon(QIcon.fromTheme('application-x-executable'))
        btn.setFixedSize(32, 32)
        btn.setIconSize(btn.size() * 0.8)
        btn.clicked.connect(lambda: self.quick_launch_manager.launch_quick_launch_item(file_path))
        self.toolbar_layout.insertWidget(0, btn)  # Insert before quick launch dropdown
        self.pinned_tool_buttons.append(btn)
        # (Optional) Save pinned tools to config for persistence
        # TODO: Save self.pinned_tools to a config file


# -------------------- Main Entry Point --------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Set global application icon
    icon_path = Path(__file__).parent / "ClibDT_logo.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# The following CLI menu code is now bypassed by the GUI above.
# To restore CLI, comment out the GUI block and uncomment below.
# try:
#     setup_full_logger()
# except Exception as logerr:
#     import traceback
#     print("[FATAL] Failed to set up logger:", file=sys.__stderr__)
#     traceback.print_exc(file=sys.__stderr__)
#     input("Press Enter to exit...")
#     raise SystemExit(1)
#
# try:
#     if os.name == "nt":
#         import shutil
#         cols, lines = shutil.get_terminal_size(fallback=(120, 30))
#         new_lines = int(lines * 1.2)
#         os.system(f"mode con: lines={new_lines} cols={cols}")
# except Exception:
#     pass
# def main_menu():
#     ...
# try:
#     main_menu()
# except Exception:
#     import traceback
#     print("[FATAL] Unhandled exception occurred:")
#     traceback.print_exc()
#     input("Press Enter to exit...")



