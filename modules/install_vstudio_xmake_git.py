# modules/install_vstudio_xmake_git.py
import os
import sys
import requests
import webbrowser
import subprocess
import shutil
from pathlib import Path
from colorama import init, Fore, Style
import stat
import time
from modules.utilities.common import VERSION
from modules.config_utils import get_config_directory
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QSizePolicy, QDialog, QButtonGroup, QRadioButton, QDialogButtonBox, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QFont
import threading

init(autoreset=True)


#----------utility helpers----------
def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)


#----------main----------
class InstallToolsPanel(QWidget):
    # Signal to show xmake instructions dialog
    show_xmake_instructions_signal = pyqtSignal(str)
    
    def __init__(self, parent=None, status_callback=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = None
        
        # Main layout with proper spacing (following create_project.py pattern)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Main title with divider line and Check Paths button
        title_row = QHBoxLayout()
        title_row.setSpacing(8)  # 8px spacing like create_project.py
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Development Tools")
        title.setObjectName("main_title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        
        # Add divider line
        title_divider = QLabel()
        title_divider.setObjectName("title_divider")
        title_divider.setFixedHeight(2)  # 2px for main title
        title_divider.setMinimumWidth(120)
        title_row.addWidget(title_divider)
        
        title_row.addStretch()  # Push divider to the left
        
        # Add Check Paths button
        self.check_paths_btn = QPushButton("🔍 Check Paths")
        self.check_paths_btn.setProperty("btnType", "folder")
        self.check_paths_btn.setToolTip("Check and update tool installation status")
        self.check_paths_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.check_paths_btn.setFixedWidth(120)
        self.check_paths_btn.setMinimumHeight(24)
        self.check_paths_btn.setMaximumHeight(32)
        self.check_paths_btn.clicked.connect(self.check_all_paths)
        title_row.addWidget(self.check_paths_btn)
        
        layout.addLayout(title_row)
        
        # Main description
        desc = QLabel("Install development tools required for ClibDT projects.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        
        # Development Tools section
        tools_section = QWidget()
        tools_section.setObjectName("tools_section")
        tools_layout = QVBoxLayout(tools_section)
        tools_layout.setContentsMargins(0, 0, 0, 8)
        tools_layout.setSpacing(8)
        

        
        # First row: VS Build Tools and Xmake
        tools_row1 = QHBoxLayout()
        tools_row1.setSpacing(8)
        
        # VS Build Tools with status orb
        vs_container = QVBoxLayout()
        vs_container.setSpacing(2)
        vs_orb_row = QHBoxLayout()
        vs_orb_row.setSpacing(4)
        self.vs_status_orb = QLabel("●")
        self.vs_status_orb.setProperty("toolOrb", "true")
        vs_orb_row.addWidget(self.vs_status_orb)
        vs_orb_row.addStretch()
        vs_container.addLayout(vs_orb_row)
        self.vs_btn = QPushButton("Install Visual Studio Build Tools")
        self.vs_btn.setProperty("btnType", "install")
        self.vs_btn.clicked.connect(self.install_vs_buildtools)
        # Compact button sizing following AI Theme Instructions
        self.vs_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.vs_btn.setMinimumHeight(24)
        self.vs_btn.setMaximumHeight(32)
        vs_container.addWidget(self.vs_btn)
        tools_row1.addLayout(vs_container)
        
        # Xmake with status orb
        xmake_container = QVBoxLayout()
        xmake_container.setSpacing(2)
        xmake_orb_row = QHBoxLayout()
        xmake_orb_row.setSpacing(4)
        self.xmake_status_orb = QLabel("●")
        self.xmake_status_orb.setProperty("toolOrb", "true")
        xmake_orb_row.addWidget(self.xmake_status_orb)
        xmake_orb_row.addStretch()
        xmake_container.addLayout(xmake_orb_row)
        self.xmake_btn = QPushButton("Install Xmake")
        self.xmake_btn.setProperty("btnType", "install")
        self.xmake_btn.clicked.connect(self.install_xmake)
        # Compact button sizing following AI Theme Instructions
        self.xmake_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.xmake_btn.setMinimumHeight(24)
        self.xmake_btn.setMaximumHeight(32)
        xmake_container.addWidget(self.xmake_btn)
        tools_row1.addLayout(xmake_container)
        
        tools_layout.addLayout(tools_row1)
        
        # Second row: Git and SKSE
        tools_row2 = QHBoxLayout()
        tools_row2.setSpacing(8)
        
        # Git with status orb
        git_container = QVBoxLayout()
        git_container.setSpacing(2)
        git_orb_row = QHBoxLayout()
        git_orb_row.setSpacing(4)
        self.git_status_orb = QLabel("●")
        self.git_status_orb.setProperty("toolOrb", "true")
        git_orb_row.addWidget(self.git_status_orb)
        git_orb_row.addStretch()
        git_container.addLayout(git_orb_row)
        self.git_btn = QPushButton("Install Git (Portable)")
        self.git_btn.setProperty("btnType", "install")
        self.git_btn.clicked.connect(self.install_git)
        # Compact button sizing following AI Theme Instructions
        self.git_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.git_btn.setMinimumHeight(24)
        self.git_btn.setMaximumHeight(32)
        git_container.addWidget(self.git_btn)
        tools_row2.addLayout(git_container)
        
        # SKSE with status orb
        skse_container = QVBoxLayout()
        skse_container.setSpacing(2)
        skse_orb_row = QHBoxLayout()
        skse_orb_row.setSpacing(4)
        self.skse_status_orb = QLabel("●")
        self.skse_status_orb.setProperty("toolOrb", "true")
        skse_orb_row.addWidget(self.skse_status_orb)
        skse_orb_row.addStretch()
        skse_container.addLayout(skse_orb_row)
        self.skse_btn = QPushButton("Install SKSE")
        self.skse_btn.setProperty("btnType", "install")
        self.skse_btn.clicked.connect(self.install_skse)
        # Compact button sizing following AI Theme Instructions
        self.skse_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.skse_btn.setMinimumHeight(24)
        self.skse_btn.setMaximumHeight(32)
        skse_container.addWidget(self.skse_btn)
        tools_row2.addLayout(skse_container)
        
        tools_layout.addLayout(tools_row2)
        
        # Third row: GitHub Desktop
        tools_row3 = QHBoxLayout()
        tools_row3.setSpacing(8)
        
        # GitHub Desktop with status orb
        gh_container = QVBoxLayout()
        gh_container.setSpacing(2)
        gh_orb_row = QHBoxLayout()
        gh_orb_row.setSpacing(4)
        self.gh_status_orb = QLabel("●")
        self.gh_status_orb.setProperty("toolOrb", "true")
        gh_orb_row.addWidget(self.gh_status_orb)
        gh_orb_row.addStretch()
        gh_container.addLayout(gh_orb_row)
        self.gh_btn = QPushButton("Install GitHub Desktop")
        self.gh_btn.setProperty("btnType", "install")
        self.gh_btn.clicked.connect(self.open_github_desktop)
        # Compact button sizing following AI Theme Instructions
        self.gh_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.gh_btn.setMinimumHeight(24)
        self.gh_btn.setMaximumHeight(32)
        gh_container.addWidget(self.gh_btn)
        tools_row3.addLayout(gh_container)
        
        tools_layout.addLayout(tools_row3)
        
        layout.addWidget(tools_section)
        
        # Custom Tool Download section
        custom_section = QWidget()
        custom_section.setObjectName("custom_section")
        custom_layout = QVBoxLayout(custom_section)
        custom_layout.setContentsMargins(0, 0, 0, 8)
        custom_layout.setSpacing(8)
        
        # Custom download section title with divider
        custom_title_row = QHBoxLayout()
        custom_title_row.setSpacing(8)
        custom_title_row.setContentsMargins(0, 0, 0, 0)
        
        custom_title = QLabel("Custom Tool Download")
        custom_title.setObjectName("custom_title")
        custom_title_row.addWidget(custom_title)
        
        # Add divider line
        custom_title_divider = QLabel()
        custom_title_divider.setObjectName("custom_title_divider")
        custom_title_divider.setFixedHeight(1)
        custom_title_divider.setMinimumWidth(100)
        custom_title_row.addWidget(custom_title_divider)
        
        custom_title_row.addStretch()
        custom_layout.addLayout(custom_title_row)
        
        custom_desc = QLabel("Paste a direct download link to install a custom tool:")
        custom_desc.setObjectName("section_desc")
        custom_layout.addWidget(custom_desc)
        
        # URL input field
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        
        url_label = QLabel("Download URL:")
        url_label.setObjectName("url_label")
        url_label.setFixedWidth(80)
        url_row.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/tool.zip")
        self.url_input.setObjectName("url_input")
        self.url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_input.setMinimumHeight(24)
        self.url_input.setMaximumHeight(32)
        url_row.addWidget(self.url_input)
        
        # Download button
        self.download_btn = QPushButton("Download & Install")
        self.download_btn.setProperty("btnType", "install")
        self.download_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.download_btn.setFixedWidth(140)  # Consistent width for single button
        self.download_btn.setMinimumHeight(24)
        self.download_btn.setMaximumHeight(32)
        self.download_btn.clicked.connect(self.install_custom_tool)
        url_row.addWidget(self.download_btn)
        
        custom_layout.addLayout(url_row)
        
        layout.addWidget(custom_section)
        
        # Local Tool Path section
        local_section = QWidget()
        local_section.setObjectName("local_section")
        local_layout = QVBoxLayout(local_section)
        local_layout.setContentsMargins(0, 0, 0, 8)
        local_layout.setSpacing(8)
        
        # Local Tool Path section title with divider
        local_title_row = QHBoxLayout()
        local_title_row.setSpacing(8)
        local_title_row.setContentsMargins(0, 0, 0, 0)
        
        local_title = QLabel("Local Tool Path")
        local_title.setObjectName("local_title")
        local_title_row.addWidget(local_title)
        
        # Add divider line
        local_title_divider = QLabel()
        local_title_divider.setObjectName("local_title_divider")
        local_title_divider.setFixedHeight(1)
        local_title_divider.setMinimumWidth(100)
        local_title_row.addWidget(local_title_divider)
        
        local_title_row.addStretch()
        local_layout.addLayout(local_title_row)
        
        local_desc = QLabel("Add a local tool to quick launch:")
        local_desc.setObjectName("section_desc")
        local_layout.addWidget(local_desc)
        
        # Path input for local tool - single row with buttons on the right
        path_input_row = QHBoxLayout()
        path_input_row.setSpacing(8)
        path_input_row.setContentsMargins(0, 0, 0, 0)
        
        # Label with fixed width
        path_label = QLabel("Local Tool Path:")
        path_label.setObjectName("path_label")
        path_label.setFixedWidth(80)
        path_input_row.addWidget(path_label)
        
        # Input field that expands to fill available space
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("C:/path/to/your/tool.exe")
        self.path_input.setObjectName("path_input")
        # Set size policy to expand horizontally and fill available space
        self.path_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.path_input.setMinimumHeight(24)
        self.path_input.setMaximumHeight(32)
        path_input_row.addWidget(self.path_input)
        
        # Button container to keep buttons together
        button_container = QHBoxLayout()
        button_container.setSpacing(8)
        button_container.setContentsMargins(0, 0, 0, 0)
        # Remove size constraint to allow responsive behavior
        
        # Browse button with responsive sizing
        browse_btn = QPushButton("Browse")
        browse_btn.setProperty("btnType", "folder")
        browse_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Expand to share space
        browse_btn.setMinimumHeight(24)
        browse_btn.setMaximumHeight(32)
        def browse_for_tool():
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Tool", "", "Executables (*.exe *.bat *.cmd *.py *.msi);;All Files (*)")
            if file_path:
                self.path_input.setText(file_path)
        browse_btn.clicked.connect(browse_for_tool)
        button_container.addWidget(browse_btn)
        
        # Add to Quick Launch button with responsive sizing
        add_btn = QPushButton("Add to Quick Launch")
        add_btn.setProperty("btnType", "success")
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Expand to share space
        add_btn.setMinimumHeight(24)
        add_btn.setMaximumHeight(32)
        
        def find_main_window_with_quick_launch(widget):
            parent = widget
            while parent is not None:
                if hasattr(parent, 'quick_launch_manager') and hasattr(parent, 'pin_tool_as_icon'):
                    return parent
                parent = parent.parent()
            return None
        
        def add_to_quick_launch():
            file_path = self.path_input.text().strip()
            if not file_path:
                self.set_status("[ERROR] Please enter a tool path.")
                return
            from pathlib import Path
            if not Path(file_path).exists():
                self.set_status("[ERROR] File does not exist.")
                return
            # Walk up the parent chain to find the main window
            main_window = find_main_window_with_quick_launch(self)
            if main_window:
                quick_launch_manager = getattr(main_window, 'quick_launch_manager', None)
                if quick_launch_manager:
                    quick_launch_manager.add_quick_launch_item(file_path)
                    self.set_status(f"[OK] Added {file_path} to quick launch.")
                    self.path_input.clear()
                else:
                    self.set_status("[ERROR] Main window does not support quick launch integration.")
            else:
                self.set_status("[ERROR] Could not access main window for quick launch integration.")
        add_btn.clicked.connect(add_to_quick_launch)
        button_container.addWidget(add_btn)
        
        # Add the button container to the main row
        path_input_row.addLayout(button_container)
        
        local_layout.addLayout(path_input_row)
        
        layout.addWidget(local_section)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize launcher data
        self.pinned_items = []
        
        # Initialize tool paths configuration
        self.tool_paths_config = {}
        self.load_tool_paths_config()
        
        # Apply initial theme (will use fallback theme)
        self.apply_theme()
        
        # Initialize status orbs with lazy loading (after theme is applied)
        self.tool_status_cache = {}  # Cache for tool status to avoid repeated checks
        self.status_orbs_initialized = False
        # Removed automatic tool check on startup - user must click "Check Paths" button
        
        self.load_pinned_items()
        
        # Connect signal to show xmake instructions dialog
        self.show_xmake_instructions_signal.connect(self._show_xmake_instructions_dialog)
    
    def _show_xmake_instructions_dialog(self, xmake_path):
        """Show xmake instructions dialog (called from main thread via signal)"""
        self.set_status("[DEBUG] Signal received, showing instructions dialog...")
        try:
            self._show_xmake_instructions(xmake_path)
            self.set_status("[DEBUG] Instructions dialog created successfully")
        except Exception as e:
            self.set_status(f"[ERROR] Failed to create instructions dialog: {e}")
            # Show fallback instructions in terminal
            self.set_status("=" * 60)
            self.set_status("📋 XMAKE INSTALLATION INSTRUCTIONS")
            self.set_status("=" * 60)
            self.set_status("1. The xmake installer should now be running")
            self.set_status("2. When prompted for installation directory, use:")
            self.set_status(f"   📁 {xmake_path}")
            self.set_status("3. Complete the installation")
            self.set_status("4. Return here and click 'Verify Installation'")
            self.set_status("=" * 60)
    
    def set_theme_manager(self, theme_manager):
        """Set the theme manager for this panel"""
        self.theme_manager = theme_manager
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
        
        # Initialize status orbs with neutral state if not already done
        if not self.status_orbs_initialized:
            self.update_status_orbs_lazy()

    def get_dev_root(self):
        """Get the dev root path from environment or use default"""
        env_root = os.getenv("XSE_CLIBDT_DEVROOT")
        if env_root:
            return str(Path(env_root) / "tools")
        return r"C:\ClibDT\tools"

    def check_vs_buildtools(self):
        """Check if Visual Studio Build Tools are available and working"""
        import shutil
        import subprocess
        
        # Check saved path first
        saved_path = self.tool_paths_config.get('vs_buildtools_path')
        if saved_path and Path(saved_path).exists():
            cl_path = Path(saved_path) / "VC" / "Tools" / "MSVC"
            if cl_path.exists():
                for version_dir in cl_path.iterdir():
                    if version_dir.is_dir():
                        cl_exe = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                        if cl_exe.exists():
                            return True
        
        # Quick PATH check (fastest)
        cl_exe = shutil.which("cl.exe")
        if cl_exe:
            try:
                # Quick test with short timeout
                result = subprocess.run([cl_exe, "/?"], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 or "Microsoft (R) C/C++ Optimizing Compiler" in result.stdout:
                    # Save the path for future use
                    self.update_tool_path('vs_buildtools', str(Path(cl_exe).parent.parent.parent.parent))
                    return True
            except:
                pass
        
        # Check environment variable (fast file existence check)
        msvc_root = os.getenv("XSE_MSVCTOOLS_ROOT")
        if msvc_root:
            cl_path = Path(msvc_root) / "VC" / "Tools" / "MSVC"
            if cl_path.exists():
                # Quick check for any cl.exe without running it
                for version_dir in cl_path.iterdir():
                    if version_dir.is_dir():
                        cl_exe = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                        if cl_exe.exists():
                            # Save the path for future use
                            self.update_tool_path('vs_buildtools', str(Path(cl_exe).parent.parent.parent.parent))
                            return True
        
        # Check dev root (fast file existence check)
        dev_root = Path(self.get_dev_root())
        buildtools_path = dev_root / "BuildTools"
        if buildtools_path.exists():
            cl_path = buildtools_path / "VC" / "Tools" / "MSVC"
            if cl_path.exists():
                for version_dir in cl_path.iterdir():
                    if version_dir.is_dir():
                        cl_exe = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                        if cl_exe.exists():
                            # Save the path for future use
                            self.update_tool_path('vs_buildtools', str(buildtools_path))
                            return True
        return False

    def check_xmake(self):
        """Check if Xmake is available and working"""
        import shutil
        import subprocess
        
        # Check saved path first
        saved_path = self.tool_paths_config.get('xmake_path')
        if saved_path and Path(saved_path).exists():
            xmake_exe = Path(saved_path) / "xmake.exe"
            if xmake_exe.exists():
                return True
        
        # Quick PATH check first (fastest)
        xmake_exe = shutil.which("xmake")
        if xmake_exe:
            try:
                # Quick test with short timeout
                result = subprocess.run([xmake_exe, "--version"], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and "xmake" in result.stdout:
                    # Save the path for future use
                    self.update_tool_path('xmake', str(Path(xmake_exe).parent))
                    return True
            except:
                pass
        
        # Check environment variable (fast file existence check)
        xmake_root = os.getenv("XSE_XMAKE_ROOT")
        if xmake_root:
            xmake_exe = Path(xmake_root) / "xmake.exe"
            if xmake_exe.exists():
                # Save the path for future use
                self.update_tool_path('xmake', str(xmake_root))
                return True
        
        # Check dev root (fast file existence check)
        dev_root = Path(self.get_dev_root())
        xmake_path = dev_root / "tools" / "xmake" / "xmake.exe"
        if xmake_path.exists():
            # Save the path for future use
            self.update_tool_path('xmake', str(dev_root / "tools" / "xmake"))
            return True
        return False

    def check_git(self):
        """Check if Git is available and working"""
        import shutil
        import subprocess
        
        # Check saved path first
        saved_path = self.tool_paths_config.get('git_path')
        if saved_path and Path(saved_path).exists():
            git_exe = Path(saved_path) / "cmd" / "git.exe"
            if git_exe.exists():
                return True
        
        # Quick PATH check first (fastest)
        git_exe = shutil.which("git")
        if git_exe:
            try:
                # Quick test with short timeout
                result = subprocess.run([git_exe, "--version"], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and "git version" in result.stdout:
                    # Save the path for future use
                    self.update_tool_path('git', str(Path(git_exe).parent.parent))
                    return True
            except:
                pass
        
        # Check environment variable (fast file existence check)
        git_root = os.getenv("XSE_GIT_ROOT")
        if git_root:
            git_exe = Path(git_root) / "cmd" / "git.exe"
            if git_exe.exists():
                # Save the path for future use
                self.update_tool_path('git', str(git_root))
                return True
        
        # Check dev root Git location (fast file existence check)
        dev_root = Path(self.get_dev_root())
        git_path = dev_root / "Git" / "cmd" / "git.exe"
        if git_path.exists():
            # Save the path for future use
            self.update_tool_path('git', str(dev_root / "Git"))
            return True
        return False

    def check_skse(self):
        """Check if SKSE is available (fast file existence check)"""
        import os
        
        # Check saved path first
        saved_path = self.tool_paths_config.get('skse_path')
        if saved_path and Path(saved_path).exists():
            for fname in ["skse_loader.exe", "skse64_loader.exe"]:
                skse_exe = Path(saved_path) / fname
                if skse_exe.exists():
                    return True
        
        # Check environment variable (fastest)
        game_path = os.getenv("XSE_TES5_GAME_PATH")
        if game_path:
            for fname in ["skse_loader.exe", "skse64_loader.exe"]:
                skse_exe = Path(game_path) / fname
                if skse_exe.exists():
                    # Save the path for future use
                    self.update_tool_path('skse', str(game_path))
                    return True
        
        # Check dev root (fast file existence check)
        dev_root = Path(self.get_dev_root())
        skse_path = dev_root / "SKSE"
        for fname in ["skse_loader.exe", "skse64_loader.exe"]:
            skse_exe = skse_path / fname
            if skse_exe.exists():
                # Save the path for future use
                self.update_tool_path('skse', str(skse_path))
                return True
        
        return False

    def check_github_desktop(self):
        """Check if GitHub Desktop is available (fast file existence check)"""
        import os
        
        # Check saved path first
        saved_path = self.tool_paths_config.get('github_desktop_path')
        if saved_path and Path(saved_path).exists():
            gh_exe = Path(saved_path) / "GitHubDesktop.exe"
            if gh_exe.exists() and gh_exe.is_file():
                return True
        
        # Check environment variable (fastest)
        gh_path = os.getenv("XSE_GITHUB_DESKTOP_PATH")
        if gh_path:
            gh_exe = Path(gh_path) / "GitHubDesktop.exe"
            if gh_exe.exists() and gh_exe.is_file():
                # Save the path for future use
                self.update_tool_path('github_desktop', str(gh_path))
                return True
        
        # Check default installation (fast file existence check)
        default_path = Path(os.getenv("LocalAppData", "")) / "GitHubDesktop" / "GitHubDesktop.exe"
        if default_path.exists() and default_path.is_file():
            # Save the path for future use
            self.update_tool_path('github_desktop', str(default_path.parent))
            return True
        
        # Check dev root (fast file existence check)
        dev_root = Path(self.get_dev_root())
        gh_path = dev_root / "GitHubDesktop" / "GitHubDesktop.exe"
        if gh_path.exists() and gh_path.is_file():
            # Save the path for future use
            self.update_tool_path('github_desktop', str(dev_root / "GitHubDesktop"))
            return True
            
        # Check Program Files (x86) for older installations
        program_files = Path(os.getenv("ProgramFiles(x86)", "")) / "GitHub Inc" / "GitHub Desktop" / "GitHubDesktop.exe"
        if program_files.exists() and program_files.is_file():
            # Save the path for future use
            self.update_tool_path('github_desktop', str(program_files.parent))
            return True
            
        return False

    def update_status_orbs_lazy(self):
        """Initialize status orbs with saved paths check"""
        # Get theme colors
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            # Fallback colors
            theme = {
                'success_color': '#27ae60',
                'error_color': '#e74c3c',
                'text_secondary': '#b0b0b0'  # Gray for unknown status
            }
        
        # Check saved paths and update orbs accordingly
        success_style = f"""
            QLabel {{
                font-size: 10px;
                color: {theme['success_color']};
                min-width: 10px;
                max-width: 10px;
                border-radius: 5px;
                background-color: transparent;
            }}
        """
        
        neutral_style = f"""
            QLabel {{
                font-size: 10px;
                color: {theme['text_secondary']};
                min-width: 10px;
                max-width: 10px;
                border-radius: 5px;
                background-color: transparent;
            }}
        """
        
        # Check VS Build Tools
        if self.tool_paths_config.get('vs_buildtools_path') and Path(self.tool_paths_config['vs_buildtools_path']).exists():
            self.vs_status_orb.setStyleSheet(success_style)
        else:
            self.vs_status_orb.setStyleSheet(neutral_style)
        
        # Check Xmake
        if self.tool_paths_config.get('xmake_path') and Path(self.tool_paths_config['xmake_path']).exists():
            self.xmake_status_orb.setStyleSheet(success_style)
        else:
            self.xmake_status_orb.setStyleSheet(neutral_style)
        
        # Check Git
        if self.tool_paths_config.get('git_path') and Path(self.tool_paths_config['git_path']).exists():
            self.git_status_orb.setStyleSheet(success_style)
        else:
            self.git_status_orb.setStyleSheet(neutral_style)
        
        # Check SKSE
        if self.tool_paths_config.get('skse_path') and Path(self.tool_paths_config['skse_path']).exists():
            self.skse_status_orb.setStyleSheet(success_style)
        else:
            self.skse_status_orb.setStyleSheet(neutral_style)
        
        # Check GitHub Desktop
        if self.tool_paths_config.get('github_desktop_path') and Path(self.tool_paths_config['github_desktop_path']).exists():
            self.gh_status_orb.setStyleSheet(success_style)
        else:
            self.gh_status_orb.setStyleSheet(neutral_style)
        
        # Mark as initialized
        self.status_orbs_initialized = True
    
    def check_all_paths(self):
        """Check all tool paths and update status orbs"""
        self.set_status("Checking tool installation status...")
        
        # Disable the button during check
        self.check_paths_btn.setEnabled(False)
        self.check_paths_btn.setText("⏳ Checking...")
        
        def run_checks():
            try:
                # Check each tool with timeout to prevent hanging
                import threading
                import time
                
                # Dictionary to store results
                results = {}
                
                # Function to check a tool with timeout
                def check_tool_with_timeout(tool_name, check_func, timeout=3):
                    try:
                        # Use threading with timeout
                        result = [None]
                        exception = [None]
                        
                        def check_wrapper():
                            try:
                                result[0] = check_func()
                            except Exception as e:
                                exception[0] = e
                        
                        thread = threading.Thread(target=check_wrapper)
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout)
                        
                        if thread.is_alive():
                            # Thread is still running, consider it failed
                            results[tool_name] = False
                            return False
                        elif exception[0]:
                            # Exception occurred
                            results[tool_name] = False
                            return False
                        else:
                            # Check completed
                            results[tool_name] = result[0]
                            return result[0]
                    except Exception:
                        results[tool_name] = False
                        return False
                
                # Check each tool with timeout
                check_tool_with_timeout("VS Build Tools", self.check_vs_buildtools)
                check_tool_with_timeout("Xmake", self.check_xmake)
                check_tool_with_timeout("Git", self.check_git)
                check_tool_with_timeout("SKSE", self.check_skse)
                check_tool_with_timeout("GitHub Desktop", self.check_github_desktop)
                
                # Update UI in main thread
                self.update_status_orbs_from_results(results)
                
            except Exception as e:
                self.set_status(f"[ERROR] Path check failed: {e}")
            finally:
                # Re-enable button in main thread
                self.check_paths_btn.setEnabled(True)
                self.check_paths_btn.setText("🔍 Check Paths")
        
        # Run checks in background thread
        threading.Thread(target=run_checks, daemon=True).start()
    
    def update_status_orbs_from_results(self, results):
        """Update status orbs based on cached results"""
        # Get theme colors
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            # Fallback colors
            theme = {
                'success_color': '#27ae60',
                'error_color': '#e74c3c'
            }
        
        # Update VS Build Tools orb
        vs_installed = results.get("VS Build Tools", False)
        if vs_installed:
            self.vs_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['success_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        else:
            self.vs_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['error_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        
        # Update Xmake orb
        xmake_installed = results.get("Xmake", False)
        if xmake_installed:
            self.xmake_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['success_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        else:
            self.xmake_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['error_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        
        # Update Git orb
        git_installed = results.get("Git", False)
        if git_installed:
            self.git_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['success_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        else:
            self.git_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['error_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        
        # Update SKSE orb
        skse_installed = results.get("SKSE", False)
        if skse_installed:
            self.skse_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['success_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        else:
            self.skse_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['error_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        
        # Update GitHub Desktop orb
        gh_installed = results.get("GitHub Desktop", False)
        if gh_installed:
            self.gh_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['success_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        else:
            self.gh_status_orb.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {theme['error_color']};
                    min-width: 10px;
                    max-width: 10px;
                    border-radius: 5px;
                    background-color: transparent;
                }}
            """)
        
        # Show summary
        installed_count = sum(1 for installed in results.values() if installed)
        total_count = len(results)
        self.set_status(f"[OK] Path check complete: {installed_count}/{total_count} tools installed")
    
    def update_status_orbs(self):
        """Legacy method - now calls the optimized version"""
        self.check_all_paths()

    def set_status(self, msg):
        if self.status_callback:
            self.status_callback(msg)



    def install_git(self):
        """Install Git using the progress widget"""
        # Get the main window to access progress widget
        main_window = self.window()
        if hasattr(main_window, 'start_progress_operation'):
            # Use the progress widget for installation
            def git_install_operation(progress_callback, status_callback):
                import requests
                import subprocess
                from pathlib import Path
                import time
                import os
                
                try:
                    dev_root = Path(self.get_dev_root())
                    git_path = dev_root / "Git"
                    dl_dir = dev_root.parent / "downloads"
                    dl_dir.mkdir(parents=True, exist_ok=True)
                    
                    # New Git installer URL
                    git_url = "https://github.com/git-for-windows/git/releases/download/v2.50.1.windows.1/Git-2.50.1-64-bit.exe"
                    git_file = dl_dir / "Git-2.50.1-64-bit.exe"
                    
                    status_callback("Preparing Git installation...")
                    progress_callback(5, 100)
                    
                    # Check if installer already exists in downloads
                    if git_file.exists():
                        status_callback("Git installer found in downloads folder, skipping download...")
                        progress_callback(70, 100)
                    else:
                        # Download the installer
                        status_callback("Downloading Git installer...")
                        progress_callback(10, 100)
                        
                        r = requests.get(git_url, stream=True, timeout=30)
                        total_size = int(r.headers.get('Content-Length', 0))
                        downloaded = 0
                        
                        with open(git_file, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        progress = 10 + int((downloaded / total_size) * 60)  # 10-70%
                                        progress_callback(progress, 100)
                                        status_callback(f"Downloading Git installer... {downloaded//1024//1024}MB")
                                    else:
                                        progress_callback(0, 0)  # Indeterminate
                                        status_callback("Downloading Git installer...")
                        
                        status_callback("Download completed")
                        progress_callback(70, 100)
                    
                    # Clean up existing installation if it exists
                    if git_path.exists():
                        status_callback("Removing existing Git installation...")
                        try:
                            import shutil
                            shutil.rmtree(git_path)
                        except Exception as e:
                            status_callback(f"[WARN] Could not remove existing installation: {e}")
                    
                    # Create the target directory
                    git_path.mkdir(parents=True, exist_ok=True)
                    
                    # Launch the installer with the specified path
                    status_callback("Launching Git installer...")
                    progress_callback(80, 100)
                    
                    # Ensure we have an absolute path without quotes (as per NSIS documentation)
                    git_path_absolute = git_path.resolve()
                    status_callback(f"[INFO] Installer will open with path pre-filled to: {git_path_absolute}")
                    status_callback("[INFO] Complete the installation in the installer window.")
                    
                    # Launch installer in background (don't wait for it)
                    # Use /DIR without quotes as per NSIS documentation
                    creationflags = 0
                    if sys.platform.startswith("win"):
                        creationflags = subprocess.CREATE_NO_WINDOW
                    subprocess.Popen([str(git_file), f'/DIR={git_path_absolute}'], shell=True, creationflags=creationflags)
                    
                    # Set environment variable after a short delay to allow installation to start
                    time.sleep(2)
                    
                    # Set environment variable
                    os.environ["XSE_GIT_ROOT"] = str(git_path)
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.run(["setx", "XSE_GIT_ROOT", str(git_path)], shell=True, creationflags=creationflags)
                    
                    status_callback(f"[OK] XSE_GIT_ROOT set to: {git_path}")
                    status_callback("[OK] Git installer launched. Please complete the installation.")
                    status_callback("[INFO] The status orb will update once Git is installed and detected.")
                    
                    progress_callback(100, 100)
                    return str(git_path)
                    
                except Exception as e:
                    status_callback(f"[ERROR] Git installation failed: {e}")
                    return None
            
            # Start the progress operation
            main_window.start_progress_operation("Installing Git", git_install_operation)
        else:
            # Fallback to old method if progress widget not available
            self.set_status("Downloading Git installer...")
            def run():
                import requests
                import subprocess
                from pathlib import Path
                import time
                
                dev_root = Path(self.get_dev_root())
                git_path = dev_root / "Git"
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                
                # New Git installer URL
                git_url = "https://github.com/git-for-windows/git/releases/download/v2.50.1.windows.1/Git-2.50.1-64-bit.exe"
                git_file = dl_dir / "Git-2.50.1-64-bit.exe"
                
                try:
                    # Check if file already exists and remove it if it's locked
                    if git_file.exists():
                        self.set_status("Removing existing installer file...")
                        try:
                            git_file.unlink()
                        except Exception as e:
                            self.set_status(f"[WARN] Could not remove existing file: {e}")
                            # Try to use a different filename
                            import time
                            timestamp = int(time.time())
                            git_file = dl_dir / f"Git-2.50.1-64-bit-{timestamp}.exe"
                            self.set_status(f"[INFO] Using alternative filename: {git_file.name}")
                    
                    # Download the installer
                    self.set_status("Downloading Git installer...")
                    r = requests.get(git_url, stream=True, timeout=30)
                    total_size = int(r.headers.get('Content-Length', 0))
                    downloaded = 0
                    
                    with open(git_file, "wb") as f:
                        last_percent = -1
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = (downloaded * 100) // total_size
                                    # Only update status every 5% to reduce CPU usage
                                    if percent >= last_percent + 5 or percent == 100:
                                        self.set_status(f"Downloading Git installer... {percent}%")
                                        last_percent = percent
                    
                    self.set_status("[OK] Git installer downloaded.")
                    
                    # Clean up existing installation if it exists
                    if git_path.exists():
                        self.set_status("Removing existing Git installation...")
                        try:
                            import shutil
                            shutil.rmtree(git_path)
                        except Exception as e:
                            self.set_status(f"[WARN] Could not remove existing installation: {e}")
                    
                    # Create the target directory
                    git_path.mkdir(parents=True, exist_ok=True)
                    
                    # Launch the installer with the specified path
                    self.set_status("Launching Git installer...")
                    
                    # Ensure we have an absolute path without quotes (as per NSIS documentation)
                    git_path_absolute = git_path.resolve()
                    self.set_status(f"[INFO] Installer will open with path pre-filled to: {git_path_absolute}")
                    self.set_status("[INFO] Complete the installation in the installer window.")
                    
                    # Launch installer in background (don't wait for it)
                    # Use /DIR without quotes as per NSIS documentation
                    creationflags = 0
                    if sys.platform.startswith("win"):
                        creationflags = subprocess.CREATE_NO_WINDOW
                    subprocess.Popen([str(git_file), f'/DIR={git_path_absolute}'], shell=True, creationflags=creationflags)
                    
                    # Set environment variable after a short delay to allow installation to start
                    import time
                    time.sleep(2)
                    
                    # Set environment variable
                    os.environ["XSE_GIT_ROOT"] = str(git_path)
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.run(["setx", "XSE_GIT_ROOT", str(git_path)], shell=True, creationflags=creationflags)
                    self.set_status(f"[OK] XSE_GIT_ROOT set to: {git_path}")
                    self.set_status("[OK] Git installer launched. Please complete the installation.")
                    self.set_status("[INFO] The status orb will update once Git is installed and detected.")
                        
                except Exception as e:
                    self.set_status(f"[ERROR] Git download failed: {e}")
                    
            threading.Thread(target=run).start()

    def install_vs_buildtools(self):
        """Install Visual Studio Build Tools using the progress widget"""
        # Get the main window to access progress widget
        main_window = self.window()
        if hasattr(main_window, 'start_progress_operation'):
            # Use the progress widget for installation
            def vs_buildtools_install_operation(progress_callback, status_callback):
                import requests
                from pathlib import Path
                import subprocess
                import json
                import time
                
                try:
                    dev_root = Path(self.get_dev_root())
                    tools_dir = dev_root / "BuildTools"
                    dl_dir = dev_root.parent / "downloads"
                    dl_dir.mkdir(parents=True, exist_ok=True)
                    buildtools_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
                    buildtools_exe = dl_dir / "vs_BuildTools.exe"
                    
                    status_callback("Preparing Visual Studio Build Tools installation...")
                    progress_callback(5, 100)
                    
                    # Download installer if not present
                    if not buildtools_exe.exists():
                        status_callback("Downloading Build Tools installer...")
                        progress_callback(10, 100)
                        
                        try:
                            r = requests.get(buildtools_url, stream=True, timeout=30)
                            total_size = int(r.headers.get('Content-Length', 0))
                            downloaded = 0
                            with open(buildtools_exe, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size > 0:
                                            progress = 10 + int((downloaded / total_size) * 30)  # 10-40%
                                            progress_callback(progress, 100)
                                            status_callback(f"Downloading Build Tools installer... {downloaded//1024//1024}MB")
                                        else:
                                            progress_callback(0, 0)  # Indeterminate
                                            status_callback("Downloading Build Tools installer...")
                            status_callback("[OK] Build Tools installer downloaded.")
                        except Exception as e:
                            status_callback(f"[ERROR] Build Tools download failed: {e}")
                            return None
                    else:
                        status_callback("Build Tools installer already exists")
                        progress_callback(40, 100)
                    
                    # Clean up existing installation if it exists
                    if tools_dir.exists():
                        status_callback("Removing existing Build Tools installation...")
                        try:
                            import shutil
                            shutil.rmtree(tools_dir)
                        except Exception as e:
                            status_callback(f"[WARN] Could not remove existing installation: {e}")
                    
                    progress_callback(45, 100)
                    
                    # Build the silent install command with individual components (working approach)
                    components = [
                        "Microsoft.VisualStudio.Component.Roslyn.Compiler",
                        "Microsoft.Component.MSBuild",
                        "Microsoft.VisualStudio.Component.CoreBuildTools",
                        "Microsoft.VisualStudio.Workload.MSBuildTools",
                        "Microsoft.VisualStudio.Component.Windows10SDK",
                        "Microsoft.VisualStudio.Component.VC.CoreBuildTools",
                        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                        "Microsoft.VisualStudio.Component.VC.Redist.14.Latest",
                        "Microsoft.VisualStudio.Component.Windows11SDK.26100",
                        "Microsoft.VisualStudio.Component.VC.CMake.Project",
                        "Microsoft.VisualStudio.Component.TestTools.BuildTools",
                        "Microsoft.VisualStudio.Component.VC.ATL",
                        "Microsoft.Net.Component.4.8.SDK",
                        "Microsoft.Net.Component.4.7.2.TargetingPack",
                        "Microsoft.VisualStudio.Component.VC.ASAN",
                        "Microsoft.VisualStudio.Component.TextTemplating",
                        "Microsoft.VisualStudio.Component.VC.CoreIde",
                        "Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core",
                        "Microsoft.VisualStudio.Component.Vcpkg",
                        "Microsoft.VisualStudio.Component.Windows11SDK.22621",
                        "Microsoft.VisualStudio.Component.Windows10SDK.19041",
                        "Microsoft.VisualStudio.Workload.VCTools",
                        "Microsoft.NetCore.Component.Runtime.9.0",
                        "Microsoft.Net.Component.4.6.1.TargetingPack",
                        "Microsoft.VisualStudio.Component.VC.14.44.17.14.CLI.Support"
                    ]
                    
                    cmd = [
                        str(buildtools_exe),
                        "--installPath", str(tools_dir),
                        "--quiet", "--wait", "--norestart", "--nocache"
                    ]
                    for comp in components:
                        cmd += ["--add", comp]
                    
                    # Verify installer file exists and is executable
                    if not buildtools_exe.exists():
                        status_callback(f"[ERROR] Installer file not found: {buildtools_exe}")
                        return None
                    
                    status_callback(f"[DEBUG] Installer file exists: {buildtools_exe}")
                    status_callback(f"[DEBUG] Installer file size: {buildtools_exe.stat().st_size} bytes")
                    
                    status_callback("Running Build Tools installer (silent)... This may take 10-30 minutes.")
                    progress_callback(50, 100)
                    
                    # Progress animation (simple approach like old code)
                    import threading as _threading
                    progress_running = True
                    def progress_anim():
                        dots = 0
                        start_time = time.time()
                        while progress_running:
                            elapsed = int(time.time() - start_time)
                            progress = 50 + int((elapsed / 1800) * 45)  # 50-95% over 30 minutes
                            if progress > 95:
                                progress = 95
                            progress_callback(progress, 100)
                            status_callback(f"Installing Build Tools (silent) - {elapsed}s{'.' * (dots % 4)}")
                            dots += 1
                            time.sleep(2)
                    
                    progress_thread = _threading.Thread(target=progress_anim)
                    progress_thread.start()
                    
                    try:
                        # Run installer with timeout (60 minutes for slower systems) - simple approach like old code
                        status_callback("Starting installation process...")
                        ret = subprocess.run(cmd, timeout=3600, capture_output=True, text=True)
                        
                        progress_running = False
                        progress_thread.join()
                        
                        if ret.returncode == 0:
                            # Verify installation
                            status_callback("Verifying installation...")
                            progress_callback(95, 100)
                            cl_exe_found = False
                            
                            # Check for cl.exe in the installed directory
                            cl_path = tools_dir / "VC" / "Tools" / "MSVC"
                            if cl_path.exists():
                                for version_dir in cl_path.iterdir():
                                    if version_dir.is_dir():
                                        cl_exe = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                                        if cl_exe.exists():
                                            cl_exe_found = True
                                            status_callback(f"[OK] Found cl.exe at: {cl_exe}")
                                            break
                            
                            if cl_exe_found:
                                # Set environment variable
                                os.environ["XSE_MSVCTOOLS_ROOT"] = str(tools_dir)
                                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                                subprocess.run(["setx", "XSE_MSVCTOOLS_ROOT", str(tools_dir)], shell=True, creationflags=creationflags)
                                status_callback(f"[OK] Build Tools installed successfully to: {tools_dir}")
                                status_callback(f"[OK] XSE_MSVCTOOLS_ROOT set to: {tools_dir}")
                                # Update status orb
                                self.update_status_orbs()
                                progress_callback(100, 100)
                                return str(tools_dir)
                            else:
                                status_callback("[ERROR] Installation completed but cl.exe not found. Installation may have failed.")
                                status_callback("[INFO] Check the installer output for errors.")
                                if ret.stdout:
                                    status_callback(f"Installer output: {ret.stdout}")
                                if ret.stderr:
                                    status_callback(f"Installer errors: {ret.stderr}")
                                return None
                        else:
                            status_callback(f"[ERROR] Build Tools installer failed with return code: {ret.returncode}")
                            if ret.stdout:
                                status_callback(f"Installer output: {ret.stdout}")
                            if ret.stderr:
                                status_callback(f"Installer errors: {ret.stderr}")
                            
                            # Direct guidance for installation issues
                            status_callback("[INFO] Installation failed. Completely uninstall any previous Build Tools and try again.")
                            return None
                            
                    except subprocess.TimeoutExpired:
                        progress_running = False
                        progress_thread.join()
                        status_callback("[ERROR] Build Tools installation timed out after 60 minutes.")
                        status_callback("[INFO] The installer may still be running in the background.")
                        status_callback("[INFO] Installation timed out. Completely uninstall any previous Build Tools and try again.")
                        return None
                        
                    except Exception as e:
                        progress_running = False
                        progress_thread.join()
                        status_callback(f"[ERROR] Build Tools silent install failed: {e}")
                        status_callback("[INFO] Installation failed. Completely uninstall any previous Build Tools and try again.")
                        status_callback("[INFO] Attempting fallback to manual download...")
                        import webbrowser
                        webbrowser.open(buildtools_url)
                        status_callback("[INFO] Please download and install Build Tools manually from the opened page.")
                        return None
                        
                except Exception as e:
                    status_callback(f"[ERROR] Build Tools installation failed: {e}")
                    return None
            
            # Start the progress operation
            main_window.start_progress_operation("Installing Visual Studio Build Tools", vs_buildtools_install_operation)
        else:
            # Fallback to old method if progress widget not available
            self.set_status("Installing Visual Studio Build Tools silently...")
            def run():
                import requests
                from pathlib import Path
                import subprocess
                import json
                import time
                
                dev_root = Path(self.get_dev_root())
                tools_dir = dev_root / "BuildTools"
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                buildtools_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
                buildtools_exe = dl_dir / "vs_BuildTools.exe"
                
                # Download installer if not present
                if not buildtools_exe.exists():
                    self.set_status("Downloading Build Tools installer...")
                    try:
                        r = requests.get(buildtools_url, stream=True, timeout=30)
                        total_size = int(r.headers.get('Content-Length', 0))
                        downloaded = 0
                        with open(buildtools_exe, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        percent = (downloaded * 100) // total_size
                                        self.set_status(f"Downloading Build Tools installer... {percent}%")
                        self.set_status("[OK] Build Tools installer downloaded.")
                    except Exception as e:
                        self.set_status(f"[ERROR] Build Tools download failed: {e}")
                        return
                
                # Clean up existing installation if it exists
                if tools_dir.exists():
                    self.set_status("Removing existing Build Tools installation...")
                    try:
                        import shutil
                        shutil.rmtree(tools_dir)
                    except Exception as e:
                        self.set_status(f"[WARN] Could not remove existing installation: {e}")
                
                # Build the silent install command with individual components (working approach)
                components = [
                    "Microsoft.VisualStudio.Component.Roslyn.Compiler",
                    "Microsoft.Component.MSBuild",
                    "Microsoft.VisualStudio.Component.CoreBuildTools",
                    "Microsoft.VisualStudio.Workload.MSBuildTools",
                    "Microsoft.VisualStudio.Component.Windows10SDK",
                    "Microsoft.VisualStudio.Component.VC.CoreBuildTools",
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                    "Microsoft.VisualStudio.Component.VC.Redist.14.Latest",
                    "Microsoft.VisualStudio.Component.Windows11SDK.26100",
                    "Microsoft.VisualStudio.Component.VC.CMake.Project",
                    "Microsoft.VisualStudio.Component.TestTools.BuildTools",
                    "Microsoft.VisualStudio.Component.VC.ATL",
                    "Microsoft.Net.Component.4.8.SDK",
                    "Microsoft.Net.Component.4.7.2.TargetingPack",
                    "Microsoft.VisualStudio.Component.VC.ASAN",
                    "Microsoft.VisualStudio.Component.TextTemplating",
                    "Microsoft.VisualStudio.Component.VC.CoreIde",
                    "Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core",
                    "Microsoft.VisualStudio.Component.Vcpkg",
                    "Microsoft.VisualStudio.Component.Windows11SDK.22621",
                    "Microsoft.VisualStudio.Component.Windows10SDK.19041",
                    "Microsoft.VisualStudio.Workload.VCTools",
                    "Microsoft.NetCore.Component.Runtime.9.0",
                    "Microsoft.Net.Component.4.6.1.TargetingPack",
                    "Microsoft.VisualStudio.Component.VC.14.44.17.14.CLI.Support"
                ]
                
                cmd = [
                    str(buildtools_exe),
                    "--installPath", str(tools_dir),
                    "--quiet", "--wait", "--norestart", "--nocache"
                ]
                for comp in components:
                    cmd += ["--add", comp]
                
                # Verify installer file exists and is executable
                if not buildtools_exe.exists():
                    self.set_status(f"[ERROR] Installer file not found: {buildtools_exe}")
                    return
                
                self.set_status(f"[DEBUG] Installer file exists: {buildtools_exe}")
                self.set_status(f"[DEBUG] Installer file size: {buildtools_exe.stat().st_size} bytes")
                
                self.set_status("Running Build Tools installer (silent)... This may take 10-30 minutes.")
                
                # Progress animation (simple approach like old code)
                import threading as _threading
                progress_running = True
                def progress_anim():
                    dots = 0
                    start_time = time.time()
                    while progress_running:
                        elapsed = int(time.time() - start_time)
                        self.set_status(f"Installing Build Tools - {elapsed}s{'.' * (dots % 4)}")
                        dots += 1
                        time.sleep(2)
                
                progress_thread = _threading.Thread(target=progress_anim)
                progress_thread.start()
                
                try:
                    # Run installer with timeout (60 minutes for slower systems) - simple approach like old code
                    self.set_status("Starting installation process...")
                    ret = subprocess.run(cmd, timeout=3600, capture_output=True, text=True)
                    
                    progress_running = False
                    progress_thread.join()
                    
                    if ret.returncode == 0:
                        # Verify installation
                        self.set_status("Verifying installation...")
                        cl_exe_found = False
                        
                        # Check for cl.exe in the installed directory
                        cl_path = tools_dir / "VC" / "Tools" / "MSVC"
                        if cl_path.exists():
                            for version_dir in cl_path.iterdir():
                                if version_dir.is_dir():
                                    cl_exe = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                                    if cl_exe.exists():
                                        cl_exe_found = True
                                        self.set_status(f"[OK] Found cl.exe at: {cl_exe}")
                                        break
                        
                        if cl_exe_found:
                            # Set environment variable
                            os.environ["XSE_MSVCTOOLS_ROOT"] = str(tools_dir)
                            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                            subprocess.run(["setx", "XSE_MSVCTOOLS_ROOT", str(tools_dir)], shell=True, creationflags=creationflags)
                            self.set_status(f"[OK] Build Tools installed successfully to: {tools_dir}")
                            self.set_status(f"[OK] XSE_MSVCTOOLS_ROOT set to: {tools_dir}")
                            # Update status orb
                            self.update_status_orbs()
                        else:
                            self.set_status("[ERROR] Installation completed but cl.exe not found. Installation may have failed.")
                            self.set_status("[INFO] Check the installer output for errors.")
                            if ret.stdout:
                                self.set_status(f"Installer output: {ret.stdout}")
                            if ret.stderr:
                                self.set_status(f"Installer errors: {ret.stderr}")
                    else:
                        self.set_status(f"[ERROR] Build Tools installer failed with return code: {ret.returncode}")
                        if ret.stdout:
                            self.set_status(f"Installer output: {ret.stdout}")
                        if ret.stderr:
                            self.set_status(f"Installer errors: {ret.stderr}")
                        
                        # Direct guidance for installation issues
                        self.set_status("[INFO] Installation failed. Completely uninstall any previous Build Tools and try again.")
                       
                        
                except subprocess.TimeoutExpired:
                    progress_running = False
                    progress_thread.join()
                    self.set_status("[ERROR] Build Tools installation timed out after 60 minutes.")
                    self.set_status("[INFO] The installer may still be running in the background.")
                    self.set_status("[INFO] Installation timed out. Completely uninstall any previous Build Tools and try again.")
                    
                except Exception as e:
                    progress_running = False
                    progress_thread.join()
                    self.set_status(f"[ERROR] Build Tools silent install failed: {e}")
                    self.set_status("[INFO] Installation failed. Completely uninstall any previous Build Tools and try again.")
                    self.set_status("[INFO] Attempting fallback to manual download...")
                    import webbrowser
                    webbrowser.open(buildtools_url)
                    self.set_status("[INFO] Please download and install Build Tools manually from the opened page.")
            
            threading.Thread(target=run).start()

    def install_xmake(self):
        """Download xmake installer and let user install manually"""
        # Get the main window to access progress widget
        main_window = self.window()
        if hasattr(main_window, 'start_progress_operation'):
            # Use the progress widget for download
            def xmake_download_operation(progress_callback, status_callback):
                import requests
                from pathlib import Path
                import subprocess
                import os
                
                try:
                    # Download directory
                    dl_dir = Path(self.get_dev_root()).parent / "downloads"
                    dl_dir.mkdir(parents=True, exist_ok=True)
                    
                    status_callback("Preparing xmake installer download...")
                    progress_callback(5, 100)
                    
                    # Download the direct Windows installer
                    installer_url = "https://github.com/xmake-io/xmake/releases/download/v3.0.1/xmake-dev.win64.exe"
                    installer_file = dl_dir / "xmake-dev.win64.exe"
                    
                    # Check if installer already exists in downloads
                    if installer_file.exists():
                        status_callback("xmake installer found in downloads folder, skipping download...")
                        progress_callback(90, 100)
                    else:
                        status_callback("Downloading xmake Windows installer...")
                        progress_callback(10, 100)
                        
                        # Download with progress
                        response = requests.get(installer_url, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        with open(str(installer_file), 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        progress = 10 + int((downloaded / total_size) * 80)  # 10-90%
                                        progress_callback(progress, 100)
                                        status_callback(f"Downloading xmake... {downloaded//1024//1024}MB")
                                    else:
                                        progress_callback(0, 0)  # Indeterminate
                                        status_callback("Downloading xmake...")
                        
                        status_callback("Download completed!")
                        progress_callback(90, 100)
                    
                    # Launch the installer for user to complete manually
                    status_callback("Launching xmake installer...")
                    progress_callback(95, 100)
                    
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.Popen([str(installer_file)], creationflags=creationflags)
                    
                    status_callback("[OK] xmake installer launched successfully!")
                    
                    # Show installation path dialog on main thread
                    from PyQt6.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, 'show_xmake_path_dialog', Qt.ConnectionType.QueuedConnection)
                    
                    # Wait a bit for installer to start, then start detection loop
                    import time
                    time.sleep(3)
                    
                    # Start detection loop in background
                    def detect_installation():
                        max_attempts = 30  # 5 minutes (10 second intervals)
                        attempts = 0
                        
                        while attempts < max_attempts:
                            attempts += 1
                            time.sleep(10)  # Check every 10 seconds
                            
                            # Check for xmake.exe in common locations
                            common_paths = [
                                Path.home() / ".xmake" / "xmake.exe",
                                Path("C:/xmake/xmake.exe"),
                                Path("C:/Program Files/xmake/xmake.exe"),
                                Path("C:/Program Files (x86)/xmake/xmake.exe"),
                            ]
                            
                            for test_path in common_paths:
                                if test_path.exists():
                                    try:
                                        version_result = subprocess.run([str(test_path), "--version"], 
                                                                      capture_output=True, text=True, timeout=10)
                                        if version_result.returncode == 0:
                                            xmake_path = test_path.parent
                                            status_callback(f"[OK] xmake detected at: {xmake_path}")
                                            
                                            # Set environment variable
                                            os.environ["XSE_XMAKE_ROOT"] = str(xmake_path)
                                            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                                            subprocess.run(["setx", "XSE_XMAKE_ROOT", str(xmake_path)], shell=True, creationflags=creationflags)
                                            
                                            status_callback(f"[OK] XSE_XMAKE_ROOT set to: {xmake_path}")
                                            status_callback("[OK] xmake installation completed successfully!")
                                            
                                            # Update status orb
                                            self.update_status_orbs()
                                            return
                                    except:
                                        continue
                            
                            if attempts % 6 == 0:  # Every minute
                                status_callback(f"[INFO] Still waiting for xmake installation... ({attempts//6} minutes)")
                        
                        status_callback("[WARN] xmake not detected after 5 minutes.")
                        status_callback("[INFO] Please restart ClibDT after completing the installation.")
                    
                    # Start detection in background thread
                    detection_thread = threading.Thread(target=detect_installation, daemon=True)
                    detection_thread.start()
                    
                    progress_callback(100, 100)
                    
                    return str(installer_file)
                    
                except Exception as e:
                    status_callback(f"[ERROR] Download failed: {e}")
                    status_callback("You can manually download xmake from: https://xmake.io/")
                    return None
            
            # Start the progress operation
            main_window.start_progress_operation("Downloading Xmake Installer", xmake_download_operation)
        else:
            # Fallback to old method if progress widget not available
            self.set_status("Downloading xmake installer...")
            def run():
                import requests
                from pathlib import Path
                import subprocess
                import os
                
                # Download directory
                dl_dir = Path(self.get_dev_root()).parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                
                # Download the direct Windows installer
                installer_url = "https://github.com/xmake-io/xmake/releases/download/v3.0.1/xmake-dev.win64.exe"
                installer_file = dl_dir / "xmake-dev.win64.exe"
                
                try:
                    self.set_status("Downloading xmake Windows installer...")
                    response = requests.get(installer_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(str(installer_file), 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    self.set_status("Download completed. Launching installer...")
                    
                    # Launch the installer normally (let user interact)
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.Popen([str(installer_file)], creationflags=creationflags)
                    
                    self.set_status("[OK] xmake installer launched successfully!")
                    
                    # Show installation path dialog on main thread
                    from PyQt6.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, 'show_xmake_path_dialog', Qt.ConnectionType.QueuedConnection)
                    
                    # Wait a bit for installer to start, then start detection loop
                    import time
                    time.sleep(3)
                    
                    # Start detection loop in background
                    def detect_installation():
                        max_attempts = 30  # 5 minutes (10 second intervals)
                        attempts = 0
                        
                        while attempts < max_attempts:
                            attempts += 1
                            time.sleep(10)  # Check every 10 seconds
                            
                            # Check for xmake.exe in common locations
                            common_paths = [
                                Path.home() / ".xmake" / "xmake.exe",
                                Path("C:/xmake/xmake.exe"),
                                Path("C:/Program Files/xmake/xmake.exe"),
                                Path("C:/Program Files (x86)/xmake/xmake.exe"),
                            ]
                            
                            for test_path in common_paths:
                                if test_path.exists():
                                    try:
                                        version_result = subprocess.run([str(test_path), "--version"], 
                                                                      capture_output=True, text=True, timeout=10)
                                        if version_result.returncode == 0:
                                            xmake_path = test_path.parent
                                            self.set_status(f"[OK] xmake detected at: {xmake_path}")
                                            
                                            # Set environment variable
                                            os.environ["XSE_XMAKE_ROOT"] = str(xmake_path)
                                            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                                            subprocess.run(["setx", "XSE_XMAKE_ROOT", str(xmake_path)], shell=True, creationflags=creationflags)
                                            
                                            self.set_status(f"[OK] XSE_XMAKE_ROOT set to: {xmake_path}")
                                            self.set_status("[OK] xmake installation completed successfully!")
                                            
                                            # Update status orb
                                            self.update_status_orbs()
                                            return
                                    except:
                                        continue
                            
                            if attempts % 6 == 0:  # Every minute
                                self.set_status(f"[INFO] Still waiting for xmake installation... ({attempts//6} minutes)")
                        
                        self.set_status("[WARN] xmake not detected after 5 minutes.")
                        self.set_status("[INFO] Please restart ClibDT after completing the installation.")
                    
                    # Start detection in background thread
                    detection_thread = threading.Thread(target=detect_installation, daemon=True)
                    detection_thread.start()
                    
                except Exception as e:
                    self.set_status(f"[ERROR] xmake download failed: {e}")
                    self.set_status("You can manually download xmake from: https://xmake.io/")
            
            threading.Thread(target=run).start()
    

    
    def _show_xmake_instructions(self, xmake_path):
        """Show xmake installation instructions in a separate window"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        class XmakeInstructionsDialog(QDialog):
            def __init__(self, xmake_path, parent=None):
                super().__init__(parent)
                self.xmake_path = xmake_path
                self.parent_panel = parent  # Store reference to parent panel
                self.setWindowTitle("Xmake Installation Instructions")
                self.setModal(True)
                self.setFixedSize(450, 350)  # Adequate size to prevent text clipping
                
                # Main layout with generous spacing to prevent text clipping
                layout = QVBoxLayout()
                layout.setSpacing(20)  # Generous spacing between elements
                layout.setContentsMargins(24, 28, 24, 24)  # Generous margins
                
                # Title with adequate spacing and minimum height
                title = QLabel("")
                title.setStyleSheet(f"""
                    font-size: 16px;
                    font-weight: bold;
                    color: #e0e0e0;
                    margin-bottom: 20px;
                    padding: 12px 0px;
                    background: transparent;
                    min-height: 24px;
                """)
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)
                
                # Instructions text
                instructions = QTextEdit()
                instructions.setReadOnly(True)
                instructions.setFont(QFont("Consolas", 10))
                instructions.setStyleSheet(f"""
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 2px solid #404040;
                    border-radius: 6px;
                    padding: 10px;
                    min-height: 120px;
                """)
                
                instruction_text = f"""
Xmake Installation Instructions

When prompted for installation directory, use:
   {xmake_path}

                """
                
                instructions.setPlainText(instruction_text)
                layout.addWidget(instructions)
                
                # Button row with adequate spacing
                button_row = QHBoxLayout()
                button_row.setSpacing(12)  # Space between buttons
                button_row.setContentsMargins(0, 16, 0, 0)  # Top margin from content
                
                # Copy path button
                copy_btn = QPushButton("Copy Path")
                copy_btn.setProperty("btnType", "folder")
                copy_btn.setFixedSize(100, 32)  # Fixed size for consistency
                copy_btn.clicked.connect(self.copy_path)
                
                # Verify button
                verify_btn = QPushButton("Verify Installation")
                verify_btn.setProperty("btnType", "success")
                verify_btn.setFixedSize(120, 32)  # Fixed size for consistency
                verify_btn.clicked.connect(self.verify_installation)
                
                # Close button
                close_btn = QPushButton("Close")
                close_btn.setProperty("btnType", "secondary")
                close_btn.setFixedSize(80, 32)  # Fixed size for consistency
                close_btn.clicked.connect(self.close)
                
                button_row.addStretch()  # Push buttons to the right
                button_row.addWidget(copy_btn)
                button_row.addWidget(verify_btn)
                button_row.addWidget(close_btn)
                layout.addLayout(button_row)
                
                self.setLayout(layout)
                
                # Apply theme
                self.apply_theme()
            
            def copy_path(self):
                """Copy the xmake path to clipboard"""
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(str(self.xmake_path))
                
                # Show temporary feedback
                self.setWindowTitle("Xmake Installation Instructions - Path Copied!")
                
                # Reset title after 2 seconds
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.setWindowTitle("Xmake Installation Instructions"))
            
            def verify_installation(self):
                """Verify xmake installation"""
                # Call the parent's verification method
                if self.parent_panel and hasattr(self.parent_panel, '_verify_xmake_installation'):
                    self.parent_panel._verify_xmake_installation(self.xmake_path)
                    self.setWindowTitle("Xmake Installation Instructions - Verification Complete!")
                else:
                    # Try to find the main window and call verification
                    try:
                        from PyQt6.QtWidgets import QApplication
                        app = QApplication.instance()
                        if app:
                            for widget in app.topLevelWidgets():
                                if hasattr(widget, 'install_tools_panel') and hasattr(widget.install_tools_panel, '_verify_xmake_installation'):
                                    widget.install_tools_panel._verify_xmake_installation(self.xmake_path)
                                    self.setWindowTitle("Xmake Installation Instructions - Verification Complete!")
                                    return
                    except Exception:
                        pass
                    self.setWindowTitle("Xmake Installation Instructions - Verification Failed!")
            
            def apply_theme(self):
                """Apply theme styling following AI Theme Instructions for dialogs"""
                # Get theme from parent if available
                theme = self.get_theme_from_parent()
                
                # Apply minimal global styles to avoid conflicts
                self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {theme['window_bg']};
                        color: {theme['text_primary']};
                    }}
                    
                    QLabel {{
                        color: {theme['text_primary']};
                        background: transparent;
                    }}
                    
                    /* Dialog-specific button styling */
                    QPushButton {{
                        border: none !important;
                        padding: 8px 16px !important;
                        border-radius: 6px !important;
                        font-size: 11px !important;
                        font-weight: bold !important;
                        min-height: 16px !important;
                        margin: 2px 4px !important;
                    }}
                    
                    QPushButton[btnType="success"] {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                        color: {theme['text_light']} !important;
                        border: 1px solid {theme['success_color']} !important;
                    }}
                    
                    QPushButton[btnType="success"]:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                        border: 2px solid #a9dfbf !important;
                        color: #ffffff !important;
                    }}
                    
                    QPushButton[btnType="folder"] {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {theme['info_color']}, stop:1 {theme['info_color']}) !important;
                        color: {theme['text_light']} !important;
                        border: 1px solid {theme['info_color']} !important;
                    }}
                    
                    QPushButton[btnType="folder"]:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #85c1e9, stop:0.5 #5dade2, stop:1 #3498db) !important;
                        border: 2px solid #a9cce3 !important;
                        color: #ffffff !important;
                    }}
                    
                    QPushButton[btnType="secondary"] {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #6c757d, stop:1 #5a6268) !important;
                        color: {theme['text_light']} !important;
                        border: 1px solid #5a6268 !important;
                    }}
                    
                    QPushButton[btnType="secondary"]:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #bdc3c7, stop:0.5 #95a5a6, stop:1 #7f8c8d) !important;
                        border: 2px solid #d5dbdb !important;
                        color: #ffffff !important;
                    }}
                """)
            
            def get_theme_from_parent(self):
                """Get theme from parent window's theme manager"""
                try:
                    # Try to get theme from parent panel if available
                    if self.parent_panel and hasattr(self.parent_panel, 'theme_manager'):
                        return self.parent_panel.theme_manager.get_theme()
                    
                    # Try to get theme from dialog parent
                    parent = self.parent()
                    if parent and hasattr(parent, 'theme_manager'):
                        return parent.theme_manager.get_theme()
                    
                    # Try to find main window through application
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        for widget in app.topLevelWidgets():
                            if hasattr(widget, 'theme_manager'):
                                return widget.theme_manager.get_theme()
                except Exception:
                    pass
                
                # Fallback theme
                return {
                    'window_bg': '#1e1e1e',
                    'text_primary': '#e0e0e0',
                    'text_secondary': '#b0b0b0',
                    'text_light': '#ffffff',
                    'button_bg': '#0078d4',
                    'input_border': '#404040',
                    'bg_primary': '#2d2d2d',
                    'success_color': '#27ae60',
                    'error_color': '#e74c3c',
                    'info_color': '#3498db'
                }
        
        # Create and show the dialog in a non-blocking way
        try:
            self.set_status("[DEBUG] Creating XmakeInstructionsDialog...")
            # Create dialog without parent to avoid threading issues
            dialog = XmakeInstructionsDialog(xmake_path, None)
            self.set_status("[DEBUG] Showing dialog...")
            dialog.show()
            # Ensure the dialog is properly initialized
            dialog.raise_()
            dialog.activateWindow()
            self.set_status("[DEBUG] Dialog should now be visible")
        except Exception as e:
            self.set_status(f"[ERROR] Failed to show instructions dialog: {e}")
            # Fallback to simple message
            self.set_status("=" * 60)
            self.set_status("XMAKE INSTALLATION INSTRUCTIONS")
            self.set_status("=" * 60)
            self.set_status("1. The xmake installer should now be running")
            self.set_status("2. When prompted for installation directory, use:")
            self.set_status(f"   {xmake_path}")
            self.set_status("3. Complete the installation")
            self.set_status("4. Return here and click 'Verify Installation'")
            self.set_status("=" * 60)
    
    def _add_verify_button(self, xmake_path):
        """Add a verify installation button to the main panel"""
        try:
            from PyQt6.QtWidgets import QPushButton
            from PyQt6.QtCore import Qt
            
            # Create verify button
            verify_btn = QPushButton("✅ Verify xmake Installation")
            verify_btn.setObjectName("verify_xmake_btn")
            verify_btn.clicked.connect(lambda: self._verify_xmake_installation(xmake_path))
            verify_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #229954);
                    color: #ffffff;
                    border: 2px solid #229954;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 200px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #58d68d, stop:1 #27ae60);
                    border-color: #58d68d;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #229954, stop:1 #1e8449);
                    border-color: #1e8449;
                }
            """)
            
            # Add to the main layout as a fallback
            main_layout = self.layout()
            if main_layout:
                main_layout.addWidget(verify_btn)
                
        except Exception as e:
            self.set_status(f"[ERROR] Failed to add verify button: {e}")
    
    def _verify_xmake_installation(self, xmake_path):
        """Verify xmake installation and set environment variables"""
        try:
            import subprocess
            import os
            
            # Check for xmake.exe in the installation path
            xmake_exe = xmake_path / "xmake.exe"
            if not xmake_exe.exists():
                # Check common installation paths
                common_paths = [
                    xmake_path,
                    Path.home() / ".xmake",
                    Path("C:/xmake"),
                    Path("C:/Program Files/xmake"),
                ]
                
                for path in common_paths:
                    test_exe = path / "xmake.exe"
                    if test_exe.exists():
                        xmake_exe = test_exe
                        xmake_path = path
                        self.set_status(f"[DEBUG] Found xmake at: {xmake_path}")
                        break
            
            if xmake_exe.exists():
                # Test xmake version
                try:
                    version_result = subprocess.run([str(xmake_exe), "--version"], 
                                                  capture_output=True, text=True, timeout=10)
                    if version_result.returncode == 0:
                        version_output = version_result.stdout.strip()
                        self.set_status(f"[OK] xmake version: {version_output}")
                    else:
                        self.set_status("[WARNING] Could not verify xmake version")
                except Exception as e:
                    self.set_status(f"[WARNING] Could not verify xmake version: {e}")
                
                # Set environment variable
                os.environ["XSE_XMAKE_ROOT"] = str(xmake_path)
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                subprocess.run(["setx", "XSE_XMAKE_ROOT", str(xmake_path)], shell=True, creationflags=creationflags)
                self.set_status(f"[OK] xmake installed to: {xmake_path}")
                self.set_status(f"[OK] XSE_XMAKE_ROOT set to: {xmake_path}")
                
                # Update status orb
                self.update_status_orbs()
            else:
                self.set_status("[ERROR] xmake.exe not found after installation")
                self.set_status("[INFO] Please check the installer output and try again")
                
        except Exception as e:
            self.set_status(f"[ERROR] Failed to verify xmake installation: {e}")

    def open_github_desktop(self):
        """Download and launch GitHub Desktop installer with progress bar and junction symlink setup"""
        main_window = self.window()
        if hasattr(main_window, 'start_progress_operation'):
            def github_desktop_operation(progress_callback, status_callback):
                import requests
                from pathlib import Path
                import subprocess
                import os
                import shutil
                import time
                
                # Check if custom path is set
                custom_path = os.getenv("XSE_GITHUB_DESKTOP_PATH")
                default_path = Path(os.getenv('LOCALAPPDATA', '')) / 'GitHubDesktop'
                
                # Determine target installation path
                if custom_path:
                    target_path = Path(custom_path)
                else:
                    # Use dev root for installation if no custom path
                    dev_root = Path(self.get_dev_root())
                    target_path = dev_root / "GitHubDesktop"
                
                gh_url = "https://central.github.com/deployments/desktop/desktop/latest/win32"
                dev_root = Path(self.get_dev_root())
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                exe_file = dl_dir / "GitHubDesktop-latest.exe"
                
                try:
                    # Check for existing GitHub Desktop installation and remove it
                    if default_path.exists():
                        status_callback("Found existing GitHub Desktop installation, removing it...")
                        
                        # Stop any running GitHub Desktop processes
                        try:
                            status_callback("Stopping GitHub Desktop processes...")
                            subprocess.run(["taskkill", "/f", "/im", "GitHubDesktop.exe"], 
                                         capture_output=True, timeout=10)
                            time.sleep(2)  # Give processes time to close
                            status_callback("GitHub Desktop processes stopped")
                        except Exception as e:
                            status_callback(f"Note: Could not stop GitHub Desktop processes: {e}")
                        
                        try:
                            import shutil
                            shutil.rmtree(default_path)
                            status_callback("Removed existing GitHub Desktop installation")
                        except Exception as e:
                            status_callback(f"Warning: Could not remove existing installation: {e}")
                            status_callback("Continuing with installation...")
                    
                    # Check if installer already exists in downloads
                    if exe_file.exists():
                        status_callback("GitHub Desktop installer found in downloads folder, skipping download...")
                        progress_callback(60, 100)
                    else:
                        # Download installer
                        status_callback("Downloading GitHub Desktop installer...")
                        progress_callback(0, 100)
                        r = requests.get(gh_url, stream=True, timeout=10)
                        total_size = int(r.headers.get('content-length', 0))
                        downloaded = 0
                        with open(exe_file, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        progress = int((downloaded / total_size) * 60)
                                        progress_callback(progress, 100)
                                        status_callback(f"Downloading... {downloaded//1024//1024}MB")
                                    else:
                                        progress_callback(0, 0)
                    
                    status_callback("[OK] GitHub Desktop installer ready. Launching installer...")
                    progress_callback(70, 100)
                    
                    # Launch installer
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.Popen([str(exe_file)], creationflags=creationflags)
                    status_callback(f"[OK] GitHub Desktop installer launched. Complete the setup in the installer window.")
                    progress_callback(80, 100)

                    # Wait for installation to complete and handle path setup
                    status_callback("Waiting for installation to complete...")
                    
                    # Define target path for dev root installation
                    dev_root = Path(self.get_dev_root())
                    target_path = dev_root / "GitHubDesktop"
                    
                    # Check multiple possible locations for installation
                    possible_paths = [
                        default_path / 'GitHubDesktop.exe',
                        target_path / 'GitHubDesktop.exe'
                    ]
                    
                    gh_exe = None
                    installed_path = None
                    
                    # Wait up to 60 seconds for installation
                    for i in range(60):
                        for path in possible_paths:
                            if path.exists():
                                gh_exe = path
                                installed_path = path.parent
                                break
                        if gh_exe:
                            break
                        time.sleep(1)
                        if i % 10 == 0:  # Update status every 10 seconds
                            status_callback(f"Waiting for installation... ({i}s)")
                    
                    if gh_exe and installed_path:
                        status_callback("[OK] GitHub Desktop installed successfully!")
                        progress_callback(90, 100)
                        
                        # Debug: Log the detected paths
                        status_callback(f"Debug: Installed at {installed_path}")
                        status_callback(f"Debug: Default path is {default_path}")
                        status_callback(f"Debug: Custom path is {custom_path}")
                        status_callback(f"Debug: Target path would be {dev_root / 'GitHubDesktop'}")
                        status_callback(f"Debug: String comparison - installed: '{str(installed_path)}' vs default: '{str(default_path)}'")
                        status_callback(f"Debug: Comparison result: {str(installed_path) == str(default_path)}")
                        status_callback(f"Debug: Custom path exists: {custom_path is not None}")
                        
                        # If installation is in default location but we want it in dev root, move it
                        should_move = (str(installed_path) == str(default_path) and not custom_path)
                        status_callback(f"Debug: Should move? {should_move}")
                        
                        if should_move:
                            try:
                                status_callback("Moving installation to dev root...")
                                
                                status_callback(f"Debug: Moving from {installed_path} to {target_path}")
                                
                                # Create target directory
                                target_path.mkdir(parents=True, exist_ok=True)
                                
                                # List what we're moving
                                items_to_move = list(installed_path.iterdir())
                                status_callback(f"Debug: Found {len(items_to_move)} items to move")
                                
                                # Move all files from default location to dev root
                                moved_count = 0
                                for item in items_to_move:
                                    try:
                                        if item.is_file():
                                            shutil.move(str(item), str(target_path / item.name))
                                            moved_count += 1
                                            status_callback(f"Debug: Moved file {item.name}")
                                        elif item.is_dir():
                                            shutil.move(str(item), str(target_path / item.name))
                                            moved_count += 1
                                            status_callback(f"Debug: Moved directory {item.name}")
                                    except Exception as move_error:
                                        status_callback(f"Debug: Failed to move {item.name}: {move_error}")
                                
                                status_callback(f"Debug: Successfully moved {moved_count} items")
                                
                                # Verify the move worked
                                if (target_path / "GitHubDesktop.exe").exists():
                                    # Update paths to use the new location
                                    gh_exe = target_path / "GitHubDesktop.exe"
                                    installed_path = target_path
                                    final_path = str(target_path)
                                    
                                    status_callback(f"Moved GitHub Desktop to: {final_path}")
                                else:
                                    status_callback("Warning: Move completed but GitHubDesktop.exe not found at target")
                                    status_callback(f"Debug: Checking if target path exists: {target_path.exists()}")
                                    if target_path.exists():
                                        status_callback(f"Debug: Target path contents: {list(target_path.iterdir())}")
                                    final_path = str(installed_path)
                                
                            except Exception as e:
                                status_callback(f"Warning: Could not move installation to dev root: {e}")
                                # Fallback to default location
                                final_path = str(installed_path)
                        else:
                            status_callback(f"Debug: Not moving - installed_path != default_path or custom_path exists")
                            final_path = str(installed_path)
                        
                        # Set environment variable and update paths
                        os.environ['XSE_GITHUB_DESKTOP_PATH'] = final_path
                        
                        # Set permanent environment variable
                        try:
                            subprocess.run(["setx", "XSE_GITHUB_DESKTOP_PATH", final_path], 
                                         shell=True, creationflags=creationflags)
                            status_callback(f"Set environment variable: XSE_GITHUB_DESKTOP_PATH={final_path}")
                        except Exception as e:
                            status_callback(f"Warning: Could not set environment variable: {e}")
                        
                        # Update tool path config
                        self.update_tool_path('github_desktop', final_path)
                        
                        # Update EnvVarsPanel if present
                        if hasattr(main_window, 'stack'):
                            for i in range(main_window.stack.count()):
                                panel = main_window.stack.widget(i)
                                if hasattr(panel, 'edits') and 'XSE_GITHUB_DESKTOP_PATH' in getattr(panel, 'edits', {}):
                                    panel.edits['XSE_GITHUB_DESKTOP_PATH'].setText(final_path)
                                    break
                        
                        # Pin to quick launch
                        if hasattr(main_window, 'quick_launch_manager'):
                            qlm = main_window.quick_launch_manager
                            if hasattr(qlm, 'add_quick_launch_item'):
                                qlm.add_quick_launch_item(str(gh_exe))
                        
                        status_callback(f"[SUCCESS] GitHub Desktop installed at: {final_path}")
                        
                        # Refresh status orbs to show updated status
                        self.update_status_orbs()
                        
                    else:
                        status_callback("[WARNING] GitHub Desktop installation not detected. Please check manually.")
                    
                    progress_callback(100, 100)
                except Exception as e:
                    status_callback(f"[ERROR] GitHub Desktop install failed: {e}\nOpening download page...")
                    import webbrowser
                    webbrowser.open("https://desktop.github.com/")
                    progress_callback(100, 100)
                    
            main_window.start_progress_operation("Installing GitHub Desktop", github_desktop_operation)
        else:
            self.set_status("Downloading GitHub Desktop installer...")
            def run():
                import requests
                from pathlib import Path
                import subprocess
                import os
                gh_url = "https://central.github.com/deployments/desktop/desktop/latest/win32"
                dev_root = Path(self.get_dev_root())
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                exe_file = dl_dir / "GitHubDesktop-latest.exe"
                try:
                    r = requests.get(gh_url, stream=True, timeout=10)
                    with open(exe_file, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.set_status("[OK] GitHub Desktop installer downloaded. Launching installer...")
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                    subprocess.Popen([str(exe_file)], creationflags=creationflags)
                    self.set_status(f"[OK] GitHub Desktop installer launched. Complete the setup in the installer window.")
                except Exception as e:
                    self.set_status(f"[ERROR] GitHub Desktop install failed: {e}\nOpening download page...")
                    import webbrowser
                    webbrowser.open("https://desktop.github.com/")
            threading.Thread(target=run).start()

    def install_skse(self):
        """Install SKSE to the dev root tools directory"""
        # Get the main window to access progress widget
        main_window = self.window()
        if hasattr(main_window, 'start_progress_operation'):
            # Show version selection dialog first
            skse_version = self._show_skse_version_dialog()
            if not skse_version:
                self.set_status("[INFO] SKSE installation cancelled by user")
                return
            
            # Use the progress widget for installation
            def skse_install_operation(progress_callback, status_callback):
                import requests
                from pathlib import Path
                import subprocess
                import os
                import zipfile
                import webbrowser
                
                try:
                    # Create SKSE directory in dev root
                    dev_root = Path(self.get_dev_root())
                    skse_path = dev_root / "SKSE"
                    skse_path.mkdir(parents=True, exist_ok=True)
                    
                    status_callback("Preparing SKSE installation...")
                    progress_callback(5, 100)
                    
                    # SKSE download URLs for different versions
                    skse_links = {
                        "1": ("skse64_2_02_06.7z", "https://skse.silverlock.org/beta/skse64_2_02_06.7z", "Anniversary Edition"),
                        "2": ("skse64_2_02_06_gog.7z", "https://skse.silverlock.org/beta/skse64_2_02_06_gog.7z", "Anniversary GOG"),
                        "3": ("skse64_2_00_20.7z", "https://skse.silverlock.org/beta/skse64_2_00_20.7z", "Special Edition"),
                        "4": ("sksevr_2_00_12.7z", "https://skse.silverlock.org/beta/sksevr_2_00_12.7z", "Skyrim VR")
                    }
                    
                    choice = skse_version
                    if choice not in skse_links:
                        status_callback("Invalid choice. Using Anniversary Edition.")
                        choice = "1"
                    
                    filename, url, version_name = skse_links[choice]
                    status_callback(f"Downloading SKSE {version_name}...")
                    progress_callback(10, 100)
                    
                    # Download directory
                    dl_dir = dev_root.parent / "downloads"
                    dl_dir.mkdir(parents=True, exist_ok=True)
                    skse_archive = dl_dir / filename
                    
                    # Check if archive already exists in downloads
                    if skse_archive.exists():
                        status_callback(f"SKSE {version_name} archive found in downloads folder, skipping download...")
                        progress_callback(50, 100)
                    else:
                        # Download SKSE with progress
                        response = requests.get(url, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        
                        with open(skse_archive, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        progress = 10 + int((downloaded / total_size) * 40)  # 10-50%
                                        progress_callback(progress, 100)
                                        status_callback(f"Downloading SKSE... {downloaded//1024//1024}MB")
                                    else:
                                        progress_callback(0, 0)  # Indeterminate
                                        status_callback("Downloading SKSE...")
                        
                        status_callback("Download completed. Extracting...")
                        progress_callback(50, 100)
                    
                    # Extract using 7-Zip - check multiple possible locations
                    possible_7zip_paths = [
                        dev_root / "tools" / "7zip" / "7za.exe",  # dev root tools
                        Path(__file__).parent.parent / "tools" / "7zip" / "7za.exe",  # ClibDT root tools
                        dev_root / "7zip" / "7za.exe",  # dev root direct
                        Path(__file__).parent.parent / "7zip" / "7za.exe",  # ClibDT root direct
                    ]
                    
                    sevenzip_exe = None
                    for path in possible_7zip_paths:
                        status_callback(f"Looking for 7-Zip at: {path}")
                        if path.exists():
                            sevenzip_exe = path
                            status_callback(f"Found 7-Zip at: {sevenzip_exe}")
                            break
                    
                    if not sevenzip_exe:
                        # Try to find 7-Zip in system PATH
                        import shutil
                        status_callback("7-Zip not found in common locations, checking system PATH...")
                        sevenzip_exe = shutil.which("7za")
                        if not sevenzip_exe:
                            sevenzip_exe = shutil.which("7z")
                        if sevenzip_exe:
                            sevenzip_exe = Path(sevenzip_exe)
                            status_callback(f"Found 7-Zip at: {sevenzip_exe}")
                        else:
                            status_callback("7-Zip not found in system PATH")
                    
                    if sevenzip_exe and sevenzip_exe.exists():
                        status_callback(f"Using 7-Zip: {sevenzip_exe}")
                        # Extract to temporary directory
                        tmp_extract_dir = skse_path / "_skse_tmp"
                        tmp_extract_dir.mkdir(parents=True, exist_ok=True)
                        
                        status_callback("Extracting SKSE archive...")
                        progress_callback(60, 100)
                        
                        ret = subprocess.run([
                            str(sevenzip_exe), "x", str(skse_archive),
                            f"-o{tmp_extract_dir}", "-y", "-aoa"
                        ], check=True, capture_output=True, text=True)
                        
                        status_callback("Archive extracted. Processing files...")
                        progress_callback(70, 100)
                        
                        # Find SKSE subfolder
                        inner_skse_dir = None
                        for sub in tmp_extract_dir.iterdir():
                            if sub.is_dir() and (sub / "skse64_loader.exe").exists():
                                inner_skse_dir = sub
                                break
                            elif sub.is_dir() and (sub / "skse").is_dir():
                                inner_skse_dir = sub / "skse"
                                break
                        
                        if inner_skse_dir and inner_skse_dir.exists():
                            # Move files to SKSE directory
                            status_callback("Moving SKSE files...")
                            progress_callback(80, 100)
                            
                            for item in inner_skse_dir.iterdir():
                                dest = skse_path / item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        import shutil
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                import shutil
                                shutil.move(str(item), str(dest))
                            
                            status_callback("Files moved successfully.")
                            progress_callback(85, 100)
                        else:
                            raise Exception("Could not find valid SKSE subfolder in archive.")
                        
                        # Clean up temp directory
                        import shutil
                        shutil.rmtree(tmp_extract_dir)
                    else:
                        # Provide helpful error message with installation instructions
                        status_callback("7-Zip is required to extract SKSE.")
                        status_callback("Please install 7-Zip from: https://7-zip.org/")
                        status_callback("Or install it through the 'Install Custom Tool' option with URL:")
                        status_callback("https://7-zip.org/a/7z2301-x64.exe")
                        raise Exception("7-Zip not found. Please install 7-Zip to extract SKSE archives.")
                    
                    # Verify installation
                    status_callback("Verifying installation...")
                    progress_callback(90, 100)
                    
                    try:
                        skse_loader = None
                        for fname in ["skse_loader.exe", "skse64_loader.exe"]:
                            found = list(skse_path.glob(fname))
                            if found:
                                skse_loader = found[0]
                                status_callback(f"Found SKSE loader: {skse_loader.name}")
                                break
                        
                        if skse_loader:
                            status_callback("Setting environment variables...")
                            
                            # Set environment variable
                            os.environ["XSE_TES5_GAME_PATH"] = str(skse_path)
                            
                            # Try to set system environment variable (may fail without admin rights)
                            try:
                                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                                subprocess.run(["setx", "XSE_TES5_GAME_PATH", str(skse_path)], shell=True, creationflags=creationflags, timeout=10)
                                status_callback("System environment variable set successfully")
                            except Exception as env_error:
                                status_callback(f"Warning: Could not set system environment variable: {env_error}")
                                status_callback("You may need to run as administrator to set system variables")
                            
                            status_callback(f"SKSE installed to: {skse_path}")
                            status_callback(f"XSE_TES5_GAME_PATH set to: {skse_path}")
                            
                            # Save to tool paths config
                            try:
                                self.update_tool_path("skse", str(skse_loader))
                                status_callback("Tool path saved to configuration")
                            except Exception as config_error:
                                status_callback(f"Warning: Could not save tool path: {config_error}")
                            
                            # Update status orb
                            try:
                                self.update_status_orbs()
                                status_callback("Status orbs updated")
                            except Exception as orb_error:
                                status_callback(f"Warning: Could not update status orbs: {orb_error}")
                            
                            status_callback("Installation completed successfully!")
                            progress_callback(100, 100)
                            
                            # Clean up downloaded file
                            try:
                                skse_archive.unlink(missing_ok=True)
                                status_callback("Downloaded archive cleaned up")
                            except Exception as cleanup_error:
                                status_callback(f"Warning: Could not clean up archive: {cleanup_error}")
                            
                            return str(skse_path)
                        else:
                            # List what files were actually found for debugging
                            found_files = list(skse_path.glob("*"))
                            status_callback(f"Files found in SKSE directory: {[f.name for f in found_files]}")
                            raise Exception("skse_loader.exe not found after extraction.")
                    
                    except Exception as verify_error:
                        status_callback(f"Verification failed: {verify_error}")
                        raise Exception(f"Installation verification failed: {verify_error}")
                    
                except Exception as e:
                    status_callback(f"Installation failed: {e}")
                    # Don't automatically open browser - let user decide
                    status_callback("You can manually download SKSE from: https://skse.silverlock.org/")
                    # Don't re-raise the exception - just return None to indicate failure
                    return None
            
            # Start the progress operation with error handling
            try:
                main_window.start_progress_operation("Installing SKSE", skse_install_operation)
            except Exception as e:
                self.set_status(f"[ERROR] Failed to start SKSE installation: {e}")
                # Fallback to terminal output
                self.set_status("[INFO] Installation failed. Check terminal for details.")
        else:
            # Fallback to old method if progress widget not available
            self.set_status("Installing SKSE...")
            def run():
                import requests
                from pathlib import Path
                import subprocess
                import os
                import zipfile
                import webbrowser
                
                # Create SKSE directory in dev root
                dev_root = Path(self.get_dev_root())
                skse_path = dev_root / "SKSE"
                skse_path.mkdir(parents=True, exist_ok=True)
                
                # SKSE download URLs for different versions
                skse_links = {
                    "1": ("skse64_2_02_06.7z", "https://skse.silverlock.org/beta/skse64_2_02_06.7z", "Anniversary Edition"),
                    "2": ("skse64_2_02_06_gog.7z", "https://skse.silverlock.org/beta/skse64_2_02_06_gog.7z", "Anniversary GOG"),
                    "3": ("skse64_2_00_20.7z", "https://skse.silverlock.org/beta/skse64_2_00_20.7z", "Special Edition"),
                    "4": ("sksevr_2_00_12.7z", "https://skse.silverlock.org/beta/sksevr_2_00_12.7z", "Skyrim VR")
                }
                
                # Show version selection
                self.set_status("Select SKSE version:")
                self.set_status("1. Anniversary Edition (AE)")
                self.set_status("2. Anniversary GOG")
                self.set_status("3. Special Edition (SE)")
                self.set_status("4. Skyrim VR")
                
                # For now, default to Anniversary Edition (fallback method doesn't have dialog)
                choice = "1"
                self.set_status("[INFO] Using Anniversary Edition (AE) - use progress widget for version selection")
                if choice not in skse_links:
                    self.set_status("[ERROR] Invalid choice. Using Anniversary Edition.")
                    choice = "1"
                
                filename, url, version_name = skse_links[choice]
                self.set_status(f"Downloading SKSE {version_name}...")
                
                # Download directory
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                skse_archive = dl_dir / filename
                
                try:
                    # Download SKSE
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(skse_archive, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    self.set_status("[OK] SKSE downloaded. Extracting...")
                    
                    # Extract using 7-Zip - check multiple possible locations
                    possible_7zip_paths = [
                        dev_root / "tools" / "7zip" / "7za.exe",  # dev root tools
                        Path(__file__).parent.parent / "tools" / "7zip" / "7za.exe",  # ClibDT root tools
                        dev_root / "7zip" / "7za.exe",  # dev root direct
                        Path(__file__).parent.parent / "7zip" / "7za.exe",  # ClibDT root direct
                    ]
                    
                    sevenzip_exe = None
                    for path in possible_7zip_paths:
                        if path.exists():
                            sevenzip_exe = path
                            break
                    
                    if not sevenzip_exe:
                        # Try to find 7-Zip in system PATH
                        import shutil
                        sevenzip_exe = shutil.which("7za")
                        if not sevenzip_exe:
                            sevenzip_exe = shutil.which("7z")
                        if sevenzip_exe:
                            sevenzip_exe = Path(sevenzip_exe)
                    
                    if sevenzip_exe and sevenzip_exe.exists():
                        # Extract to temporary directory
                        tmp_extract_dir = skse_path / "_skse_tmp"
                        tmp_extract_dir.mkdir(parents=True, exist_ok=True)
                        
                        ret = subprocess.run([
                            str(sevenzip_exe), "x", str(skse_archive),
                            f"-o{tmp_extract_dir}", "-y", "-aoa"
                        ], check=True, capture_output=True, text=True)
                        
                        self.set_status("[OK] SKSE archive extracted to temp folder.")
                        
                        # Find SKSE subfolder
                        inner_skse_dir = None
                        for sub in tmp_extract_dir.iterdir():
                            if sub.is_dir() and (sub / "skse64_loader.exe").exists():
                                inner_skse_dir = sub
                                break
                            elif sub.is_dir() and (sub / "skse").is_dir():
                                inner_skse_dir = sub / "skse"
                                break
                        
                        if inner_skse_dir and inner_skse_dir.exists():
                            # Move files to SKSE directory
                            for item in inner_skse_dir.iterdir():
                                dest = skse_path / item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        import shutil
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                import shutil
                                shutil.move(str(item), str(dest))
                            
                            self.set_status("[OK] SKSE files moved to SKSE folder.")
                        else:
                            self.set_status("[ERROR] Could not find valid SKSE subfolder in archive.")
                            return
                        
                        # Clean up temp directory
                        import shutil
                        shutil.rmtree(tmp_extract_dir)
                    else:
                        self.set_status("[ERROR] 7-Zip not found. Cannot extract SKSE.")
                        return
                    
                    # Verify installation
                    skse_loader = None
                    for fname in ["skse_loader.exe", "skse64_loader.exe"]:
                        found = list(skse_path.glob(fname))
                        if found:
                            skse_loader = found[0]
                            break
                    
                    if skse_loader:
                        # Set environment variable
                        os.environ["XSE_TES5_GAME_PATH"] = str(skse_path)
                        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                        subprocess.run(["setx", "XSE_TES5_GAME_PATH", str(skse_path)], shell=True, creationflags=creationflags)
                        self.set_status(f"[OK] SKSE installed to: {skse_path}")
                        self.set_status(f"[OK] XSE_TES5_GAME_PATH set to: {skse_path}")
                        # Update status orb
                        self.update_status_orbs()
                    else:
                        self.set_status("[ERROR] skse_loader.exe not found after extraction.")
                    
                    # Clean up downloaded file
                    skse_archive.unlink(missing_ok=True)
                    
                except Exception as e:
                    self.set_status(f"[ERROR] SKSE installation failed: {e}")
                    self.set_status("[INFO] You can manually download SKSE from: https://skse.silverlock.org/")
                    # Log the full error for debugging but don't crash
                    import traceback
                    self.set_status(f"[DEBUG] Full error: {traceback.format_exc()}")
            
            threading.Thread(target=run).start()

    def _show_skse_version_dialog(self):
        """Show a dialog to select SKSE version"""
        
        class SKSEVersionDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Select SKSE Version")
                self.setModal(True)
                self.setFixedSize(450, 350)
                
                # Get theme from parent
                theme = None
                if parent and hasattr(parent, 'theme_manager') and parent.theme_manager:
                    theme = parent.theme_manager.get_theme()
                elif parent and hasattr(parent, 'window') and parent.window() and hasattr(parent.window(), 'theme_manager') and parent.window().theme_manager:
                    theme = parent.window().theme_manager.get_theme()
                
                if not theme:
                    # Fallback theme
                    theme = {
                        'window_bg': '#1e1e1e',
                        'bg_primary': '#2d2d2d',
                        'text_primary': '#e0e0e0',
                        'text_secondary': '#b0b0b0',
                        'button_bg': '#0078d4',
                        'button_hover': '#106ebe',
                        'input_border': '#404040'
                    }
                
                layout = QVBoxLayout()
                layout.setSpacing(20)
                layout.setContentsMargins(24, 28, 24, 24)
                
                # Title
                title = QLabel("Select SKSE Version")
                title.setStyleSheet(f"""
                    font-size: 16px;
                    font-weight: bold;
                    color: {theme['text_primary']};
                    margin-bottom: 20px;
                    padding: 12px 0px;
                    background: transparent;
                    min-height: 24px;
                """)
                layout.addWidget(title)
                
                # Description
                desc = QLabel("Choose the SKSE version that matches your Skyrim installation:")
                desc.setStyleSheet(f"""
                    color: {theme['text_secondary']};
                    font-size: 11px;
                    margin-bottom: 16px;
                """)
                layout.addWidget(desc)
                
                # Radio buttons
                self.button_group = QButtonGroup()
                self.selected_version = "1"  # Default to Anniversary Edition
                
                versions = [
                    ("1", "Anniversary Edition (AE)"),
                    ("2", "Anniversary GOG"),
                    ("3", "Special Edition (SE)"),
                    ("4", "Skyrim VR")
                ]
                
                for version_id, title_text in versions:
                    radio = QRadioButton(title_text)
                    radio.setProperty("version_id", version_id)
                    radio.setStyleSheet(f"""
                        QRadioButton {{
                            color: {theme['text_primary']} !important;
                            font-size: 12px !important;
                            font-weight: bold !important;
                            margin: 12px 0px !important;
                            padding: 8px 0px !important;
                            background: transparent !important;
                            min-height: 20px !important;
                        }}
                        QRadioButton::indicator {{
                            width: 16px;
                            height: 16px;
                            margin-right: 8px;
                        }}
                        QRadioButton::indicator:unchecked {{
                            border: 2px solid {theme['input_border']};
                            background-color: {theme['bg_primary']};
                            border-radius: 8px;
                        }}
                        QRadioButton::indicator:checked {{
                            border: 2px solid {theme['button_bg']};
                            background-color: {theme['button_bg']};
                            border-radius: 8px;
                        }}
                    """)
                    
                    self.button_group.addButton(radio)
                    layout.addWidget(radio)
                    
                    # Set default selection
                    if version_id == "1":
                        radio.setChecked(True)
                
                # Connect button group
                self.button_group.buttonClicked.connect(self.on_version_selected)
                
                # Buttons
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                
                cancel_btn = QPushButton("Cancel")
                cancel_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme['bg_primary']};
                        color: {theme['text_primary']};
                        border: 1px solid {theme['input_border']};
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme['input_border']};
                    }}
                """)
                cancel_btn.clicked.connect(self.reject)
                button_layout.addWidget(cancel_btn)
                
                ok_btn = QPushButton("Install")
                ok_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme['button_bg']};
                        color: white;
                        border: 1px solid {theme['button_bg']};
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {theme['button_hover']};
                        border-color: {theme['button_hover']};
                    }}
                """)
                ok_btn.clicked.connect(self.accept)
                button_layout.addWidget(ok_btn)
                
                layout.addLayout(button_layout)
                
                # Apply theme to dialog
                self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {theme['window_bg']};
                        color: {theme['text_primary']};
                    }}
                    QLabel {{
                        color: {theme['text_primary']};
                        background: transparent;
                    }}
                """)
                
                self.setLayout(layout)
            
            def on_version_selected(self, button):
                self.selected_version = button.property("version_id")
            
            def get_selected_version(self):
                return self.selected_version
        
        # Show dialog
        dialog = SKSEVersionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_version()
        else:
            return None

    def install_custom_tool(self):
        """Install a custom tool from a direct download URL"""
        url = self.url_input.text().strip()
        if not url:
            self.set_status("[ERROR] Please enter a download URL.")
            return
        
        if not url.startswith(('http://', 'https://')):
            self.set_status("[ERROR] Please enter a valid HTTP/HTTPS URL.")
            return
        
        self.set_status(f"Downloading custom tool from: {url}")
        
        def run():
            import requests
            from pathlib import Path
            import subprocess
            import os
            import zipfile
            import tarfile
            from urllib.parse import urlparse
            
            try:
                # Create downloads directory
                dev_root = Path(self.get_dev_root())
                dl_dir = dev_root.parent / "downloads"
                dl_dir.mkdir(parents=True, exist_ok=True)
                
                # Extract filename from URL
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = "custom_tool.zip"  # Default fallback
                
                # Download file
                self.set_status(f"Downloading {filename}...")
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                file_path = dl_dir / filename
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.set_status(f"[OK] Downloaded {filename}. Extracting...")
                
                # Determine extraction method based on file extension
                file_ext = file_path.suffix.lower()
                
                # Create tools directory
                tools_dir = dev_root / "tools"
                tools_dir.mkdir(parents=True, exist_ok=True)
                
                if file_ext in ['.exe', '.msi']:
                    # For executables, try silent installation to tools folder first
                    self.set_status(f"[OK] Attempting silent installation of: {filename}")
                    
                    # Create tools directory
                    tools_dir = dev_root / "tools"
                    tools_dir.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        # Try common silent installation arguments
                        silent_args = []
                        
                        if file_ext == '.exe':
                            # Common silent installation arguments for .exe files
                            silent_args = [
                                ["/S", "/D=" + str(tools_dir)],  # NSIS-style
                                ["/silent", "/dir=" + str(tools_dir)],  # Inno Setup-style
                                ["-q", "-dir=" + str(tools_dir)],  # Some installers
                                ["/VERYSILENT", "/DIR=" + str(tools_dir)],  # Inno Setup
                                ["/S", "/D=" + str(tools_dir)],  # Generic silent
                                ["--silent", "--prefix=" + str(tools_dir)],  # Some tools
                                ["/quiet", "/norestart", "/log=" + str(tools_dir / "install.log")],  # MSI-style
                            ]
                        elif file_ext == '.msi':
                            # MSI silent installation
                            silent_args = [
                                ["/quiet", "/norestart", f"INSTALLDIR={tools_dir}"],
                                ["/passive", "/norestart", f"INSTALLDIR={tools_dir}"],
                                ["/qn", "/norestart", f"INSTALLDIR={tools_dir}"],
                            ]
                        
                        # Try each set of arguments
                        success = False
                        for args in silent_args:
                            try:
                                self.set_status(f"[INFO] Trying: {filename} {' '.join(args)}")
                                result = subprocess.run(
                                    [str(file_path)] + args,
                                    timeout=300,  # 5 minute timeout
                                    capture_output=True,
                                    text=True,
                                    shell=False
                                )
                                
                                if result.returncode == 0:
                                    self.set_status(f"[OK] Silent installation successful!")
                                    success = True
                                    break
                                else:
                                    self.set_status(f"[INFO] Silent install failed (code {result.returncode}), trying next method...")
                                    
                            except subprocess.TimeoutExpired:
                                self.set_status(f"[INFO] Installation timed out, trying next method...")
                                continue
                            except Exception as e:
                                self.set_status(f"[INFO] Silent install error: {e}, trying next method...")
                                continue
                        
                        if not success:
                            # If all silent methods failed, launch with GUI
                            self.set_status(f"[INFO] Silent installation failed. Launching installer GUI...")
                            creationflags = 0
                            if sys.platform.startswith("win"):
                                creationflags = subprocess.CREATE_NO_WINDOW
                            subprocess.Popen([str(file_path)], shell=True, creationflags=creationflags)
                            self.set_status(f"[OK] Installer launched. Complete the installation in the installer window.")
                            self.set_status(f"[INFO] Suggested installation path: {tools_dir}")
                        
                    except Exception as e:
                        self.set_status(f"[ERROR] Failed to launch installer: {e}")
                        # Fallback to GUI launch
                        try:
                            creationflags = 0
                            if sys.platform.startswith("win"):
                                creationflags = subprocess.CREATE_NO_WINDOW
                            subprocess.Popen([str(file_path)], shell=True, creationflags=creationflags)
                            self.set_status(f"[OK] Installer launched with GUI fallback.")
                        except Exception as e2:
                            self.set_status(f"[ERROR] GUI fallback also failed: {e2}")
                    
                elif file_ext in ['.zip', '.tar', '.tar.gz', '.tgz', '.7z']:
                    # For archives, extract to a new folder
                    # Create a folder name based on the filename (without extension)
                    folder_name = file_path.stem
                    if folder_name.lower() in ['tool', 'custom_tool']:
                        # Generate a more descriptive name
                        folder_name = f"custom_tool_{int(time.time())}"
                    
                    # Create temporary extraction directory
                    temp_extract_dir = tools_dir / f"temp_{folder_name}"
                    temp_extract_dir.mkdir(parents=True, exist_ok=True)
                    
                    if file_ext == '.zip':
                        # Extract ZIP file to temp directory
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_extract_dir)
                        
                    elif file_ext in ['.tar', '.tar.gz', '.tgz']:
                        # Extract TAR file to temp directory
                        with tarfile.open(file_path, 'r:*') as tar_ref:
                            tar_ref.extractall(temp_extract_dir)
                        
                    elif file_ext == '.7z':
                        # Extract 7Z file using 7-Zip if available
                        sevenzip_exe = dev_root / "7zip" / "7za.exe"
                        if sevenzip_exe.exists():
                            # Ensure the output directory exists
                            temp_extract_dir.mkdir(parents=True, exist_ok=True)
                            try:
                                # Use absolute paths and ensure proper formatting
                                sevenzip_cmd = str(sevenzip_exe)
                                file_path_str = str(file_path.absolute())
                                output_path_str = str(temp_extract_dir.absolute())
                                
                                ret = subprocess.run([
                                    sevenzip_cmd, "x", file_path_str,
                                    f"-o{output_path_str}", "-y", "-aoa"
                                ], check=True, capture_output=True, text=True, shell=False)
                            except subprocess.CalledProcessError as e:
                                self.set_status(f"[ERROR] 7-Zip extraction failed: {e}")
                                self.set_status(f"[DEBUG] Command: {sevenzip_cmd} x {file_path_str} -o{output_path_str} -y -aoa")
                                self.set_status(f"[DEBUG] Output: {e.stdout}")
                                self.set_status(f"[DEBUG] Error: {e.stderr}")
                                return
                        else:
                            self.set_status(f"[ERROR] 7-Zip not found. Cannot extract {filename}")
                            return
                    
                    # Now handle the extracted contents
                    final_dir = tools_dir / folder_name
                    
                    # Check what was extracted
                    extracted_items = list(temp_extract_dir.iterdir())
                    
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        # Single directory extracted - this is likely the tool folder
                        single_dir = extracted_items[0]
                        if single_dir.name.lower() in ['tools', 'bin', 'lib', 'include']:
                            # Move contents of this directory to final location
                            import shutil
                            for item in single_dir.iterdir():
                                dest = final_dir / item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                shutil.move(str(item), str(dest))
                            # Remove the empty single directory
                            shutil.rmtree(single_dir)
                        else:
                            # Move the single directory to final location
                            import shutil
                            if final_dir.exists():
                                shutil.rmtree(final_dir)
                            shutil.move(str(single_dir), str(final_dir))
                    else:
                        # Multiple items or files - move everything to final location
                        import shutil
                        for item in extracted_items:
                            dest = final_dir / item.name
                            if dest.exists():
                                if dest.is_dir():
                                    shutil.rmtree(dest)
                                else:
                                    dest.unlink()
                            shutil.move(str(item), str(dest))
                    
                    # Clean up temp directory
                    import shutil
                    shutil.rmtree(temp_extract_dir)
                    
                    self.set_status(f"[OK] Extracted {filename} to {final_dir}")
                    
                else:
                    # Unknown format, try to extract as ZIP first
                    try:
                        folder_name = file_path.stem
                        if folder_name.lower() in ['tool', 'custom_tool']:
                            folder_name = f"custom_tool_{int(time.time())}"
                        
                        # Create temporary extraction directory
                        temp_extract_dir = tools_dir / f"temp_{folder_name}"
                        temp_extract_dir.mkdir(parents=True, exist_ok=True)
                        
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_extract_dir)
                        
                        # Now handle the extracted contents
                        final_dir = tools_dir / folder_name
                        
                        # Check what was extracted
                        extracted_items = list(temp_extract_dir.iterdir())
                        
                        if len(extracted_items) == 1 and extracted_items[0].is_dir():
                            # Single directory extracted - this is likely the tool folder
                            single_dir = extracted_items[0]
                            if single_dir.name.lower() in ['tools', 'bin', 'lib', 'include']:
                                # Move contents of this directory to final location
                                import shutil
                                for item in single_dir.iterdir():
                                    dest = final_dir / item.name
                                    if dest.exists():
                                        if dest.is_dir():
                                            shutil.rmtree(dest)
                                        else:
                                            dest.unlink()
                                    shutil.move(str(item), str(dest))
                                # Remove the empty single directory
                                shutil.rmtree(single_dir)
                            else:
                                # Move the single directory to final location
                                import shutil
                                if final_dir.exists():
                                    shutil.rmtree(final_dir)
                                shutil.move(str(single_dir), str(final_dir))
                        else:
                            # Multiple items or files - move everything to final location
                            import shutil
                            for item in extracted_items:
                                dest = final_dir / item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                shutil.move(str(item), str(dest))
                        
                        # Clean up temp directory
                        import shutil
                        shutil.rmtree(temp_extract_dir)
                        
                        self.set_status(f"[OK] Extracted {filename} to {final_dir}")
                    except:
                        # If ZIP extraction fails, just move the file to tools
                        dest_path = tools_dir / filename
                        import shutil
                        shutil.move(str(file_path), str(dest_path))
                        self.set_status(f"[OK] Moved {filename} to {tools_dir}")
                
                # Clean up downloaded file (except for executables that need to run)
                if file_ext not in ['.exe', '.msi']:
                    try:
                        file_path.unlink()
                    except:
                        pass
                else:
                    self.set_status(f"[INFO] Installer file kept at: {file_path}")
                
                self.set_status(f"[OK] Custom tool installation complete!")
                self.url_input.clear()
                
            except Exception as e:
                self.set_status(f"[ERROR] Custom tool installation failed: {e}")
        
        threading.Thread(target=run).start()

    def load_tool_paths_config(self):
        """Load tool paths configuration from storage"""
        try:
            import json
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_tool_paths_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.tool_paths_config = json.load(f)
            else:
                # Initialize with default empty config
                self.tool_paths_config = {
                    'vs_buildtools_path': None,
                    'xmake_path': None,
                    'git_path': None,
                    'skse_path': None,
                    'github_desktop_path': None,
                    'clibdt_version': VERSION
                }
        except Exception as e:
            self.set_status(f"[WARN] Could not load tool paths config: {e}")
            # Initialize with default empty config
            self.tool_paths_config = {
                'vs_buildtools_path': None,
                'xmake_path': None,
                'git_path': None,
                'skse_path': None,
                'github_desktop_path': None,
                'clibdt_version': VERSION
            }

    def save_tool_paths_config(self):
        """Save tool paths configuration to storage"""
        try:
            import json
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_tool_paths_config.json"
            
            # Update version
            self.tool_paths_config['clibdt_version'] = VERSION
            
            with open(config_file, 'w') as f:
                json.dump(self.tool_paths_config, f, indent=2)
        except Exception as e:
            self.set_status(f"[WARN] Could not save tool paths config: {e}")

    def update_tool_path(self, tool_name, path):
        """Update a tool path in the configuration"""
        if path and Path(path).exists():
            self.tool_paths_config[f'{tool_name}_path'] = str(path)
            self.save_tool_paths_config()
            self.set_status(f"[OK] Updated {tool_name} path: {path}")

    def load_pinned_items(self):
        """Load pinned items from storage"""
        try:
            import json
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_launcher_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.pinned_items = data.get('pinned_items', [])
        except Exception as e:
            self.set_status(f"[WARN] Could not load launcher config: {e}")

    def save_pinned_items(self):
        """Save pinned items to storage"""
        try:
            import json
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_launcher_config.json"
            with open(config_file, 'w') as f:
                json.dump({'pinned_items': self.pinned_items}, f, indent=2)
        except Exception as e:
            self.set_status(f"[WARN] Could not save launcher config: {e}")



    def launch_file(self, file_path):
        """Launch a file with appropriate method"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.set_status(f"[ERROR] File not found: {file_path}")
                return
            
            # Determine how to launch based on file extension
            ext = path.suffix.lower()
            
            # Set creation flags to prevent terminal popups
            creationflags = 0
            if sys.platform.startswith("win"):
                creationflags = subprocess.CREATE_NO_WINDOW
            
            if ext in ['.exe', '.bat', '.cmd']:
                # Launch executable directly
                subprocess.Popen([str(path)], shell=True, creationflags=creationflags)
                self.set_status(f"[OK] Launched: {path.name}")
                
            elif ext in ['.py']:
                # Launch Python script
                subprocess.Popen([sys.executable, str(path)], shell=True, creationflags=creationflags)
                self.set_status(f"[OK] Launched Python script: {path.name}")
                
            elif ext in ['.msi']:
                # Launch MSI installer
                subprocess.Popen(['msiexec', '/i', str(path)], shell=True, creationflags=creationflags)
                self.set_status(f"[OK] Launched MSI installer: {path.name}")
                
            else:
                # Try to open with default application
                import os
                os.startfile(str(path))
                self.set_status(f"[OK] Opened with default app: {path.name}")
                
        except Exception as e:
            self.set_status(f"[ERROR] Failed to launch {file_path}: {e}")

    def apply_theme(self):
        """Apply current theme to the panel"""
        if self.theme_manager:
            self.setStyleSheet(self.theme_manager.get_install_tools_style())
        else:
            # Fallback to basic theme if no theme manager
            try:
                from modules.theme_manager import ThemeManager
                fallback_manager = ThemeManager()
                self.setStyleSheet(fallback_manager.get_install_tools_style())
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
        
        # Status orbs will be updated when user clicks "Check Paths" button

    @pyqtSlot()
    def show_xmake_path_dialog(self):
        """Show a dialog with xmake installation path"""
        
        class XmakePathDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Xmake Installation Path")
                self.setModal(True)
                self.setFixedSize(450, 150)
                
                # Get theme from parent
                theme = None
                if parent and hasattr(parent, 'theme_manager') and parent.theme_manager:
                    theme = parent.theme_manager.get_theme()
                elif parent and hasattr(parent, 'window') and parent.window() and hasattr(parent.window(), 'theme_manager') and parent.window().theme_manager:
                    theme = parent.window().theme_manager.get_theme()
                
                if not theme:
                    # Fallback theme
                    theme = {
                        'window_bg': '#1e1e1e',
                        'bg_primary': '#2d2d2d',
                        'text_primary': '#e0e0e0',
                        'text_secondary': '#b0b0b0',
                        'button_bg': '#0078d4',
                        'button_hover': '#106ebe',
                        'input_border': '#404040'
                    }
                
                layout = QVBoxLayout()
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # Title
                title = QLabel("Install xmake to this path:")
                # Invert the theme for the dialog
                if theme['window_bg'] == '#1e1e1e':  # dark theme
                    bg = '#f8f9fa'
                    fg = '#212529'
                    input_bg = '#ffffff'
                    border = '#ced4da'
                    button_bg = '#007bff'
                    button_hover = '#0056b3'
                else:  # light theme
                    bg = '#1e1e1e'
                    fg = '#e0e0e0'
                    input_bg = '#2d2d2d'
                    border = '#404040'
                    button_bg = '#0078d4'
                    button_hover = '#106ebe'
                self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {bg};
                    }}
                """)
                title.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: bold;
                    color: {fg};
                    margin-bottom: 10px;
                """)
                layout.addWidget(title)
                
                # Path input with copy button
                path_layout = QHBoxLayout()
                path_layout.setSpacing(10)
                
                # Get the xmake path from environment variables or use default
                xmake_root = os.getenv("XSE_XMAKE_ROOT")
                if not xmake_root:
                    # Fallback to dev root if not set
                    dev_root = Path(parent.get_dev_root()) if parent else Path.home()
                    xmake_path = dev_root / "tools" / "xmake"
                    xmake_root = str(xmake_path)
                
                path_input = QLineEdit()
                path_input.setText(xmake_root)
                path_input.setReadOnly(True)
                path_input.setMinimumHeight(32)
                path_input.setStyleSheet(f"""
                    QLineEdit {{
                        background-color: {input_bg};
                        color: {fg};
                        border: 2px solid {border};
                        border-radius: 4px;
                        padding: 8px;
                        font-family: 'Consolas', monospace;
                        font-size: 11px;
                    }}
                """)
                path_layout.addWidget(path_input)
                
                # Copy button
                copy_button = QPushButton("Copy Path")
                copy_button.setFixedWidth(110)
                copy_button.clicked.connect(lambda: QApplication.clipboard().setText(path_input.text()))
                copy_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {button_bg};
                        color: white;
                        border: none;
                        padding: 8px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {button_hover};
                    }}
                """)
                path_layout.addWidget(copy_button)
                
                layout.addLayout(path_layout)
                
                # OK button
                ok_button = QPushButton("OK")
                ok_button.clicked.connect(self.accept)
                ok_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #28a745;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #218838;
                    }}
                """)
                layout.addWidget(ok_button)
                
                self.setLayout(layout)
                
                # Center the dialog over the parent window
                if parent and parent.isVisible():
                    parent_rect = parent.frameGeometry()
                    dialog_rect = self.frameGeometry()
                    center_point = parent_rect.center()
                    dialog_rect.moveCenter(center_point)
                    self.move(dialog_rect.topLeft())
                else:
                    # Fallback: center on screen
                    self.move(self.screen().geometry().center() - self.rect().center())
        
        # Show the dialog
        dialog = XmakePathDialog(self)
        return dialog.exec()





