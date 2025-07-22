import os
import subprocess
import sys
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QWizard, QWizardPage, QSizePolicy, QDialog)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication



def setx(var, value, parent=None, terminal=None, show_popup=False):
    import subprocess
    try:
        # Set system-wide environment variable
        result = subprocess.run(["setx", var, value], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            if show_popup and parent:
                QMessageBox.critical(parent, "Set Environment Variable Failed", f"Failed to set {var}: {result.stderr.strip() or 'Unknown error'}")
            raise Exception(result.stderr.strip() or "Unknown error")
        
        # Update current process environment immediately
        os.environ[var] = value
        
        # Broadcast environment change to other processes on Windows
        if sys.platform.startswith("win"):
            try:
                import ctypes
                from ctypes import wintypes
                
                # Define Windows API constants
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                
                # Send broadcast message to notify other processes
                result = ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                    SMTO_ABORTIFHUNG, 5000, ctypes.byref(wintypes.DWORD())
                )
            except Exception:
                # Silently fail if broadcasting fails - environment is still set
                pass
        
        # Copy 7zip if needed
        if var == "XSE_CLIBDT_DEVROOT":
            new_dev_root = Path(value)
            new_7zip = new_dev_root / "tools" / "7zip"
            current_dir = Path(__file__).parent.parent.resolve()
            src_7zip = current_dir / "tools" / "7zip"
            if src_7zip.exists() and not new_7zip.exists():
                try:
                    shutil.copytree(src_7zip, new_7zip)
                except Exception as e:
                    if show_popup and parent:
                        QMessageBox.warning(parent, "7-Zip Copy Failed", f"Failed to copy 7-Zip to new dev root: {e}")
            
            # Set game/mods folder defaults if not set
            game_env = os.getenv("XSE_TES5_GAME_PATH")
            if not game_env or not game_env.strip():
                game_path = str(new_dev_root / "tools" / "SKSE")
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                subprocess.run(["setx", "XSE_TES5_GAME_PATH", game_path], shell=True, creationflags=creationflags)
                os.environ["XSE_TES5_GAME_PATH"] = game_path
                if show_popup and parent:
                    QMessageBox.information(parent, "Default Game Folder", f"Game folder set to: {game_path}")
            
            mods_env = os.getenv("XSE_TES5_MODS_PATH")
            if not mods_env or not mods_env.strip():
                mods_path = str(new_dev_root / "output")
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                subprocess.run(["setx", "XSE_TES5_MODS_PATH", mods_path], shell=True, creationflags=creationflags)
                os.environ["XSE_TES5_MODS_PATH"] = mods_path
                if show_popup and parent:
                    QMessageBox.information(parent, "Default Mods Folder", f"Mods folder set to: {mods_path}")
        
        return True
    except Exception as e:
        if show_popup and parent:
            QMessageBox.critical(parent, "Set Environment Variable Failed", f"Failed to set {var}: {e}")
        return False

