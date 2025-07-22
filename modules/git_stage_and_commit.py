import os
import subprocess
from colorama import init, Fore, Style
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QLineEdit, QTextEdit, QFrame, QGroupBox, QCheckBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

class GitCommitThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, commit_message, status_callback=None):
        super().__init__()
        self.commit_message = commit_message
        self.status_callback = status_callback
    
    def run(self):
        try:
            def status(msg):
                self.progress_signal.emit(msg)
                if self.status_callback:
                    self.status_callback(msg)
            
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
                
        except Exception as e:
            self.finished_signal.emit(False, f"Git operation failed: {e}")

class GitCommitPanel(QWidget):
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.commit_thread = None
        self.theme_manager = theme_manager
        self.init_ui()
    
    def init_ui(self):
        # Main layout with proper spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Git Stage & Commit")
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
        desc = QLabel("Stage all changes and commit them to the git repository.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        
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

        # Button row with proper spacing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Commit button
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.setProperty("btnType", "success")
        self.commit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.commit_btn.setFixedHeight(32)
        self.commit_btn.clicked.connect(self.start_commit)
        self.commit_btn.setToolTip("Stage and commit all changes")
        btn_row.addWidget(self.commit_btn)
        
        layout.addLayout(btn_row)
        
        # Add stretch to prevent content from expanding to fill available space
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
            GitCommitPanel,
            GitCommitPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            GitCommitPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Main title - largest and most prominent */
            GitCommitPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
            }}
            
            /* Color-coded section titles */
            GitCommitPanel QLabel#custom_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['info_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            GitCommitPanel QLabel#success_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['success_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            GitCommitPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            /* Section descriptions */
            GitCommitPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            /* Divider lines */
            GitCommitPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* LineEdit styling - responsive resizing */
            GitCommitPanel QLineEdit,
            GitCommitPanel QLineEdit:hover,
            GitCommitPanel QLineEdit:focus {{
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
            
            GitCommitPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            GitCommitPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* CheckBox styling - transparent background */
            GitCommitPanel QCheckBox {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                spacing: 8px !important;
                padding: 2px 0px !important;
                background: transparent !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            GitCommitPanel QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                border: 2px solid {theme['input_border']} !important;
                background-color: {theme['input_bg']} !important;
                border-radius: 3px !important;
            }}
            
            GitCommitPanel QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']} !important;
                border-color: {theme['button_bg']} !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
            }}
            
            GitCommitPanel QCheckBox:hover::indicator:unchecked {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            /* Base button styling for all states */
            GitCommitPanel QPushButton,
            GitCommitPanel QPushButton:hover,
            GitCommitPanel QPushButton:pressed,
            GitCommitPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            /* General disabled button styling (applies to ALL button types) */
            GitCommitPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons - Green theme with bright hover effects */
            GitCommitPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            GitCommitPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            GitCommitPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
        """)
    
    def start_commit(self):
        commit_msg = self.commit_msg_edit.text().strip()
        if not commit_msg:
            self.status("[ERROR] Please enter a commit message.")
            return
        
        self.commit_btn.setEnabled(False)
        self.status("=== Starting Git Commit ===")
        
        # Start commit thread
        self.commit_thread = GitCommitThread(
            commit_message=commit_msg,
            status_callback=self.status
        )
        self.commit_thread.progress_signal.connect(self.status)
        self.commit_thread.finished_signal.connect(self.commit_finished)
        self.commit_thread.start()
    
    def commit_finished(self, success, message):
        self.commit_btn.setEnabled(True)
        
        if success:
            self.status(f"[SUCCESS] {message}")
            # Clear the commit message for next time
            self.commit_msg_edit.setText("Commit")
        else:
            self.status(f"[ERROR] {message}")
    
    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

def run_git_commit():
    """CLI version of git commit for backward compatibility"""
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set. Cannot continue.", Fore.RED)
        input("Press Enter to return...")
        return

    #----------Automatic Git init----------
    cprint("  🔧 Initializing Git repository...", Fore.CYAN)
    subprocess.run(["git", "init"], capture_output=True, text=True)

    #----------Stage all changes----------
    cprint("  📝 Staging files...", Fore.CYAN)
    subprocess.run(["git", "add", "."], capture_output=True, text=True)

    #----------Check for staged changes----------
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:
        cprint("  💾 Ready to commit your changes.", Fore.CYAN)
        commit_msg = input("Enter a commit message [Default: Commit]: ").strip()
        if not commit_msg:
            commit_msg = "Commit"
        cprint(f"  💾 Creating commit: {commit_msg}", Fore.CYAN)
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        cprint("[OK] Changes committed successfully.", Fore.GREEN)
    else:
        cprint("[OK] No changes to commit. Working tree is clean.", Fore.GREEN)

    print()
    cprint("[OK] Git commit helper finished.", Fore.GREEN)
    input("Press Enter to return...")

if __name__ == "__main__":
    run_git_commit()
