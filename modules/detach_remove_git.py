import os
import shutil
import json
from pathlib import Path
from colorama import init, Fore, Style
import stat

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def confirm(prompt, default="n"):
    resp = input(Style.RESET_ALL + prompt).strip().lower()
    if resp == "m":
        return "m"
    if not resp:
        return default.lower()
    return resp

def force_rmtree(path, retries=3):
    import time
    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=on_rm_error)
            return True
        except Exception as e:
            if attempt < retries - 1:
                cprint(f"[WARN] Could not delete {path} (attempt {attempt+1}/{retries}): {e}", Fore.YELLOW)
                cprint("[INFO] Retrying after making files writable...", Fore.LIGHTBLACK_EX)
                make_all_writable(path)
                time.sleep(1)
            else:
                cprint(f"[ERROR] Failed to delete {path} after {retries} attempts: {e}", Fore.RED)
                return False

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        cprint(f"[ERROR] Could not forcibly delete {path}: {e}", Fore.RED)

def make_all_writable(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), stat.S_IWRITE)
            except Exception:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IWRITE)
            except Exception:
                pass

def run_detach_remove_git():
    cprint("\n[DETACH GIT] Remove Git History from Project", Fore.CYAN + Style.BRIGHT)
    cprint("[INFO] Current folder:", Fore.YELLOW)
    cprint(f"  {os.getcwd()}\n", Fore.LIGHTBLACK_EX)

    git_folder = Path(".git")
    if not git_folder.exists() or not git_folder.is_dir():
        cprint("[OK] No .git folder found. Nothing to remove.", Fore.GREEN)
        input(Style.RESET_ALL + "Press Enter to return to the main menu...")
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return

    cprint("[CAUTION] This will permanently remove all Git history from this project!", Fore.RED + Style.BRIGHT)
    cprint("[WARNING] This cannot be undone.", Fore.RED)
    cprint("[INFO] Enter M to return to the main menu.", Fore.LIGHTBLACK_EX)
    print()

    resp = confirm("Delete .git folder and detach from Git? (Y/N): ", default="n")
    if resp == "m":
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    if resp != "y":
        cprint("[INFO] Kept existing .git folder. No changes made.", Fore.LIGHTBLACK_EX)
        input(Style.RESET_ALL + "Press Enter to return to the main menu...")
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return

    try:
        #----------Robust force delete----------
        if force_rmtree(git_folder):
            if git_folder.exists():
                cprint("[ERROR] Failed to remove .git folder. Check permissions and try again.", Fore.RED)
            else:
                cprint("[OK] .git folder removed successfully. Project is now detached from Git.", Fore.GREEN)
        else:
            cprint("[ERROR] Could not remove .git folder after multiple attempts.", Fore.RED)
    except Exception as e:
        cprint(f"[ERROR] Exception while removing .git: {e}", Fore.RED)

    print()
    input(Style.RESET_ALL + "Press Enter to return to the main menu...")
    cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)

# GUI Panel
from modules.utilities.common import VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QCheckBox, QProgressBar, QFrame, QGroupBox, QComboBox, QLineEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

class DetachGitThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, project_path=None, status_callback=None):
        super().__init__()
        self.project_path = project_path
        self.status_callback = status_callback
    
    def run(self):
        try:
            def status(msg):
                self.progress_signal.emit(msg)
                if self.status_callback:
                    self.status_callback(msg)
            
            if not self.project_path:
                self.finished_signal.emit(False, "No project path provided.")
                return
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(str(self.project_path))
            status(f"[INFO] Changed to project directory: {self.project_path}")
            
            git_folder = Path(".git")
            if not git_folder.exists() or not git_folder.is_dir():
                status("[OK] No .git folder found. Nothing to remove.")
                self.finished_signal.emit(True, "No .git folder found. Nothing to remove.")
                return
            
            status("[INFO] Found .git folder. Proceeding with removal...")
            
            # Force remove the .git folder
            if force_rmtree(git_folder):
                if git_folder.exists():
                    status("[ERROR] Failed to remove .git folder. Check permissions and try again.")
                    self.finished_signal.emit(False, "Failed to remove .git folder.")
                else:
                    status("[OK] .git folder removed successfully. Project is now detached from Git.")
                    self.finished_signal.emit(True, "Git history removed successfully!")
            else:
                status("[ERROR] Could not remove .git folder after multiple attempts.")
                self.finished_signal.emit(False, "Could not remove .git folder after multiple attempts.")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Detach Git failed with error: {e}")
        finally:
            # Restore original directory
            try:
                os.chdir(original_cwd)
            except:
                pass

