# modules/progress_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont
import time


class ProgressWidget(QWidget):
    """Reusable progress widget for long-running operations"""
    
    # Signals
    cancelled = pyqtSignal()
    completed = pyqtSignal()
    
    def __init__(self, parent=None, title="Operation in Progress", show_cancel=True):
        super().__init__(parent)
        self.title = title
        self.show_cancel = show_cancel
        self.is_cancelled = False
        self.operation_thread = None
        
        # Setup UI
        self.setup_ui()
        
        # Animation timer for indeterminate progress
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_dots = 0
        
    def setup_ui(self):
        """Setup the progress widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("progress_title")
        layout.addWidget(self.title_label)
        
        # Status message
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("progress_status")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setMaximumHeight(32)
        layout.addWidget(self.progress_bar)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Cancel button (shown during operation)
        if self.show_cancel:
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.setProperty("btnType", "danger")
            self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.cancel_btn.setFixedWidth(80)
            self.cancel_btn.setMinimumHeight(24)
            self.cancel_btn.setMaximumHeight(32)
            self.cancel_btn.clicked.connect(self.cancel_operation)
            button_layout.addWidget(self.cancel_btn)
        
        # OK button (shown after completion, initially hidden)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setProperty("btnType", "success")
        self.ok_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ok_btn.setFixedWidth(80)
        self.ok_btn.setMinimumHeight(24)
        self.ok_btn.setMaximumHeight(32)
        self.ok_btn.clicked.connect(self.dismiss_widget)
        self.ok_btn.setVisible(False)
        button_layout.addWidget(self.ok_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initially hidden
        self.setVisible(False)
    
    def start_operation(self, operation_func, *args, **kwargs):
        """Start a long-running operation with progress tracking"""
        try:
            self.is_cancelled = False
            self.setVisible(True)
            
            # Create operation thread
            self.operation_thread = OperationThread(operation_func, *args, **kwargs)
            self.operation_thread.progress_update.connect(self.update_progress)
            self.operation_thread.status_update.connect(self.update_status)
            self.operation_thread.operation_finished.connect(self.operation_finished)
            self.operation_thread.error_occurred.connect(self.operation_error)

            
            # Start the operation
            self.operation_thread.start()
            
            # Start animation for indeterminate progress
            self.start_animation()
        except Exception as e:
            # Log the error and show a user-friendly message
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[PROGRESS WIDGET START ERROR] {error_details}")
            self.update_status(f"Failed to start operation: {e}")
            self.progress_bar.setValue(0)
            
            # Show OK button and hide cancel button
            if hasattr(self, 'cancel_btn') and self.cancel_btn:
                self.cancel_btn.setVisible(False)
            if hasattr(self, 'ok_btn'):
                self.ok_btn.setVisible(True)
    
    def update_progress(self, value, maximum=100):
        """Update progress bar value"""
        if maximum > 0:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)
            self.progress_bar.setFormat(f"{value}/{maximum} ({value/maximum*100:.1f}%)")
        else:
            # Indeterminate progress
            self.progress_bar.setRange(0, 0)
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.setText(message)
    
    def start_animation(self):
        """Start animation for indeterminate progress"""
        self.animation_dots = 0
        self.animation_timer.start(500)  # Update every 500ms
    
    def update_animation(self):
        """Update animation dots for indeterminate progress"""
        self.animation_dots = (self.animation_dots + 1) % 4
        dots = "." * self.animation_dots
        current_text = self.status_label.text()
        # Remove any existing dots and add new ones
        base_text = current_text.rstrip(".")
        self.status_label.setText(f"{base_text}{dots}")
    
    def stop_animation(self):
        """Stop animation"""
        self.animation_timer.stop()
    
    def cancel_operation(self):
        """Cancel the current operation"""
        self.is_cancelled = True
        if self.operation_thread and self.operation_thread.isRunning():
            self.operation_thread.terminate()
            self.operation_thread.wait()
        
        self.update_status("Operation cancelled")
        self.stop_animation()
        self.cancelled.emit()
        
        # Show OK button and hide cancel button
        if hasattr(self, 'cancel_btn') and self.cancel_btn:
            self.cancel_btn.setVisible(False)
        if hasattr(self, 'ok_btn'):
            self.ok_btn.setVisible(True)
    
    def operation_finished(self, result):
        """Handle operation completion"""
        self.stop_animation()
        self.update_status("Operation completed successfully")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.completed.emit()
        
        # Show OK button and hide cancel button
        if hasattr(self, 'cancel_btn') and self.cancel_btn:
            self.cancel_btn.setVisible(False)
        if hasattr(self, 'ok_btn'):
            self.ok_btn.setVisible(True)
    
    def operation_error(self, error_message):
        """Handle operation error"""
        self.stop_animation()
        self.update_status(f"Error: {error_message}")
        self.progress_bar.setValue(0)
        
        # Log the error for debugging
        print(f"[PROGRESS WIDGET ERROR] {error_message}")
        
        # Show OK button and hide cancel button
        if hasattr(self, 'cancel_btn') and self.cancel_btn:
            self.cancel_btn.setVisible(False)
        if hasattr(self, 'ok_btn'):
            self.ok_btn.setVisible(True)
    
    def dismiss_widget(self):
        """Dismiss the widget when OK button is clicked"""
        self.hide()
        # Reset button states for next use
        if hasattr(self, 'cancel_btn') and self.cancel_btn:
            self.cancel_btn.setVisible(True)
        if hasattr(self, 'ok_btn'):
            self.ok_btn.setVisible(False)
    
    def set_theme_manager(self, theme_manager):
        """Set theme manager for styling"""
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    

    
    def apply_theme(self):
        """Apply current theme to the progress widget"""
        if hasattr(self, 'theme_manager') and self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            # Fallback theme
            theme = {
                'window_bg': '#1e1e1e',
                'bg_primary': '#2d2d2d',
                'text_primary': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'button_bg': '#0078d4',
                'button_hover': '#106ebe',
                'button_pressed': '#005a9e',
                'success_color': '#27ae60',
                'error_color': '#e74c3c',
                'warning_color': '#f39c12',
                'separator': '#404040'
            }
        
        self.setStyleSheet(f"""
            ProgressWidget {{
                background-color: {theme['bg_primary']};
                border: 1px solid {theme['separator']};
                border-radius: 6px;
                padding: 8px;
            }}
            
            ProgressWidget QLabel#progress_title {{
                color: {theme['text_primary']};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }}
            
            ProgressWidget QLabel#progress_status {{
                color: {theme['text_secondary']};
                font-size: 11px;
                background: transparent;
            }}
            
            ProgressWidget QProgressBar {{
                border: 2px solid {theme['separator']};
                border-radius: 4px;
                text-align: center;
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
                font-size: 11px;
                font-weight: bold;
            }}
            
            ProgressWidget QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['button_bg']}, stop:1 {theme['button_pressed']});
                border-radius: 2px;
            }}
            
            ProgressWidget QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['button_bg']}, stop:1 {theme['button_pressed']});
                color: #ffffff;
                border: 1px solid {theme['button_bg']};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            
            ProgressWidget QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['button_hover']}, stop:1 {theme['button_bg']});
                border: 1px solid {theme['button_hover']};
            }}
            
            ProgressWidget QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['button_pressed']}, stop:1 {theme['button_pressed']});
                border: 1px solid {theme['button_pressed']};
            }}
            
            ProgressWidget QPushButton[btnType="danger"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                border: 1px solid {theme['error_color']};
            }}
            
            ProgressWidget QPushButton[btnType="danger"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                border: 1px solid {theme['error_color']};
                opacity: 0.9;
            }}
            
            ProgressWidget QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']});
                border: 1px solid {theme['success_color']};
            }}
            
            ProgressWidget QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']});
                border: 1px solid {theme['success_color']};
                opacity: 0.9;
            }}
        """)


class OperationThread(QThread):
    """Thread for running long operations with progress updates"""
    
    # Signals
    progress_update = pyqtSignal(int, int)  # value, maximum
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    operation_finished = pyqtSignal(object)  # result
    
    def __init__(self, operation_func, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Run the operation function"""
        try:
            # Create thread-safe callback functions that emit signals
            def progress_callback(value, maximum=100):
                self.progress_update.emit(value, maximum)
            
            def status_callback(message):
                self.status_update.emit(str(message))
            
            # Call the operation function with progress callback
            result = self.operation_func(
                progress_callback=progress_callback,
                status_callback=status_callback,
                *self.args, **self.kwargs
            )
            
            # Emit finished signal with result
            self.operation_finished.emit(result)
            
        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[OPERATION THREAD ERROR] {error_details}")
            self.error_occurred.emit(str(e))