class EnvVarsPanel(QWidget):
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = theme_manager
        
        # Connect to theme changes if theme manager is provided
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        
        # Main layout with proper spacing (following create_project.py pattern)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title with divider line following create_project.py pattern
        title_row = QHBoxLayout()
        title_row.setSpacing(8)  # Match create_project.py spacing
        title_row.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Environment Variables")
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
        desc = QLabel("Configure development environment paths and settings.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        
        # Environment Variables section
        env_section = QWidget()
        env_section.setObjectName("env_section")
        env_layout = QVBoxLayout(env_section)
        env_layout.setContentsMargins(0, 0, 0, 8)
        env_layout.setSpacing(8)

        # Environment variables list
        self.vars = [
            ("XSE_CLIBDT_DEVROOT", "Dev Root Folder"),
            ("XSE_TES5_GAME_PATH", "Skyrim Game Folder"),
            ("XSE_TES5_MODS_PATH", "Skyrim Mods Folder"),
            ("XSE_GIT_ROOT", "Git Root"),
            ("XSE_MSVCTOOLS_ROOT", "MSVC Toolchain Root"),
            ("XSE_XMAKE_ROOT", "Xmake Root"),
            ("XSE_NINJA_ROOT", "Ninja Root"),
            ("XSE_GITHUB_DESKTOP_PATH", "GitHub Desktop Path")
        ]
        self.edits = {}
        self.rows = {}
        
        for var, label in self.vars:
            # Create row for each variable
            var_row = QHBoxLayout()
            var_row.setSpacing(8)
            var_row.setContentsMargins(0, 0, 0, 0)
            
            # Label with styling
            var_label = QLabel(label)
            var_label.setObjectName("var_label")
            var_label.setFixedWidth(100)
            var_row.addWidget(var_label)
            
            # Input field with styling
            edit = QLineEdit(os.getenv(var) or "")
            edit.setPlaceholderText(f"Enter {label.lower()}...")
            edit.setObjectName("var_edit")
            edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            edit.setMinimumWidth(200)
            edit.setMinimumHeight(24)
            edit.setMaximumHeight(32)
            self.edits[var] = edit
            var_row.addWidget(edit)
            
            # Folder button with styling
            folder_btn = QPushButton("📁")
            folder_btn.setProperty("btnType", "folder")
            folder_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            folder_btn.setFixedWidth(60)
            folder_btn.setMinimumHeight(24)
            folder_btn.setMaximumHeight(32)
            folder_btn.clicked.connect(lambda _, v=var: self.browse_folder(v))
            var_row.addWidget(folder_btn)
            
            self.rows[var] = (var_row, var_label, edit, folder_btn)
            env_layout.addLayout(var_row)
        # Hide all but Dev Root Folder initially
        for var, (var_row, var_label, edit, folder_btn) in self.rows.items():
            if var != "XSE_CLIBDT_DEVROOT":
                var_label.setVisible(False)
                edit.setVisible(False)
                folder_btn.setVisible(False)
        # Add a placeholder for where the rest will go
        self.extra_vars_widget = QWidget()
        self.extra_vars_layout = QVBoxLayout(self.extra_vars_widget)
        self.extra_vars_layout.setContentsMargins(0, 0, 0, 0)
        self.extra_vars_layout.setSpacing(8)
        env_layout.addWidget(self.extra_vars_widget)
        
        # Add spacing before status
        env_layout.addSpacing(8)
        
        # Status label with styling - hidden by default
        self.status = QLabel()
        self.status.setObjectName("status_label")
        self.status.setVisible(False)  # Hidden by default
        self.status.setWordWrap(True)  # Allow text wrapping
        env_layout.addWidget(self.status)
        
        # Add spacing before buttons
        env_layout.addSpacing(8)
        
        # Button row with proper spacing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Apply button
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setProperty("btnType", "success")
        apply_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        apply_btn.setFixedWidth(120)
        apply_btn.setMinimumHeight(24)
        apply_btn.setMaximumHeight(32)
        apply_btn.clicked.connect(self.apply)
        btn_row.addWidget(apply_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear Variables")
        clear_btn.setProperty("btnType", "uninstall")
        clear_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        clear_btn.setFixedWidth(120)
        clear_btn.setMinimumHeight(24)
        clear_btn.setMaximumHeight(32)
        clear_btn.clicked.connect(self.clear_env_vars)
        btn_row.addWidget(clear_btn)
        
        # Defaults button
        defaults_btn = QPushButton("Use Defaults")
        defaults_btn.setProperty("btnType", "secondary")
        defaults_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        defaults_btn.setFixedWidth(120)
        defaults_btn.setMinimumHeight(24)
        defaults_btn.setMaximumHeight(32)
        defaults_btn.clicked.connect(self.use_defaults)
        btn_row.addWidget(defaults_btn)
        
        env_layout.addLayout(btn_row)
        
        layout.addWidget(env_section)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Apply initial theme
        self.apply_theme()
        # Connect dev root edit to update visibility
        self.edits["XSE_CLIBDT_DEVROOT"].textChanged.connect(self._on_dev_root_changed)
        self._on_dev_root_changed(self.edits["XSE_CLIBDT_DEVROOT"].text())
    
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
    
    def set_theme_manager(self, theme_manager):
        """Set the theme manager for this panel"""
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def browse_folder(self, var):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.edits[var].setText(folder)
            # Get the label for this variable
            var_label = next((label for v, label in self.vars if v == var), var)
            status_text = f"📁 {var_label} set to: {folder}"
            self.set_status(status_text, "info")

    def browse_file(self, var):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Executables (*.exe *.bat *.cmd *.sh);;All Files (*.*)")
        if dlg.exec():
            file_path = dlg.selectedFiles()[0]
            self.edits[var].setText(file_path)
            var_label = next((label for v, label in self.vars if v == var), var)
            status_text = f"📝 {var_label} set to: {file_path}"
            self.set_status(status_text, "info")

    def apply(self):
        class ModalStatusDialog(QDialog):
            def __init__(self, parent=None, total=0):
                super().__init__(parent)
                self.setWindowTitle("Setting Environment Variables")
                self.setModal(True)
                self.setFixedSize(380, 120)
                layout = QVBoxLayout(self)
                self.label = QLabel("Applying environment variable changes...")
                self.label.setWordWrap(True)
                layout.addWidget(self.label)
                self.setLayout(layout)

            def update_status(self, text):
                self.label.setText(text)
                QApplication.processEvents()

        errors = []
        total = len(self.vars)
        dlg = ModalStatusDialog(self, total=total)
        dlg.show()
        QApplication.processEvents()

        for idx, (var, _) in enumerate(self.vars, 1):
            value = self.edits[var].text().strip()
            if value:
                ok = setx(var, value, parent=self, show_popup=False)
                if not ok:
                    errors.append(var)
            dlg.update_status(f"Setting {var} ({idx}/{total})...")

        dlg.update_status("All environment variables processed.")
        QApplication.processEvents()
        dlg.accept()

        if errors:
            status_text = f"❌ Failed to set: {', '.join(errors)}. Check permissions."
            self.set_status(status_text, "error")
            QMessageBox.critical(self, "Environment", f"Some environment variables could not be set: {', '.join(errors)}. Please check your permissions and try again.")
        else:
            status_text = "✅ Environment variables updated successfully and are now available!"
            self.set_status(status_text, "success")
            QMessageBox.information(self, "Environment", "Environment variables updated successfully and are now available immediately!")

    def clear_env_vars(self):
        ENV_VARS = [
            "XSE_CLIBDT_DEVROOT",
            "XSE_TES5_GAME_PATH",
            "XSE_TES5_MODS_PATH",
            "XSE_GIT_ROOT",
            "XSE_MSVCTOOLS_ROOT",
            "XSE_XMAKE_ROOT",
            "XSE_NINJA_ROOT",
            "XSE_GITHUB_DESKTOP_PATH",
        ]
        for var in ENV_VARS:
            if var in os.environ:
                del os.environ[var]
            if var in self.edits:
                self.edits[var].setText("")
        status_text = "🗑️ Environment variables cleared for this session. This does not affect system-wide variables."
        self.set_status(status_text, "info")
        QMessageBox.information(self, "Environment", "Environment variables cleared for this session. This does not affect system-wide variables.")

    def use_defaults(self):
        dev_root = r"C:\ClibDT"
        self.edits["XSE_CLIBDT_DEVROOT"].setText(dev_root)
        self.edits["XSE_TES5_GAME_PATH"].setText(str(Path(dev_root) / "tools" / "SKSE"))
        self.edits["XSE_TES5_MODS_PATH"].setText(str(Path(dev_root) / "output"))
        self.edits["XSE_GIT_ROOT"].setText(str(Path(dev_root) / "tools" / "Git"))
        self.edits["XSE_MSVCTOOLS_ROOT"].setText(str(Path(dev_root) / "tools" / "BuildTools"))
        self.edits["XSE_XMAKE_ROOT"].setText(str(Path(dev_root) / "tools" / "Xmake"))
        self.edits["XSE_NINJA_ROOT"].setText(str(Path(dev_root) / "tools" / "Ninja"))
        self.edits["XSE_GITHUB_DESKTOP_PATH"].setText(str(Path(dev_root) / "tools" / "GitHubDesktop"))
        status_text = "⚙️ Default environment variables loaded. Click 'Apply Changes' to save them."
        self.set_status(status_text, "info")
    
    def set_status(self, message, status_type="info"):
        """Set status message with fancy styling and show/hide logic"""
        if not message or not message.strip():
            self.status.setVisible(False)
            return
        
        # Show the status label
        self.status.setVisible(True)
        
        # Apply fancy styling based on status type
        if status_type == "success":
            self.status.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    background-color: rgba(39, 174, 96, 0.1);
                    border: 1px solid #27ae60;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 4px 0px;
                }
            """)
        elif status_type == "error":
            self.status.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    background-color: rgba(231, 76, 60, 0.1);
                    border: 1px solid #e74c3c;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 4px 0px;
                }
            """)
        elif status_type == "warning":
            self.status.setStyleSheet("""
                QLabel {
                    color: #f39c12;
                    background-color: rgba(243, 156, 18, 0.1);
                    border: 1px solid #f39c12;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 4px 0px;
                }
            """)
        else:  # info
            self.status.setStyleSheet("""
                QLabel {
                    color: #3498db;
                    background-color: rgba(52, 152, 219, 0.1);
                    border: 1px solid #3498db;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 4px 0px;
                }
            """)
        
        self.status.setText(message)
    
    def apply_theme(self):
        """Apply theme colors to the panel"""
        if self.theme_manager:
            self.setStyleSheet(self.theme_manager.get_env_vars_style())
        else:
            # Fallback to basic theme if no theme manager
            try:
                from modules.theme_manager import ThemeManager
                fallback_manager = ThemeManager()
                self.setStyleSheet(fallback_manager.get_env_vars_style())
            except Exception:
                # Ultimate fallback with basic styling
                self.setStyleSheet("""
                    QWidget {
                        background-color: #1e1e1e;
                        color: #e0e0e0;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QLabel {
                        background-color: transparent;
                        color: #e0e0e0;
                        font-size: 11px;
                    }
                    QLineEdit {
                        background-color: #2d2d2d;
                        color: #e0e0e0;
                        border: 2px solid #404040;
                        border-radius: 4px;
                        padding: 6px 8px;
                        font-size: 11px;
                    }
                    QPushButton {
                        background-color: #0078d4;
                        color: #ffffff;
                        border: 1px solid #0078d4;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                """)

    def _on_dev_root_changed(self, text):
        dev_root = text.strip()
        show_others = bool(dev_root)
        for var, (var_row, var_label, edit, folder_btn) in self.rows.items():
            if var == "XSE_CLIBDT_DEVROOT":
                continue
            var_label.setVisible(show_others)
            edit.setVisible(show_others)
            folder_btn.setVisible(show_others)
            if show_others:
                # Set default values based on dev_root
                if var == "XSE_TES5_GAME_PATH":
                    edit.setText(str(Path(dev_root) / "tools" / "SKSE"))
                elif var == "XSE_TES5_MODS_PATH":
                    edit.setText(str(Path(dev_root) / "output"))
                elif var == "XSE_GIT_ROOT":
                    edit.setText(str(Path(dev_root) / "tools" / "Git"))
                elif var == "XSE_MSVCTOOLS_ROOT":
                    edit.setText(str(Path(dev_root) / "tools" / "BuildTools"))
                elif var == "XSE_XMAKE_ROOT":
                    edit.setText(str(Path(dev_root) / "tools" / "Xmake"))
                elif var == "XSE_NINJA_ROOT":
                    edit.setText(str(Path(dev_root) / "tools" / "Ninja"))
                elif var == "XSE_GITHUB_DESKTOP_PATH":
                    edit.setText(str(Path(dev_root) / "tools" / "GitHubDesktop"))
        self.extra_vars_widget.setVisible(bool(dev_root))

