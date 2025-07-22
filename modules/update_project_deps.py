import os
import subprocess
import shutil
from pathlib import Path
from colorama import init, Fore, Style
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
import json

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_yesno(message, default="n"):
    val = input(f"{message} ").strip().lower()
    if val == "m":
        return "M"
    return val if val else default.lower()

def run_with_progress(cmd, description, console, show_progress=True):
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=None)
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                progress.update(task, completed=True)
                return result
            except subprocess.CalledProcessError as e:
                progress.update(task, completed=True)
                return None
    else:
        cprint(f"  {description}", Fore.CYAN)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return None

def update_project_deps():
    console = Console()
    
    #----------dev root----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] Missing environment variable: XSE_CLIBDT_DEVROOT", Fore.RED)
        input("\nPress Enter to return...")
        return

    dev_root_path = Path(dev_root).resolve()
    project_root = Path.cwd().resolve()

    if not str(project_root).startswith(str(dev_root_path)):
        cprint("[ERROR] This script must be run inside a subfolder of your dev projects root:", Fore.RED)
        cprint(f"        {dev_root_path}", Fore.YELLOW)
        input("\nPress Enter to return...")
        return

    # Check for valid project using new detection method
    try:
        from modules.refresh_project import is_valid_clib_project
    except ImportError:
        # Fallback to old xmake.lua detection if module not available
        def is_valid_clib_project(project_path):
            return (project_path / "xmake.lua").exists()
    
    if not is_valid_clib_project(project_root):
        cprint("[ERROR] This script must be run from a valid ClibDT project folder", Fore.RED)
        input("\nPress Enter to return...")
        return

    cprint("[OK] Project folder confirmed.", Fore.GREEN)
    print()

    #----------xmake repo --update----------
    cprint("=== UPDATING PACKAGE INDEX ===", Fore.CYAN + Style.BRIGHT)
    do_repo = prompt_yesno("Update xmake's package repository index? [Y/n]: ", "y")
    if do_repo == "m":
        return
    if do_repo == "y":
        result = run_with_progress(
            ["xmake", "repo", "--update"],
            "📦 Updating xmake package index...",
            console,
            show_progress=True
        )

        if result and result.returncode == 0:
            cprint("[OK] Package index updated successfully.", Fore.GREEN)
        elif result and "refusing to merge unrelated histories" in result.stderr:
            cprint("[ERROR] Detected unrelated Git histories in xmake-repo.", Fore.RED)
            xmake_repo_path = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.xmake"),
                "repos", "xmake-repo"
            )
            if os.path.exists(xmake_repo_path):
                shutil.rmtree(xmake_repo_path)
                cprint(f"[INFO] Removed corrupted repo: {xmake_repo_path}", Fore.YELLOW)

            cprint("[INFO] Retrying package index update...", Fore.CYAN)
            retry = run_with_progress(
                ["xmake", "repo", "--update"],
                "📦 Retrying package index update...",
                console,
                show_progress=True
            )
            if retry and retry.returncode == 0:
                cprint("[OK] Package index updated after fixing repo.", Fore.GREEN)
            else:
                cprint("[ERROR] Retry failed. Please investigate manually.", Fore.RED)
        else:
            cprint("[ERROR] Failed to update package index.", Fore.RED)
            if result and result.stderr:
                cprint(f"[DEBUG] Error output: {result.stderr}", Fore.LIGHTBLACK_EX)
    else:
        cprint("[INFO] Skipped updating package index.", Fore.LIGHTBLACK_EX)

    #----------xmake require --upgrade----------
    print()
    cprint("=== UPGRADING PROJECT DEPENDENCIES ===", Fore.YELLOW + Style.BRIGHT)
    cprint("   This will update all required libraries to their latest versions.", Fore.LIGHTYELLOW_EX)
    cprint("   Warning: This may change library versions and could affect compatibility.", Fore.LIGHTYELLOW_EX)
    do_upgrade = prompt_yesno("Upgrade all project dependencies to latest versions? [Y/n]: ", "n")
    if do_upgrade == "m":
        return
    if do_upgrade == "y":
        result = run_with_progress(
            ["xmake", "require", "--upgrade"],
            "⬆️  Upgrading project dependencies...",
            console,
            show_progress=True
        )
        if result and result.returncode == 0:
            cprint("[OK] Dependencies upgraded successfully.", Fore.GREEN)
        else:
            cprint("[ERROR] Failed to upgrade dependencies.", Fore.RED)
            if result and result.stderr:
                cprint(f"[DEBUG] Error output: {result.stderr}", Fore.LIGHTBLACK_EX)
    else:
        cprint("[INFO] Skipped upgrading dependencies.", Fore.LIGHTBLACK_EX)

    print()
    cprint("✅ All operations completed!", Fore.GREEN)
    input("\nPress Enter to return...")

