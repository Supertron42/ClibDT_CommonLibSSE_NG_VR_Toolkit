import os
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from modules.utilities.common import VERSION
from modules.config_utils import get_config_directory


class ExplorerPanel(QWidget):
    folder_opened = pyqtSignal(str)  # Signal when a folder is opened

    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = theme_manager
        self.current_theme = 'dark'

        # Connect to theme changes if theme manager is provided
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)

        # Main layout with proper spacing (AI Theme Instructions)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Explorer")
        title.setObjectName("main_title")
        title_row.addWidget(title)
        divider = QLabel()
        divider.setObjectName("title_divider")
        divider.setFixedHeight(2)
        divider.setMinimumWidth(120)
        title_row.addWidget(divider)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Description
        desc = QLabel("Browse and manage ClibDT folders and directories.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)

        # Folders list
        self.folders_list = QListWidget()
        self.folders_list.setObjectName("folders_list")
        self.folders_list.setMinimumHeight(300)
        self.folders_list.itemDoubleClicked.connect(self.open_folder)
        layout.addWidget(self.folders_list)



        # Add stretch to prevent content expansion
        layout.addStretch()

        self.setLayout(layout)

        # Load folders on initialization
        self.load_folders()

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

    def get_dev_root(self):
        """Get the development root directory"""
        dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
        if not dev_root:
            dev_root = r"C:\ClibDT"
        return Path(dev_root)

    def get_folder_info(self):
        """Get information about all ClibDT folders"""
        dev_root = self.get_dev_root()
        
        folders = [
            {
                'name': 'Development Root',
                'path': dev_root,
                'description': 'Main ClibDT development directory',
                'icon': '🏠'
            },
            {
                'name': 'Projects',
                'path': dev_root / "projects",
                'description': 'All your ClibDT projects',
                'icon': '📁'
            },
            {
                'name': 'Output',
                'path': dev_root / "output",
                'description': 'Compiled mods and build outputs',
                'icon': '📦'
            },
            {
                'name': 'Tools',
                'path': dev_root / "tools",
                'description': 'Development tools and utilities',
                'icon': '🔧'
            },
            {
                'name': 'Downloads',
                'path': dev_root / "downloads",
                'description': 'Downloaded files and archives',
                'icon': '⬇️'
            },
            {
                'name': 'Config',
                'path': get_config_directory(),
                'description': 'ClibDT configuration files',
                'icon': '⚙️'
            },
            {
                'name': 'Logs',
                'path': Path(__file__).parent.parent,
                'description': 'Application logs and temporary files',
                'icon': '📋'
            }
        ]
        
        return folders

    def load_folders(self):
        """Load and display all ClibDT folders"""
        self.folders_list.clear()
        folders = self.get_folder_info()
        
        for folder in folders:
            path = folder['path']
            exists = path.exists()
            
            # Create list item with icon and name
            item_text = f"{folder['icon']} {folder['name']}"
            item = QListWidgetItem(item_text)
            
            # Set tooltip with path and description
            tooltip = f"{folder['description']}\nPath: {path}"
            if not exists:
                tooltip += "\n⚠️ Directory does not exist"
            item.setToolTip(tooltip)
            
            # Store the path as item data
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            
            # Set item properties for styling
            if exists:
                item.setData(Qt.ItemDataRole.UserRole + 1, "exists")
            else:
                item.setData(Qt.ItemDataRole.UserRole + 1, "missing")
            
            self.folders_list.addItem(item)

    def open_folder(self, item):
        """Open the selected folder in Windows Explorer"""
        path_str = item.data(Qt.ItemDataRole.UserRole)
        path = Path(path_str)
        
        if path.exists():
            try:
                # Use Windows Explorer to open the folder
                if sys.platform.startswith("win"):
                    subprocess.run(["explorer", str(path)], check=True)
                    self.set_status(f"Opened: {path}")
                    self.folder_opened.emit(str(path))
                else:
                    # Fallback for other platforms
                    subprocess.run(["xdg-open", str(path)], check=True)
                    self.set_status(f"Opened: {path}")
            except subprocess.CalledProcessError as e:
                self.set_status(f"Error opening folder: {e}")
        else:
            self.set_status(f"Directory does not exist: {path}")



    def set_status(self, message):
        """Set status message"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

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
                'info_color': '#3498db',
                'menu_item_selected': '#0078d4',
                'scrollbar_bg': '#2d2d2d',
                'scrollbar_handle': '#404040',
                'scrollbar_handle_hover': '#505050'
            }

        # Apply comprehensive theme styling
        self.setStyleSheet(f"""
            /* Main panel styling */
            ExplorerPanel {{
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}

            /* Main title styling */
            ExplorerPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
                background: transparent !important;
            }}

            /* Divider lines */
            ExplorerPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}

            /* Section descriptions */
            ExplorerPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
                background: transparent !important;
            }}

            /* Folders list styling */
            ExplorerPanel QListWidget#folders_list {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                padding: 8px !important;
                font-size: 11px !important;
                selection-background-color: {theme['menu_item_selected']} !important;
                selection-color: {theme['text_light']} !important;
            }}

            ExplorerPanel QListWidget::item {{
                background-color: transparent !important;
                border: none !important;
                border-radius: 4px !important;
                padding: 8px 12px !important;
                margin: 2px 0px !important;
                font-weight: normal !important;
            }}

            ExplorerPanel QListWidget::item:hover {{
                background-color: {theme['bg_secondary']} !important;
            }}

            ExplorerPanel QListWidget::item:selected {{
                background-color: {theme['menu_item_selected']} !important;
                color: {theme['text_light']} !important;
                font-weight: bold !important;
            }}

            /* Scrollbar styling */
            ExplorerPanel QListWidget QScrollBar:vertical {{
                background-color: {theme['scrollbar_bg']} !important;
                width: 8px !important;
                border-radius: 4px !important;
            }}

            ExplorerPanel QListWidget QScrollBar::handle:vertical {{
                background-color: {theme['scrollbar_handle']} !important;
                border-radius: 4px !important;
                min-height: 20px !important;
            }}

            ExplorerPanel QListWidget QScrollBar::handle:vertical:hover {{
                background-color: {theme['scrollbar_handle_hover']} !important;
            }}

            ExplorerPanel QListWidget QScrollBar::add-line:vertical, 
            ExplorerPanel QListWidget QScrollBar::sub-line:vertical {{
                height: 0px !important;
            }}


        """) 