class DetachGitPanel(QWidget):
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.detach_thread = None
        self.theme_manager = theme_manager
        self.selected_project_path = None
        # Load user preferences
        self.load_preferences()
        
        # Main layout with proper spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Detach Git")
        title.setObjectName("main_title")
        title_row.addWidget(title)
        
        # Add divider line
        title_divider = QLabel()
        title_divider.setObjectName("title_divider")
        title_divider.setFixedHeight(2)
        title_divider.setMinimumWidth(120)
        title_row.addWidget(title_divider)
        
        title_row.addStretch()
        layout.addLayout(title_row)
        
        # Description
        desc = QLabel("Remove Git history from a project to detach it from version control.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        

        
        # Project Selection
        project_row = QHBoxLayout()
        project_row.setSpacing(8)
        project_row.setContentsMargins(0, 0, 0, 0)
        
        project_label = QLabel("Project:")
        project_label.setObjectName("project_label")
        project_label.setFixedWidth(60)
        project_row.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setEditable(False)
        self.project_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.project_combo.setObjectName("project_combo")
        self.project_combo.setToolTip("Select the project to detach from Git")
        self.project_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.project_combo.setMinimumWidth(200)
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        project_row.addWidget(self.project_combo)
        layout.addLayout(project_row)
        

        
        # Git status display
        self.git_status_label = QLabel("Select a project to check Git status...")
        self.git_status_label.setObjectName("git_status_label")
        layout.addWidget(self.git_status_label)
        
        # Warning note
        warning = QLabel("⚠️  WARNING: This action will permanently remove all Git history and cannot be undone!")
        warning.setObjectName("warning_label")
        layout.addWidget(warning)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("detach_progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%p% %")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Button row with proper spacing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Detach Git button
        self.detach_btn = QPushButton("Detach Git")
        self.detach_btn.setProperty("btnType", "uninstall")
        self.detach_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.detach_btn.setFixedHeight(32)
        self.detach_btn.clicked.connect(self.start_detach)
        self.detach_btn.setEnabled(False)
        btn_row.addWidget(self.detach_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("btnType", "secondary")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setFixedHeight(32)
        self.stop_btn.clicked.connect(self.stop_detach)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)
        
        layout.addLayout(btn_row)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect to theme manager if provided
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def showEvent(self, event):
        """Override showEvent to apply theme when panel becomes visible"""
        super().showEvent(event)
        # Ensure we're connected to the main window's theme manager
        try:
            main_window = self.window()
            theme_manager = getattr(main_window, 'theme_manager', None)
            if theme_manager:
                self.set_theme_manager(theme_manager)
        except Exception:
            pass
        # Apply theme when panel is shown
        self.apply_theme()
        
        # Load projects when panel is first shown (lazy loading)
        if not hasattr(self, '_projects_loaded'):
            self.load_projects()
            self._projects_loaded = True
    
    def load_projects(self):
        """Load available projects from dev_root/projects folder"""
        try:
            # Import the new project detection module
            try:
                from modules.refresh_project import is_valid_clib_project
            except ImportError:
                # Fallback to old xmake.lua detection if module not available
                def is_valid_clib_project(project_path):
                    return (project_path / "xmake.lua").exists()
            
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if not dev_root:
                self.project_combo.addItem("No dev root found")
                return
            
            projects_path = Path(dev_root) / "projects"
            if not projects_path.exists():
                self.project_combo.addItem("No projects folder found")
                return
            
            projects = []
            for item in projects_path.iterdir():
                if item.is_dir() and is_valid_clib_project(item):
                    projects.append(item.name)
            
            if not projects:
                self.project_combo.addItem("No valid ClibDT projects found")
                return
            
            projects.sort()
            self.project_combo.addItems(projects)
            
            # Select last used project if available
            if hasattr(self, 'last_project') and self.last_project in projects:
                self.project_combo.setCurrentText(self.last_project)
            elif projects:
                self.project_combo.setCurrentText(projects[0])
                
        except Exception as e:
            self.project_combo.addItem(f"Error loading projects: {e}")
    
    def on_project_changed(self, project_name):
        """Handle project selection change"""
        if project_name and not project_name.startswith("No ") and not project_name.startswith("Error"):
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if dev_root:
                self.selected_project_path = Path(dev_root) / "projects" / project_name
                self.last_project = project_name
                self.save_preferences()
                self.check_git_status()
    
    def check_git_status(self):
        """Check if the selected project has a .git folder"""
        if not self.selected_project_path:
            self.git_status_label.setText("Select a project to check Git status...")
            self.detach_btn.setEnabled(False)
            return
        
        git_folder = self.selected_project_path / ".git"
        if git_folder.exists() and git_folder.is_dir():
            self.git_status_label.setText("✅ Git repository found. Ready to detach.")
            self.detach_btn.setEnabled(True)
        else:
            self.git_status_label.setText("❌ No Git repository found. Nothing to detach.")
            self.detach_btn.setEnabled(False)

    def load_preferences(self):
        """Load user preferences from a simple config file"""
        self.last_project = None
        
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_detach_prefs.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    prefs = json.load(f)
                    self.last_project = prefs.get('last_project', None)
        except Exception:
            # If loading fails, use defaults
            pass

    def save_preferences(self):
        """Save user preferences to a simple config file"""
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_detach_prefs.json"
            config_data = {
                'last_project': self.last_project,
                'clibdt_version': VERSION
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            # If saving fails, just continue
            pass
    
    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)
    
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
                'error_color': '#e74c3c',
                'warning_color': '#f39c12',
                'info_color': '#3498db'
            }
        
        # Ultra-compact styling that overrides ALL global styling
        self.setStyleSheet(f"""
            /* Nuclear option: Override ALL global styling with ultra-compact layout */
            DetachGitPanel,
            DetachGitPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            DetachGitPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Main title - largest and most prominent */
            DetachGitPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
            }}
            
            /* Color-coded section titles */
            DetachGitPanel QLabel#custom_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['info_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            DetachGitPanel QLabel#success_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['success_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            DetachGitPanel QLabel#warning_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['warning_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            DetachGitPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            /* Section descriptions */
            DetachGitPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            DetachGitPanel QLabel#warning_label {{
                color: {theme['warning_color']} !important;
                font-size: 10px !important;
                font-weight: normal !important;
            }}
            
            DetachGitPanel QLabel#git_status_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                padding: 4px 0px !important;
            }}
            
            /* Divider lines */
            DetachGitPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            

            
            /* ComboBox styling - responsive resizing */
            DetachGitPanel QComboBox,
            DetachGitPanel QComboBox:hover,
            DetachGitPanel QComboBox:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 120px !important;
            }}
            
            DetachGitPanel QComboBox:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            DetachGitPanel QComboBox:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            DetachGitPanel QComboBox::drop-down {{
                border: none !important;
                width: 24px !important;
            }}
            
            DetachGitPanel QComboBox::down-arrow {{
                image: none !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid {theme['text_primary']} !important;
                margin-right: 6px !important;
            }}
            
            DetachGitPanel QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                selection-background-color: {theme['button_bg']} !important;
                selection-color: {theme['text_light']} !important;
                padding: 4px !important;
            }}
            
            /* Progress Bar styling */
            DetachGitPanel QProgressBar#detach_progress_bar {{
                border: 1px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                text-align: center !important;
                font-size: 11px !important;
                color: {theme['text_primary']} !important;
                background-color: {theme['input_bg']} !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            DetachGitPanel QProgressBar#detach_progress_bar::chunk {{
                background-color: {theme['button_bg']} !important;
                border-radius: 4px !important;
            }}
            
            /* Base button styling for all states */
            DetachGitPanel QPushButton,
            DetachGitPanel QPushButton:hover,
            DetachGitPanel QPushButton:pressed,
            DetachGitPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            /* General disabled button styling (applies to ALL button types) */
            DetachGitPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Uninstall/Danger buttons - Red theme with bright hover effects */
            DetachGitPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            DetachGitPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            DetachGitPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
            
            /* Secondary utility buttons */
            DetachGitPanel QPushButton[btnType="secondary"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268) !important;
                color: {theme['text_light']} !important;
                border: 1px solid #5a6268 !important;
                padding: 6px 12px !important;
            }}
            
            DetachGitPanel QPushButton[btnType="secondary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:0.5 #95a5a6, stop:1 #7f8c8d) !important;
                border: 2px solid #d5dbdb !important;
                color: #ffffff !important;
            }}
            
            DetachGitPanel QPushButton[btnType="secondary"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #495057) !important;
                border: 1px solid #495057 !important;
            }}
        """)
    
    def start_detach(self):
        """Start Git detach operation"""
        if not self.selected_project_path:
            self.status("[ERROR] Please select a project to detach from Git.")
            return
        
        self.detach_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        self.status("=== Starting Git Detach ===")
        self.status(f"Project: {Path(self.selected_project_path).name}")
        self.status("")
        
        # Start detach thread
        self.detach_thread = DetachGitThread(
            project_path=str(self.selected_project_path),
            status_callback=self.status
        )
        self.detach_thread.progress_signal.connect(self.status)
        self.detach_thread.finished_signal.connect(self.detach_finished)
        self.detach_thread.start()
    
    def stop_detach(self):
        """Stop Git detach operation"""
        if self.detach_thread and self.detach_thread.isRunning():
            self.detach_thread.terminate()
            self.detach_thread.wait()
            self.status("[INFO] Git detach stopped by user.")
            self.detach_finished(False, "Git detach stopped by user.")
    
    def detach_finished(self, success, message):
        """Handle Git detach completion"""
        self.detach_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status(f"[SUCCESS] {message}")
            # Refresh Git status
            self.check_git_status()
        else:
            self.status(f"[ERROR] {message}")

if __name__ == "__main__":
    run_detach_remove_git()