class EnvSetupWizard(QWizard):
    def __init__(self, parent=None, terminal=None):
        super().__init__(parent)
        self.terminal = terminal
        self.setWindowTitle("Environment Setup Wizard")
        self.resize(540, 340)
        self.setStyleSheet('''
            QWizard {
                background: #23272e;
            }
            QWizard QLabel {
                color: #e0e0e0;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QLineEdit {
                background: #2c313c;
                color: #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QPushButton {
                background: #3b4252;
                color: #e0e0e0;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QPushButton:hover {
                background: #4c566a;
            }
            QWizard QFrame {
                border: none;
            }
        ''')
        self.addPage(DevRootPage(terminal=self.terminal))
        self.addPage(GameFolderPage(terminal=self.terminal))
        self.addPage(ModsFolderPage(terminal=self.terminal))
        self.addPage(SummaryPage(terminal=self.terminal))
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.finished.connect(self.apply_env_vars)

    def apply_env_vars(self):
        dev_root = self.field('dev_root')
        game_folder = self.field('game_folder')
        mods_folder = self.field('mods_folder')
        ok1 = setx("XSE_CLIBDT_DEVROOT", dev_root, parent=None, terminal=self.terminal)
        ok2 = setx("XSE_TES5_GAME_PATH", game_folder, parent=None, terminal=self.terminal)
        ok3 = setx("XSE_TES5_MODS_PATH", mods_folder, parent=None, terminal=self.terminal)
        if ok1 and ok2 and ok3:
            QMessageBox.information(self, "Environment", "Environment variables set successfully and are now available immediately!")
        else:
            QMessageBox.critical(self, "Environment", "One or more environment variables could not be set. Please check your permissions and try again.")

