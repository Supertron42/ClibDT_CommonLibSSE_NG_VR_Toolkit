from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QGroupBox, QScrollArea, QSpinBox, QCheckBox, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont
import json
from pathlib import Path
from typing import Optional
from modules.utilities.common import VERSION, NEXUS_URL
from modules.config_utils import get_config_directory


class SettingsPanel(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = theme_manager
        self.current_theme = 'dark'

        # Main layout with proper spacing (AI Theme Instructions)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Main title with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Settings")
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
        desc = QLabel("Configure ClibDT appearance and theme.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)

        # Theme selection section
        theme_section = QWidget()
        theme_section.setObjectName("theme_section")
        theme_layout = QVBoxLayout(theme_section)
        theme_layout.setContentsMargins(0, 0, 0, 8)
        theme_layout.setSpacing(8)

        # Theme section title with divider
        theme_title_row = QHBoxLayout()
        theme_title_row.setSpacing(8)
        theme_title_row.setContentsMargins(0, 0, 0, 0)
        theme_title = QLabel("Appearance")
        theme_title.setObjectName("section_title")
        theme_title_row.addWidget(theme_title)
        theme_title_divider = QLabel()
        theme_title_divider.setObjectName("section_title_divider")
        theme_title_divider.setFixedHeight(1)
        theme_title_divider.setMinimumWidth(100)
        theme_title_row.addWidget(theme_title_divider)
        theme_title_row.addStretch()
        theme_layout.addLayout(theme_title_row)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_row.setContentsMargins(0, 0, 0, 0)
        theme_label = QLabel("Theme:")
        theme_label.setObjectName("setting_label")
        theme_label.setFixedWidth(80)
        theme_row.addWidget(theme_label)
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.setObjectName("theme_dropdown")
        self.theme_dropdown.addItem("Dark Theme", "dark")
        self.theme_dropdown.addItem("Light Theme", "light")
        self.theme_dropdown.currentTextChanged.connect(self.on_theme_changed)
        self.theme_dropdown.setMinimumHeight(24)
        self.theme_dropdown.setMaximumHeight(32)
        theme_row.addWidget(self.theme_dropdown)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)
        layout.addWidget(theme_section)

        # Version check section
        version_section = QWidget()
        version_section.setObjectName("version_section")
        version_layout = QVBoxLayout(version_section)
        version_layout.setContentsMargins(0, 0, 0, 8)
        version_layout.setSpacing(8)

        # Version check section title with divider
        version_title_row = QHBoxLayout()
        version_title_row.setSpacing(8)
        version_title_row.setContentsMargins(0, 0, 0, 0)
        version_title = QLabel("Updates")
        version_title.setObjectName("section_title")
        version_title_row.addWidget(version_title)
        version_title_divider = QLabel()
        version_title_divider.setObjectName("section_title_divider")
        version_title_divider.setFixedHeight(1)
        version_title_divider.setMinimumWidth(100)
        version_title_row.addWidget(version_title_divider)
        version_title_row.addStretch()
        version_layout.addLayout(version_title_row)

        version_row = QHBoxLayout()
        version_row.setSpacing(8)
        version_row.setContentsMargins(0, 0, 0, 0)
        self.version_check_cb = QCheckBox("Enable automatic version checking")
        self.version_check_cb.setObjectName("version_check_cb")
        self.version_check_cb.setMinimumHeight(24)
        self.version_check_cb.setMaximumHeight(32)
        self.version_check_cb.setChecked(True)  # Enable by default
        self.version_check_cb.stateChanged.connect(self.on_version_check_changed)
        version_row.addWidget(self.version_check_cb)
        version_row.addStretch()
        version_layout.addLayout(version_row)
        layout.addWidget(version_section)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setProperty("btnType", "success")
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.save_btn.setMinimumHeight(24)
        self.save_btn.setMaximumHeight(32)
        self.save_btn.clicked.connect(self.save_settings)
        btn_row.addWidget(self.save_btn)
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setProperty("btnType", "secondary")
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reset_btn.setMinimumHeight(24)
        self.reset_btn.setMaximumHeight(32)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        # About/version info at the bottom
        about_section = QWidget()
        about_section.setObjectName("about_section")
        about_layout = QVBoxLayout(about_section)
        about_layout.setContentsMargins(0, 12, 0, 0)
        about_layout.setSpacing(4)
        version_label = QLabel(f"ClibDT Version: {VERSION}")
        version_label.setObjectName("about_version")
        about_layout.addWidget(version_label)
        link_label = QLabel(f'<a href="{NEXUS_URL}">Project Home</a>')
        link_label.setObjectName("about_link")
        link_label.setOpenExternalLinks(True)
        about_layout.addWidget(link_label)
        layout.addWidget(about_section)

        layout.addStretch()
        self.setLayout(layout)

        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.load_settings()
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
    
    def load_settings(self):
        """Load settings from config file with proper theme integration"""
        try:
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_settings.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                    
                    # Load theme from main window's theme manager if available
                    try:
                        from ClibDT import MainWindow
                        main_window = self.window()
                        if isinstance(main_window, MainWindow) and hasattr(main_window, 'theme_manager'):
                            current_theme = main_window.theme_manager.current_theme
                            if current_theme == 'dark':
                                self.theme_dropdown.setCurrentText("Dark Theme")
                            else:
                                self.theme_dropdown.setCurrentText("Light Theme")
                        else:
                            # Fallback to config file
                            theme = settings.get('theme', 'dark')
                            if theme == 'dark':
                                self.theme_dropdown.setCurrentText("Dark Theme")
                            else:
                                self.theme_dropdown.setCurrentText("Light Theme")
                    except Exception:
                        # Fallback to config file
                        theme = settings.get('theme', 'dark')
                        if theme == 'dark':
                            self.theme_dropdown.setCurrentText("Dark Theme")
                        else:
                            self.theme_dropdown.setCurrentText("Light Theme")
                    
                    # Load version check setting
                    version_check_enabled = settings.get('version_check_enabled', True)
                    self.version_check_cb.setChecked(version_check_enabled)
                    
        except Exception as e:
            self.set_status(f"[WARN] Could not load settings: {e}")
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_settings.json"
            
            settings = {
                'theme': 'dark' if 'Dark' in self.theme_dropdown.currentText() else 'light',
                'version_check_enabled': self.version_check_cb.isChecked()
            }
            
            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.set_status("[OK] Settings saved successfully")
            
        except Exception as e:
            self.set_status(f"[ERROR] Could not save settings: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.theme_dropdown.setCurrentText("Dark Theme")
        self.version_check_cb.setChecked(True)
        
        self.set_status("[OK] Settings reset to defaults")
    
    def on_theme_changed(self, text):
        """Handle theme dropdown selection change with integrated theme management"""
        # Determine theme from dropdown text
        if "Dark" in text:
            theme = 'dark'
        elif "Light" in text:
            theme = 'light'
        else:
            theme = 'dark'
        
        # Update current theme
        if theme != self.current_theme:
            self.current_theme = theme
            self.save_settings()
        
        # Emit theme change signal
        self.theme_changed.emit(theme)
        
        # Update main window theme through proper channels
        try:
            from ClibDT import MainWindow
            main_window = self.window()
            if isinstance(main_window, MainWindow) and hasattr(main_window, 'theme_manager'):
                # Update the main window's theme manager
                main_window.theme_manager.set_theme(theme)
        except Exception:
            # Silently handle any errors to prevent crashes
            pass
    
    def on_typography_changed(self):
        """Handle typography size changes"""
        # Auto-save typography changes
        self.save_settings()
        
        # Update main window typography through proper channels
        try:
            from ClibDT import MainWindow
            main_window = self.window()
            if isinstance(main_window, MainWindow) and hasattr(main_window, 'theme_manager'):
                # Typography changes are handled locally in settings panel
                # No need to forward to theme manager since it doesn't support typography
                pass
        except Exception:
            # Silently handle any errors to prevent crashes
            pass
    
    def on_verbose_changed(self):
        """Handle verbose output setting changes"""
        self.save_settings()
    
    def on_color_changed(self):
        """Handle color output setting changes"""
        self.save_settings()
    
    def on_version_check_changed(self):
        """Handle version check setting changes"""
        self.save_settings()
    
    def set_status(self, message):
        """Set status message"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def get_typography_sizes(self):
        """Get current typography sizes for use by other modules"""
        return {
            'header_size': 14,  # Default value
            'text_size': 11     # Default value
        }
    
    def get_terminal_settings(self):
        """Get current terminal output settings for use by other modules"""
        return {
            'verbose_output': False,  # Default value
            'color_output': True      # Default value
        }
    
    def get_version_check_enabled(self):
        """Get current version check setting for use by other modules"""
        return self.version_check_cb.isChecked()
    
    # Theme management methods
    def get_theme(self, theme_name=None):
        """Get theme colors by name - simplified for current implementation"""
        theme_name = theme_name or self.current_theme
        # Return a basic theme structure for compatibility
        return {
            'window_bg': '#1e1e1e' if theme_name == 'dark' else '#ffffff',
            'bg_primary': '#2d2d2d' if theme_name == 'dark' else '#f5f5f5',
            'bg_secondary': '#252525' if theme_name == 'dark' else '#e0e0e0',
            'text_primary': '#e0e0e0' if theme_name == 'dark' else '#000000',
            'text_secondary': '#b0b0b0' if theme_name == 'dark' else '#666666',
            'text_light': '#ffffff' if theme_name == 'dark' else '#000000',
            'button_bg': '#0078d4',
            'button_hover': '#106ebe',
            'button_pressed': '#005a9e',
            'input_bg': '#2d2d2d' if theme_name == 'dark' else '#ffffff',
            'input_border': '#404040' if theme_name == 'dark' else '#cccccc',
            'input_focus': '#0078d4',
            'separator': '#404040' if theme_name == 'dark' else '#cccccc',
            'success_color': '#27ae60',
            'error_color': '#e74c3c',
            'warning_color': '#f39c12',
            'info_color': '#3498db',
            'menu_item_selected': '#0078d4',
            'scrollbar_bg': '#2d2d2d' if theme_name == 'dark' else '#f0f0f0',
            'scrollbar_handle': '#404040' if theme_name == 'dark' else '#c0c0c0',
            'scrollbar_handle_hover': '#505050' if theme_name == 'dark' else '#a0a0a0',
            'terminal_bg': '#1e1e1e' if theme_name == 'dark' else '#ffffff',
            'terminal_text': '#e0e0e0' if theme_name == 'dark' else '#000000'
        }
    
    def set_theme(self, theme_name):
        """Set the current theme and emit signal"""
        if theme_name in ['dark', 'light']:
            if theme_name != self.current_theme:
                self.current_theme = theme_name
                self.save_settings()
            # Always emit signal to ensure UI updates
            self.theme_changed.emit(theme_name)
            return True
        return False
    
    def get_available_themes(self):
        """Get list of available theme names and display names"""
        return [('dark', 'Dark Theme'), ('light', 'Light Theme')]
    
    def get_current_theme_name(self):
        """Get the display name of the current theme"""
        return 'Dark Theme' if self.current_theme == 'dark' else 'Light Theme'
    
    def apply_theme_to_widget(self, widget, theme_name=None):
        """Apply theme colors to a widget with comprehensive styling"""
        theme = self.get_theme(theme_name)
        
        # Apply comprehensive theme to widget
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background-color: transparent;
                color: {theme['text_primary']};
            }}
            
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['text_light']};
                border: 1px solid {theme['button_bg']};
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {theme['button_hover']};
                border-color: {theme['button_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {theme['button_pressed']};
                border-color: {theme['button_pressed']};
            }}
            
            QLineEdit {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
            }}
            
            QLineEdit:focus {{
                border-color: {theme['input_focus']};
            }}
            
            QComboBox {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
            }}
            
            QComboBox:focus {{
                border-color: {theme['input_focus']};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                selection-background-color: {theme['menu_item_selected']};
            }}
            
            QCheckBox {{
                color: {theme['text_primary']};
            }}
            
            QCheckBox::indicator {{
                border: 2px solid {theme['input_border']};
                background-color: {theme['input_bg']};
                border-radius: 3px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']};
                border-color: {theme['button_bg']};
            }}
            
            QSpinBox {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 5px;
            }}
            
            QSpinBox:focus {{
                border-color: {theme['input_focus']};
            }}
            
            QProgressBar {{
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                text-align: center;
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
            }}
            
            QProgressBar::chunk {{
                background-color: {theme['button_bg']};
                border-radius: 2px;
            }}
            
            QGroupBox {{
                font-weight: bold;
                color: {theme['text_primary']};
                border: 2px solid {theme['separator']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: {theme['bg_primary']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {theme['text_primary']};
            }}
            
            QScrollBar:vertical {{
                background-color: {theme['scrollbar_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['scrollbar_handle_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def get_button_style(self, button_type='primary', theme_name=None):
        """Get styled button CSS for different button types"""
        theme = self.get_theme(theme_name)
        
        base_style = f"""
            QPushButton {{
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                min-height: 16px;
                margin: 2px 4px;
            }}
            QPushButton:disabled {{
                background-color: {theme['text_secondary']};
                color: {theme['text_secondary']};
            }}
        """
        
        if button_type == 'primary':
            return base_style + f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['button_bg']}, stop:1 {theme['button_pressed']});
                    color: {theme['text_light']};
                    border: 1px solid {theme['button_bg']};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['button_hover']}, stop:1 {theme['button_bg']});
                    border: 1px solid {theme['button_hover']};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['button_pressed']}, stop:1 {theme['button_pressed']});
                    border: 1px solid {theme['button_pressed']};
                }}
            """
        elif button_type == 'success':
            return base_style + f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['success_color']}, stop:1 {theme['success_color']});
                    color: {theme['text_light']};
                    border: 1px solid {theme['success_color']};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['success_color']}, stop:1 {theme['success_color']});
                    border: 1px solid {theme['success_color']};
                    opacity: 0.9;
                }}
            """
        elif button_type == 'warning':
            return base_style + f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['warning_color']}, stop:1 {theme['warning_color']});
                    color: {theme['text_light']};
                    border: 1px solid {theme['warning_color']};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['warning_color']}, stop:1 {theme['warning_color']});
                    border: 1px solid {theme['warning_color']};
                    opacity: 0.9;
                }}
            """
        elif button_type == 'danger':
            return base_style + f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                    color: {theme['text_light']};
                    border: 1px solid {theme['error_color']};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                    border: 1px solid {theme['error_color']};
                    opacity: 0.9;
                }}
            """
        else:
            return base_style + f"""
                QPushButton {{
                    background-color: {theme['bg_secondary']};
                    color: {theme['text_primary']};
                    border: 1px solid {theme['input_border']};
                }}
                QPushButton:hover {{
                    background-color: {theme['input_border']};
                    border-color: {theme['text_primary']};
                }}
            """
    
    def get_input_style(self, input_type='text', theme_name=None):
        """Get styled input CSS for different input types"""
        theme = self.get_theme(theme_name)
        
        base_style = f"""
            background-color: {theme['input_bg']};
            color: {theme['text_primary']};
            border: 2px solid {theme['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: bold;
        """
        
        focus_style = f"""
            border-color: {theme['input_focus']};
            background-color: {theme['input_bg']};
        """
        
        hover_style = f"""
            border-color: {theme['button_hover']};
            background-color: {theme['bg_secondary']};
        """
        
        if input_type == 'comboBox':
            return f"""
                QComboBox {{
                    {base_style}
                    min-width: 180px;
                }}
                QComboBox:hover {{
                    {hover_style}
                }}
                QComboBox:focus {{
                    {focus_style}
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 24px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 6px solid {theme['text_primary']};
                    margin-right: 6px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {theme['input_bg']};
                    color: {theme['text_primary']};
                    border: 2px solid {theme['input_border']};
                    border-radius: 6px;
                    selection-background-color: {theme['menu_item_selected']};
                    selection-color: {theme['text_light']};
                    padding: 4px;
                }}
            """
        elif input_type == 'spinBox':
            return f"""
                QSpinBox {{
                    {base_style}
                    min-width: 100px;
                }}
                QSpinBox:hover {{
                    {hover_style}
                }}
                QSpinBox:focus {{
                    {focus_style}
                }}
            """
        else:  # text input
            return f"""
                QLineEdit {{
                    {base_style}
                }}
                QLineEdit:hover {{
                    {hover_style}
                }}
                QLineEdit:focus {{
                    {focus_style}
                }}
            """

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
        
        # Apply theme following AI Theme Instructions pattern
        self.setStyleSheet(f"""
            /* Base styling */
            SettingsPanel {{
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            /* Main title styling */
            SettingsPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
            }}
            
            /* Main title divider */
            SettingsPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Section description */
            SettingsPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            /* Section titles */
            SettingsPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            /* Section title dividers */
            SettingsPanel QLabel#section_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Setting labels */
            SettingsPanel QLabel#setting_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
            }}
            
            /* ComboBox styling */
            SettingsPanel QComboBox {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                min-height: 24px !important;
                max-height: 32px !important;
            }}
            
            SettingsPanel QComboBox:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            SettingsPanel QComboBox:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            SettingsPanel QComboBox::drop-down {{
                border: none !important;
                width: 24px !important;
            }}
            
            SettingsPanel QComboBox::down-arrow {{
                image: none !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid {theme['text_primary']} !important;
                margin-right: 6px !important;
            }}
            
            SettingsPanel QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                selection-background-color: {theme['button_bg']} !important;
                selection-color: {theme['text_light']} !important;
                padding: 4px !important;
            }}
            
            /* CheckBox styling */
            SettingsPanel QCheckBox {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                spacing: 8px !important;
                padding: 2px 0px !important;
                min-height: 24px !important;
                max-height: 32px !important;
            }}
            
            SettingsPanel QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                border: 2px solid {theme['input_border']} !important;
                background-color: {theme['input_bg']} !important;
                border-radius: 3px !important;
            }}
            
            SettingsPanel QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']} !important;
                border-color: {theme['button_bg']} !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
            }}
            
            SettingsPanel QCheckBox:hover::indicator:unchecked {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            /* Button styling */
            SettingsPanel QPushButton {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 24px !important;
                max-height: 32px !important;
                margin: 2px 4px !important;
            }}
            
            SettingsPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success buttons */
            SettingsPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            SettingsPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            SettingsPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Secondary buttons */
            SettingsPanel QPushButton[btnType="secondary"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268) !important;
                color: {theme['text_light']} !important;
                border: 1px solid #5a6268 !important;
                padding: 6px 12px !important;
            }}
            
            SettingsPanel QPushButton[btnType="secondary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:0.5 #95a5a6, stop:1 #7f8c8d) !important;
                border: 2px solid #d5dbdb !important;
                color: #ffffff !important;
            }}
            
            SettingsPanel QPushButton[btnType="secondary"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #495057) !important;
                border: 1px solid #495057 !important;
            }}
            
            /* About section styling */
            SettingsPanel QLabel#about_version {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
            }}
            
            SettingsPanel QLabel#about_link {{
                color: {theme['info_color']} !important;
                font-size: 10px !important;
            }}
            
            SettingsPanel QLabel#about_link:hover {{
                color: {theme['button_hover']} !important;
            }}
        """) 