# GUI Panel
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QCheckBox, QProgressBar, QFrame, QGroupBox, QComboBox, QLineEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

class UpdateThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, update_packages=True, upgrade_deps=True, project_path=None, status_callback=None):
        super().__init__()
        self.update_packages = update_packages
        self.upgrade_deps = upgrade_deps
        self.project_path = project_path
        self.status_callback = status_callback
    
    def run(self):
        try:
            def status(msg):
                self.progress_signal.emit(msg)
                if self.status_callback:
                    self.status_callback(msg)
            
            # Check for valid project using new detection method
            try:
                from modules.refresh_project import is_valid_clib_project
            except ImportError:
                # Fallback to old xmake.lua detection if module not available
                def is_valid_clib_project(project_path):
                    return (project_path / "xmake.lua").exists()
            
            if not self.project_path or not is_valid_clib_project(Path(self.project_path)):
                self.finished_signal.emit(False, "No valid ClibDT project found in selected project directory.")
                return
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(self.project_path)
            status(f"[INFO] Changed to project directory: {self.project_path}")
            
            # Update package index if requested
            if self.update_packages:
                status("📦 Updating xmake package index...")
                result = subprocess.run(["xmake", "repo", "--update"], capture_output=True, text=True)
                if result.returncode == 0:
                    status("[OK] Package index updated successfully.")
                else:
                    status("[ERROR] Failed to update package index.")
                    if result.stderr:
                        status(f"[DEBUG] Error output: {result.stderr}")
            
            # Upgrade dependencies if requested
            if self.upgrade_deps:
                status("⬆️ Upgrading project dependencies...")
                result = subprocess.run(["xmake", "require", "--upgrade"], capture_output=True, text=True)
                if result.returncode == 0:
                    status("[OK] Dependencies upgraded successfully.")
                    self.finished_signal.emit(True, "Dependencies updated successfully!")
                else:
                    status("[ERROR] Failed to upgrade dependencies.")
                    if result.stderr:
                        status(f"[DEBUG] Error output: {result.stderr}")
                    self.finished_signal.emit(False, "Failed to upgrade dependencies.")
            else:
                self.finished_signal.emit(True, "Package index updated successfully!")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Update failed with error: {e}")
        finally:
            # Restore original directory
            try:
                os.chdir(original_cwd)
            except:
                pass