class ActivityIndicator(QWidget):
    """Simple activity indicator for operations without known progress"""
    
    def __init__(self, parent=None, message="Processing..."):
        super().__init__(parent)
        self.message = message
        self.setup_ui()
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_dots = 0
        
    def setup_ui(self):
        """Setup the activity indicator UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Activity message
        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("activity_message")
        layout.addWidget(self.message_label)
        
        # Spinner (animated dots)
        self.spinner_label = QLabel("...")
        self.spinner_label.setObjectName("activity_spinner")
        layout.addWidget(self.spinner_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initially hidden
        self.setVisible(False)
    
    def start(self):
        """Start the activity indicator"""
        self.setVisible(True)
        self.animation_dots = 0
        self.animation_timer.start(300)  # Update every 300ms
    
    def stop(self):
        """Stop the activity indicator"""
        self.animation_timer.stop()
        self.setVisible(False)
    
    def update_animation(self):
        """Update animation dots"""
        self.animation_dots = (self.animation_dots + 1) % 4
        dots = "." * self.animation_dots
        self.spinner_label.setText(dots)
    
    def set_message(self, message):
        """Update the activity message"""
        self.message = message
        self.message_label.setText(message)
    
    def apply_theme(self, theme):
        """Apply theme to the activity indicator"""
        self.setStyleSheet(f"""
            ActivityIndicator {{
                background-color: {theme['bg_primary']};
                border: 1px solid {theme['separator']};
                border-radius: 4px;
                padding: 4px;
            }}
            
            ActivityIndicator QLabel#activity_message {{
                color: {theme['text_secondary']};
                font-size: 11px;
                background: transparent;
            }}
            
            ActivityIndicator QLabel#activity_spinner {{
                color: {theme['button_bg']};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                min-width: 20px;
            }}
        """)


# Utility functions for common progress patterns
def create_download_progress(operation_name="Download"):
    """Create a progress function for download operations"""
    def download_progress(progress_callback, status_callback, url, dest_path, **kwargs):
        import requests
        from pathlib import Path
        
        try:
            status_callback(f"Starting {operation_name}...")
            progress_callback(0, 100)
            
            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get('Content-Length', 0))
            
            if total_size == 0:
                # Unknown size - use indeterminate progress
                progress_callback(0, 0)
                status_callback(f"{operation_name} in progress...")
                
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress_callback(0, 0)  # Keep indeterminate
            else:
                # Known size - use determinate progress
                downloaded = 0
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress, 100)
                            status_callback(f"{operation_name}... {progress}%")
            
            status_callback(f"{operation_name} completed")
            progress_callback(100, 100)
            return dest_path
            
        except Exception as e:
            status_callback(f"{operation_name} failed: {str(e)}")
            raise
    
    return download_progress


def create_install_progress(operation_name="Installation"):
    """Create a progress function for installation operations"""
    def install_progress(progress_callback, status_callback, installer_path, **kwargs):
        import subprocess
        import sys
        
        try:
            status_callback(f"Starting {operation_name}...")
            progress_callback(0, 100)
            
            # Launch installer
            status_callback(f"Launching installer...")
            progress_callback(10, 100)
            
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            process = subprocess.Popen([installer_path], creationflags=creationflags)
            
            # Simulate progress while installer runs
            progress = 10
            while process.poll() is None and progress < 90:
                time.sleep(1)
                progress += 5
                progress_callback(progress, 100)
                status_callback(f"{operation_name} in progress... {progress}%")
            
            # Wait for completion
            process.wait()
            
            if process.returncode == 0:
                status_callback(f"{operation_name} completed successfully")
                progress_callback(100, 100)
            else:
                status_callback(f"{operation_name} failed with code {process.returncode}")
                raise Exception(f"Installation failed with return code {process.returncode}")
            
        except Exception as e:
            status_callback(f"{operation_name} failed: {str(e)}")
            raise
    
    return install_progress


def create_build_progress(operation_name="Build"):
    """Create a progress function for build operations"""
    def build_progress(progress_callback, status_callback, build_command, **kwargs):
        import subprocess
        import sys
        
        try:
            status_callback(f"Starting {operation_name}...")
            progress_callback(0, 100)
            
            # Run build command
            status_callback(f"Running build command...")
            progress_callback(10, 100)
            
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            process = subprocess.Popen(
                build_command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creationflags
            )
            
            # Monitor output and update progress
            progress = 10
            for line in process.stdout:
                status_callback(line.strip())
                if progress < 90:
                    progress += 2
                    progress_callback(progress, 100)
            
            process.wait()
            
            if process.returncode == 0:
                status_callback(f"{operation_name} completed successfully")
                progress_callback(100, 100)
            else:
                status_callback(f"{operation_name} failed with code {process.returncode}")
                raise Exception(f"Build failed with return code {process.returncode}")
            
        except Exception as e:
            status_callback(f"{operation_name} failed: {str(e)}")
            raise
    
    return build_progress 