class DevRootPage(QWizardPage):
    def __init__(self, terminal=None):
        super().__init__()
        self.terminal = terminal
        self.setTitle("<b>Dev Root Folder</b>")
        self.setSubTitle("<span style='color:#b0b0b0; font-size: 12px; font-weight: normal;'>This will contain all your tools and projects.</span>")
        layout = QVBoxLayout()
        label = QLabel("Select your ClibDT dev root folder.")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)
        self.dev_root_edit = QLineEdit(os.getenv("XSE_CLIBDT_DEVROOT", r"C:\ClibDT"))
        self.registerField('dev_root*', self.dev_root_edit)
        layout.addWidget(self.dev_root_edit)
        browse = QPushButton("Browse")
        browse.setIcon(QIcon.fromTheme("folder"))
        browse.clicked.connect(self.browse_folder)
        layout.addWidget(browse)
        layout.addSpacing(16)
        self.setLayout(layout)
    
    def browse_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.dev_root_edit.setText(folder)

    def validatePage(self):
        path = self.dev_root_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation Error", "Dev root folder cannot be empty.")
            return False
        try:
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if not os.access(str(p), os.W_OK):
                QMessageBox.warning(self, "Validation Error", f"Cannot write to {p}. Please choose a writable folder.")
                return False
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid folder: {e}")
            return False
        return True