class UpdateProjectDepsPanel(QWidget):
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.update_thread = None
        self.commit_thread = None
        self.theme_manager = theme_manager
        self.selected_project_path = None
        # Load user preferences
        self.load_preferences()
        
        # Main layout with proper spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Git & Updates")
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
        desc = QLabel("Manage Git commits and update project dependencies.")
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
        self.project_combo.setToolTip("Select the project to update dependencies for")
        self.project_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.project_combo.setMinimumWidth(200)
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        project_row.addWidget(self.project_combo)
        layout.addLayout(project_row)
        
        # Git Commit Section with header line
        git_title_row = QHBoxLayout()
        git_title_row.setSpacing(8)
        git_title_row.setContentsMargins(0, 0, 0, 0)
        
        git_title = QLabel("Git Commit")
        git_title.setObjectName("success_title")  # Green color for action tools
        git_title_row.addWidget(git_title)
        
        # Add divider line
        git_title_divider = QLabel()
        git_title_divider.setObjectName("success_title_divider")
        git_title_divider.setFixedHeight(1)
        git_title_divider.setMinimumWidth(100)
        git_title_row.addWidget(git_title_divider)
        
        git_title_row.addStretch()
        layout.addLayout(git_title_row)
        
        # Commit message input
        commit_row = QHBoxLayout()
        commit_row.setSpacing(8)
        commit_row.setContentsMargins(0, 0, 0, 0)
        
        commit_label = QLabel("Message:")
        commit_label.setObjectName("commit_label")
        commit_label.setFixedWidth(60)
        commit_row.addWidget(commit_label)
        
        self.commit_msg_edit = QLineEdit("Commit")
        self.commit_msg_edit.setPlaceholderText("Enter commit message...")
        self.commit_msg_edit.setToolTip("Enter a descriptive commit message")
        self.commit_msg_edit.setObjectName("commit_msg_edit")
        self.commit_msg_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.commit_msg_edit.setMinimumWidth(200)
        commit_row.addWidget(self.commit_msg_edit)
        layout.addLayout(commit_row)
        
        # Git options
        self.init_repo_cb = QCheckBox("Initialize repository if needed")
        self.init_repo_cb.setChecked(True)
        self.init_repo_cb.setToolTip("Automatically initialize git repository if not already present")
        self.init_repo_cb.setObjectName("init_repo_cb")
        layout.addWidget(self.init_repo_cb)
        
        self.stage_all_cb = QCheckBox("Stage all changes")
        self.stage_all_cb.setChecked(True)
        self.stage_all_cb.setToolTip("Stage all modified files before committing")
        self.stage_all_cb.setObjectName("stage_all_cb")
        layout.addWidget(self.stage_all_cb)
        
        # Git Commit button
        git_btn_row = QHBoxLayout()
        git_btn_row.setSpacing(8)
        git_btn_row.setContentsMargins(0, 0, 0, 0)
        
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.setProperty("btnType", "success")
        self.commit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.commit_btn.setFixedHeight(32)
        self.commit_btn.clicked.connect(self.start_commit)
        self.commit_btn.setToolTip("Stage and commit all changes")
        git_btn_row.addWidget(self.commit_btn)
        
        layout.addLayout(git_btn_row)
        
        # Update Dependencies Section with header line
        update_title_row = QHBoxLayout()
        update_title_row.setSpacing(8)
        update_title_row.setContentsMargins(0, 0, 0, 0)
        
        update_title = QLabel("Update Dependencies")
        update_title.setObjectName("custom_title")  # Blue color for utility tools
        update_title_row.addWidget(update_title)
        
        # Add divider line
        update_title_divider = QLabel()
        update_title_divider.setObjectName("custom_title_divider")
        update_title_divider.setFixedHeight(1)
        update_title_divider.setMinimumWidth(100)
        update_title_row.addWidget(update_title_divider)
        
        update_title_row.addStretch()
        layout.addLayout(update_title_row)
        
        # Update Options
        self.update_packages_cb = QCheckBox("Update xmake package index")
        self.update_packages_cb.setObjectName("update_packages_cb")
        self.update_packages_cb.setChecked(self.last_update_packages)
        self.update_packages_cb.setToolTip("Updates the xmake package repository index to get latest package information")
        self.update_packages_cb.toggled.connect(self.save_preferences)
        layout.addWidget(self.update_packages_cb)
        
        self.upgrade_deps_cb = QCheckBox("Upgrade project dependencies")
        self.upgrade_deps_cb.setObjectName("upgrade_deps_cb")
        self.upgrade_deps_cb.setChecked(self.last_upgrade_deps)
        self.upgrade_deps_cb.setToolTip("Upgrades all project dependencies to their latest versions")
        self.upgrade_deps_cb.toggled.connect(self.save_preferences)
        layout.addWidget(self.upgrade_deps_cb)
        
        # Warning note
        warning = QLabel("Warning: Upgrading dependencies may change library versions and affect compatibility.")
        warning.setObjectName("warning_label")
        layout.addWidget(warning)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("update_progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%p% %")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Button row with proper spacing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Start Update button
        self.update_btn = QPushButton("Start Update")
        self.update_btn.setProperty("btnType", "success")
        self.update_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.update_btn.setFixedHeight(32)
        self.update_btn.clicked.connect(self.start_update)
        btn_row.addWidget(self.update_btn)

        # Stop Update button
        self.stop_btn = QPushButton("Stop Update")
        self.stop_btn.setProperty("btnType", "uninstall")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setFixedHeight(32)
        self.stop_btn.clicked.connect(self.stop_update)
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
    
    def load_preferences(self):
        """Load user preferences from a simple config file"""
        self.last_update_packages = True
        self.last_upgrade_deps = True
        self.last_project = None
        
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_update_prefs.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    prefs = json.load(f)
                    self.last_update_packages = prefs.get('update_packages', True)
                    self.last_upgrade_deps = prefs.get('upgrade_deps', True)
                    self.last_project = prefs.get('last_project', None)
        except Exception:
            pass
    
    def save_preferences(self):
        """Save user preferences to a simple config file"""
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_update_prefs.json"
            prefs = {
                'update_packages': self.update_packages_cb.isChecked(),
                'upgrade_deps': self.upgrade_deps_cb.isChecked(),
                'last_project': getattr(self, 'last_project', None)
            }
            with open(config_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception:
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
            UpdateProjectDepsPanel,
            UpdateProjectDepsPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            UpdateProjectDepsPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Main title - largest and most prominent */
            UpdateProjectDepsPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
            }}
            
            /* Color-coded section titles */
            UpdateProjectDepsPanel QLabel#custom_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['info_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#success_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['success_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#warning_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['warning_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            /* Section descriptions */
            UpdateProjectDepsPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#warning_label {{
                color: {theme['warning_color']} !important;
                font-size: 10px !important;
                font-weight: normal !important;
            }}
            
            /* Divider lines */
            UpdateProjectDepsPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#success_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            UpdateProjectDepsPanel QLabel#custom_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* ComboBox styling - responsive resizing */
            UpdateProjectDepsPanel QComboBox,
            UpdateProjectDepsPanel QComboBox:hover,
            UpdateProjectDepsPanel QComboBox:focus {{
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
            
            UpdateProjectDepsPanel QComboBox:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            UpdateProjectDepsPanel QComboBox:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            UpdateProjectDepsPanel QComboBox::drop-down {{
                border: none !important;
                width: 24px !important;
            }}
            
            UpdateProjectDepsPanel QComboBox::down-arrow {{
                image: none !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid {theme['text_primary']} !important;
                margin-right: 6px !important;
            }}
            
            UpdateProjectDepsPanel QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                selection-background-color: {theme['button_bg']} !important;
                selection-color: {theme['text_light']} !important;
                padding: 4px !important;
            }}
            
            /* CheckBox styling - completely transparent background */
            UpdateProjectDepsPanel QCheckBox {{
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
            UpdateProjectDepsPanel QCheckBox,
            UpdateProjectDepsPanel QCheckBox:hover,
            UpdateProjectDepsPanel QCheckBox:pressed,
            UpdateProjectDepsPanel QCheckBox:checked {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }}
            
            UpdateProjectDepsPanel QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                border: 2px solid {theme['input_border']} !important;
                background-color: {theme['input_bg']} !important;
                border-radius: 3px !important;
            }}
            
            UpdateProjectDepsPanel QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']} !important;
                border-color: {theme['button_bg']} !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
            }}
            
            UpdateProjectDepsPanel QCheckBox:hover::indicator:unchecked {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            /* Ensure checkbox text area is completely transparent */
            UpdateProjectDepsPanel QCheckBox::text {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Nuclear option: Override ALL possible checkbox backgrounds */
            UpdateProjectDepsPanel QCheckBox * {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }}
            
            /* Progress Bar styling */
            UpdateProjectDepsPanel QProgressBar#update_progress_bar {{
                border: 1px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                text-align: center !important;
                font-size: 11px !important;
                color: {theme['text_primary']} !important;
                background-color: {theme['input_bg']} !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            UpdateProjectDepsPanel QProgressBar#update_progress_bar::chunk {{
                background-color: {theme['button_bg']} !important;
                border-radius: 4px !important;
            }}
            
            /* Base button styling for all states */
            UpdateProjectDepsPanel QPushButton,
            UpdateProjectDepsPanel QPushButton:hover,
            UpdateProjectDepsPanel QPushButton:pressed,
            UpdateProjectDepsPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            /* General disabled button styling (applies to ALL button types) */
            UpdateProjectDepsPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons - Green theme with bright hover effects */
            UpdateProjectDepsPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            UpdateProjectDepsPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            UpdateProjectDepsPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Uninstall/Danger buttons - Red theme with bright hover effects */
            UpdateProjectDepsPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            UpdateProjectDepsPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            UpdateProjectDepsPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
        """)
    
    def start_update(self):
        if not self.update_packages_cb.isChecked() and not self.upgrade_deps_cb.isChecked():
            self.status("[ERROR] Please select at least one update option.")
            return
        
        if not self.selected_project_path:
            self.status("[ERROR] Please select a project to update.")
            return
        
        self.update_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        self.status("=== Starting Dependency Update ===")
        self.status(f"Project: {Path(self.selected_project_path).name}")
        self.status("")
        
        # Start update thread
        self.update_thread = UpdateThread(
            update_packages=self.update_packages_cb.isChecked(),
            upgrade_deps=self.upgrade_deps_cb.isChecked(),
            project_path=str(self.selected_project_path),
            status_callback=self.status
        )
        self.update_thread.progress_signal.connect(self.status)
        self.update_thread.finished_signal.connect(self.update_finished)
        self.update_thread.start()
    
    def stop_update(self):
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()
            self.status("[INFO] Update stopped by user.")
            self.update_finished(False, "Update stopped by user.")
    
    def update_finished(self, success, message):
        self.update_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status(f"[SUCCESS] {message}")
        else:
            self.status(f"[ERROR] {message}")
    
    def start_commit(self):
        """Start Git commit operation"""
        if not self.selected_project_path:
            self.status("[ERROR] Please select a project to commit.")
            return
        
        commit_message = self.commit_msg_edit.text().strip()
        if not commit_message:
            self.status("[ERROR] Please enter a commit message.")
            return
        
        self.commit_btn.setEnabled(False)
        self.status("=== Starting Git Commit ===")
        self.status(f"Project: {Path(self.selected_project_path).name}")
        self.status(f"Message: {commit_message}")
        self.status("")
        
        # Start commit thread
        self.commit_thread = GitCommitThread(
            commit_message=commit_message,
            project_path=str(self.selected_project_path),
            status_callback=self.status
        )
        self.commit_thread.progress_signal.connect(self.status)
        self.commit_thread.finished_signal.connect(self.commit_finished)
        self.commit_thread.start()
    
    def commit_finished(self, success, message):
        """Handle Git commit completion"""
        self.commit_btn.setEnabled(True)
        
        if success:
            self.status(f"[SUCCESS] {message}")
        else:
            self.status(f"[ERROR] {message}")

# Git Commit Thread
class GitCommitThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, commit_message, project_path=None, status_callback=None):
        super().__init__()
        self.commit_message = commit_message
        self.project_path = project_path
        self.status_callback = status_callback
    
    def run(self):
        try:
            def status(msg):
                self.progress_signal.emit(msg)
                if self.status_callback:
                    self.status_callback(msg)
            
            if not self.project_path:
                self.finished_signal.emit(False, "No project path provided for Git operations.")
                return
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(str(self.project_path))
            status(f"[INFO] Changed to project directory: {self.project_path}")
            
            try:
                # Check if we're in a git repository
                result = subprocess.run(["git", "status"], capture_output=True, text=True)
                if result.returncode != 0:
                    status("[INFO] Initializing Git repository...")
                    subprocess.run(["git", "init"], capture_output=True, text=True)
                
                # Stage all changes
                status("[INFO] Staging files...")
                subprocess.run(["git", "add", "."], capture_output=True, text=True)
                
                # Check for staged changes
                result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
                if result.returncode != 0:
                    # There are changes to commit
                    status("[INFO] Committing changes...")
                    result = subprocess.run(["git", "commit", "-m", self.commit_message], 
                                         capture_output=True, text=True)
                    if result.returncode == 0:
                        status("[OK] Changes committed successfully!")
                        self.finished_signal.emit(True, "Changes committed successfully!")
                    else:
                        status(f"[ERROR] Commit failed: {result.stderr}")
                        self.finished_signal.emit(False, f"Commit failed: {result.stderr}")
                else:
                    status("[INFO] No changes to commit.")
                    self.finished_signal.emit(True, "No changes to commit.")
            
            finally:
                # Restore original directory
                try:
                    os.chdir(original_cwd)
                except:
                    pass
                
        except Exception as e:
            self.finished_signal.emit(False, f"Git operation failed: {e}")

if __name__ == "__main__":
    update_project_deps()
