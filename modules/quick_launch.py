from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QMenu, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from functools import partial
import json
import subprocess
import os
import sys
from pathlib import Path


class QuickLaunchManager:
    """Manages quick launch functionality for ClibDT with pinned tool icons"""
    
    def __init__(self, main_window, status_callback=None):
        self.main_window = main_window
        self.status_callback = status_callback
        self.quick_launch_items = []
        # Use config folder in parent root
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
        self.config_file = config_dir / "clibdt_launcher_config.json"
        self.quick_launch_bar = None
        self.tool_buttons = {}
        
    def create_quick_launch_bar(self):
        """Create and configure the quick launch toolbar at the top"""
        from PyQt6.QtWidgets import QGridLayout
        self.quick_launch_bar = QWidget()
        self.quick_launch_bar.setObjectName("quick_launch_bar")
        self.quick_launch_bar.setFixedHeight(40)

        grid = QGridLayout()
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(6)

        # Tool buttons layout (left)
        tool_layout = QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(6)
        self.tool_layout = tool_layout
        tool_container = QWidget()
        tool_container.setLayout(tool_layout)
        grid.addWidget(tool_container, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # No editor button here anymore

        # Set column stretch for layout
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 100)
        grid.setColumnStretch(2, 0)

        self.quick_launch_bar.setLayout(grid)
        self.load_pinned_tools()
        self.apply_quick_launch_theme()
        return self.quick_launch_bar

    def load_pinned_tools(self):
        """Load and display pinned tools as buttons"""
        if not self.quick_launch_bar or not hasattr(self, 'tool_layout'):
            return
        tool_layout = self.tool_layout
        # Clear existing buttons
        while tool_layout.count():
            item = tool_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self.tool_buttons.clear()
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    pinned_items = data.get('pinned_items', [])
                    # Create buttons for each pinned item
                    for item in pinned_items:
                        button = self.create_tool_button(item['path'])
                        if button:
                            tool_layout.addWidget(button)
                            self.tool_buttons[item['path']] = button
        except Exception as e:
            self.set_status(f"[WARN] Could not load quick launch items: {e}")
    
    def create_tool_button(self, file_path):
        """Create a simple tool button with filename and color"""
        try:
            path_obj = Path(file_path)
            file_name = path_obj.stem  # Name without extension
            button = QPushButton(file_name)
            button.setToolTip(f"{file_name}\n{file_path}")
            button.setFixedSize(120, 32)
            color = self.get_button_color(len(self.tool_buttons))
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            # Simple click: just run the file standalone
            import subprocess
            button.clicked.connect(lambda: subprocess.Popen([file_path]))
            # Context menu remains unchanged
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, fp=file_path: self.show_tool_button_context_menu(fp, pos)
            )
            return button
        except Exception:
            button = QPushButton("Tool")
            button.setFixedSize(120, 32)
            button.setToolTip(str(Path(file_path).name))
            import subprocess
            button.clicked.connect(lambda: subprocess.Popen([file_path]))
            return button
    
    def get_button_color(self, index):
        """Get a different color for each button"""
        colors = [
            '#0078d4',  # Blue
            '#107c10',  # Green
            '#d83b01',  # Orange
            '#5c2d91',  # Purple
            '#e81123',  # Red
            '#00b294',  # Teal
            '#ff8c00',  # Dark Orange
            '#68217a',  # Dark Purple
            '#0078d4',  # Blue (repeats)
            '#107c10',  # Green (repeats)
        ]
        return colors[index % len(colors)]
    
    def lighten_color(self, color):
        """Lighten a hex color for hover effect"""
        try:
            # Simple lightening - add 20% white
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            r = min(255, r + 51)  # Add 20% (51/255)
            g = min(255, g + 51)
            b = min(255, b + 51)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color
    
    def darken_color(self, color):
        """Darken a hex color for pressed effect"""
        try:
            # Simple darkening - reduce by 20%
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            r = max(0, r - 51)  # Reduce by 20% (51/255)
            g = max(0, g - 51)
            b = max(0, b - 51)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color
    
    def show_tool_button_context_menu(self, file_path, position):
        """Show context menu for tool button"""
        menu = QMenu(self.main_window)
        file_name = Path(file_path).name
        
        # Launch action
        launch_action = menu.addAction(f"Launch {file_name}")
        if launch_action:
            launch_action.triggered.connect(partial(self.launch_quick_launch_item, file_path))
        
        menu.addSeparator()
        
        # Remove action
        remove_action = menu.addAction(f"Remove from Quick Launch")
        if remove_action:
            remove_action.triggered.connect(partial(self.remove_quick_launch_item, file_path))
        
        # Show menu
        if menu.actions():
            button = self.tool_buttons.get(file_path)
            if button:
                menu.exec(button.mapToGlobal(position))

    def browse_quick_launch_file(self):
        """Browse for a file to add to quick launch"""
        dlg = QFileDialog(self.main_window)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("All Files (*.*)")
        if dlg.exec():
            file_path = dlg.selectedFiles()[0]
            self.add_quick_launch_item(file_path)

    def add_quick_launch_item(self, file_path):
        """Add a file to the quick launch"""
        path = Path(file_path)
        name = path.name
        
        try:
            # Load existing config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'pinned_items': []}
            
            # Check if already exists
            pinned_items = data.get('pinned_items', [])
            for item in pinned_items:
                if item['path'] == str(path):
                    self.set_status(f"[INFO] {name} is already in quick launch")
                    return
            
            # Add to pinned items
            pinned_items.append({
                'name': name,
                'path': str(path)
            })
            data['pinned_items'] = pinned_items
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update toolbar
            self.load_pinned_tools()
            
            self.set_status(f"[OK] Added {name} to quick launch")
            
        except Exception as e:
            self.set_status(f"[ERROR] Failed to add quick launch item: {e}")

    def remove_quick_launch_item(self, file_path):
        """Remove a quick launch item from toolbar"""
        try:
            # Remove from config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                pinned_items = data.get('pinned_items', [])
                pinned_items = [item for item in pinned_items if item['path'] != file_path]
                data['pinned_items'] = pinned_items
                
                with open(self.config_file, 'w') as f:
                    json.dump(data, f, indent=2)
            
            # Update toolbar
            self.load_pinned_tools()
            
            self.set_status(f"[OK] Removed from quick launch")
        except Exception as e:
            self.set_status(f"[ERROR] Failed to remove quick launch item: {e}")

    def pin_quick_launch_item_to_top(self, file_path):
        """Move a quick launch item to the top in toolbar"""
        try:
            # Update config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                pinned_items = data.get('pinned_items', [])
                # Find and move item to top
                for i, pinned_item in enumerate(pinned_items):
                    if pinned_item['path'] == file_path:
                        pinned_items.insert(0, pinned_items.pop(i))
                        break
                
                data['pinned_items'] = pinned_items
                
                with open(self.config_file, 'w') as f:
                    json.dump(data, f, indent=2)
            
            # Update toolbar
            self.load_pinned_tools()
            
            self.set_status(f"[OK] Pinned to top")
        except Exception as e:
            self.set_status(f"[ERROR] Failed to pin quick launch item: {e}")

    def launch_quick_launch_item(self, file_path):
        """Launch a quick launch item"""
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
                os.startfile(str(path))
                self.set_status(f"[OK] Opened with default app: {path.name}")
                
        except Exception as e:
            self.set_status(f"[ERROR] Failed to launch {file_path}: {e}")

    def get_editor_path(self):
        # Try config first
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('preferred_code_editor', "")
        except Exception:
            pass
        # Fallback to env var
        return os.environ.get("XSE_CODE_EDITOR_PATH", "")

    def save_editor_path(self, path):
        try:
            data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            data['preferred_code_editor'] = path
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.set_status(f"[ERROR] Could not save code editor path: {e}")

    def set_status(self, message):
        """Set status message"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def apply_quick_launch_theme(self):
        """Apply minimal theme styling to quick launch bar"""
        if not self.quick_launch_bar:
            return
            
        # Apply minimal styling to avoid conflicts
        self.quick_launch_bar.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """) 