class GameFolderPage(QWizardPage):
    def __init__(self, terminal=None):
        super().__init__()
        self.terminal = terminal
        self.setTitle("<b>Skyrim Game Folder</b>")
        self.setSubTitle("<span style='color:#b0b0b0; font-size: 12px; font-weight: normal;'>Where skse64_loader.exe is or will be.</span>")
        layout = QVBoxLayout()
        label = QLabel("Select your Skyrim game folder.")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)
        default_game = str(Path(os.getenv("XSE_CLIBDT_DEVROOT", r"C:\ClibDT")) / "tools" / "SKSE")
        self.game_folder_edit = QLineEdit(os.getenv("XSE_TES5_GAME_PATH", default_game))
        self.registerField('game_folder*', self.game_folder_edit)
        layout.addWidget(self.game_folder_edit)
        browse = QPushButton("Browse")
        browse.setIcon(QIcon.fromTheme("folder"))
        browse.clicked.connect(self.browse_folder)
        layout.addWidget(browse)
        layout.addSpacing(16)
        self.setLayout(layout)
    
    def browse_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.game_folder_edit.setText(folder)
    
    def validatePage(self):
        path = self.game_folder_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation Error", "Game folder cannot be empty.")
            return False
        try:
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if not os.access(str(p), os.W_OK):
                QMessageBox.warning(self, "Validation Error", f"Cannot write to {p}. Please choose a writable folder.")
                return False
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid folder: {e}")
            return False
        return True

class ModsFolderPage(QWizardPage):
    def __init__(self, terminal=None):
        super().__init__()
        self.terminal = terminal
        self.setTitle("<b>Skyrim Mods Folder</b>")
        self.setSubTitle("<span style='color:#b0b0b0; font-size: 12px; font-weight: normal;'>Where compiled projects will be installed.</span>")
        layout = QVBoxLayout()
        label = QLabel("Select your Skyrim mods folder.")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)
        default_mods = str(Path(os.getenv("XSE_CLIBDT_DEVROOT", r"C:\ClibDT")) / "output")
        self.mods_folder_edit = QLineEdit(os.getenv("XSE_TES5_MODS_PATH", default_mods))
        self.registerField('mods_folder*', self.mods_folder_edit)
        layout.addWidget(self.mods_folder_edit)
        browse = QPushButton("Browse")
        browse.setIcon(QIcon.fromTheme("folder"))
        browse.clicked.connect(self.browse_folder)
        layout.addWidget(browse)
        layout.addSpacing(16)
        self.setLayout(layout)
    
    def browse_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.mods_folder_edit.setText(folder)
    
    def validatePage(self):
        path = self.mods_folder_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation Error", "Mods folder cannot be empty.")
            return False
        try:
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if not os.access(str(p), os.W_OK):
                QMessageBox.warning(self, "Validation Error", f"Cannot write to {p}. Please choose a writable folder.")
                return False
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid folder: {e}")
            return False
        return True

class SummaryPage(QWizardPage):
    def __init__(self, terminal=None):
        super().__init__()
        self.terminal = terminal
        self.setTitle("<b>Summary</b>")
        layout = QVBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setStyleSheet("font-size: 12px; color: #a3be8c; padding: 12px; font-weight: normal;")
        layout.addWidget(self.summary_label)
        self.setLayout(layout)
    
    def initializePage(self):
        dev_root = self.field('dev_root')
        game_folder = self.field('game_folder')
        mods_folder = self.field('mods_folder')
        summary = f"<b>Dev Root:</b> {dev_root}<br><b>Game Folder:</b> {game_folder}<br><b>Mods Folder:</b> {mods_folder}"
        self.summary_label.setText(summary)

class DevRootOnlyWizard(QWizard):
    def __init__(self, parent=None, terminal=None):
        super().__init__(parent)
        self.terminal = terminal
        self.setWindowTitle("Set Dev Root - ClibDT")
        self.resize(540, 200)
        self.setStyleSheet('''
            QWizard {
                background: #23272e;
            }
            QWizard QLabel {
                color: #e0e0e0;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QLineEdit {
                background: #2c313c;
                color: #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QPushButton {
                background: #3b4252;
                color: #e0e0e0;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: normal;
            }
            QWizard QPushButton:hover {
                background: #4c566a;
            }
            QWizard QFrame {
                border: none;
            }
        ''')
        self.addPage(DevRootFirstPage(terminal=self.terminal))
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.finished.connect(self.apply_dev_root)

    def apply_dev_root(self):
        dev_root = self.field('dev_root')
        setx("XSE_CLIBDT_DEVROOT", dev_root, parent=self, terminal=self.terminal)
        QMessageBox.information(self, "Environment", "Dev root is set successfully and is now available immediately!")

class DevRootFirstPage(QWizardPage):
    def __init__(self, terminal=None):
        super().__init__()
        self.terminal = terminal
        self.setTitle("<b>Set Your Dev Root Folder</b>")
        self.setSubTitle("<span style='color:#b0b0b0; font-size: 12px; font-weight: normal;'>This is the foundation for all ClibDT tools and projects.\nYou must set this first.</span>")
        layout = QVBoxLayout()
        label = QLabel("Choose your ClibDT dev root folder:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)
        self.dev_root_edit = QLineEdit(os.getenv("XSE_CLIBDT_DEVROOT", r"C:\ClibDT"))
        self.registerField('dev_root*', self.dev_root_edit)
        layout.addWidget(self.dev_root_edit)
        browse = QPushButton("Browse Folder")
        browse.setIcon(QIcon.fromTheme("folder"))
        browse.clicked.connect(self.browse_folder)
        layout.addWidget(browse)
        layout.addSpacing(16)
        self.setLayout(layout)
    
    def browse_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.dev_root_edit.setText(folder)
    
    def validatePage(self):
        path = self.dev_root_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation Error", "Dev root folder cannot be empty.")
            return False
        try:
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if not os.access(str(p), os.W_OK):
                QMessageBox.warning(self, "Validation Error", f"Cannot write to {p}. Please choose a writable folder.")
                return False
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid folder: {e}")
            return False
        return True

def show_env_setup(parent=None, terminal=None):
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root or not Path(dev_root).exists():
        wizard = DevRootOnlyWizard(parent=parent, terminal=terminal)
        wizard.exec()
        return False
    return True
