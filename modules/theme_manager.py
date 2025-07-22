from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal
import json
from pathlib import Path
from modules.config_utils import get_config_directory


class ThemeManager(QObject):
    """Manages themes for ClibDT application with beautiful integration"""
    
    theme_changed = pyqtSignal(str)  # Signal emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'
        self.themes = {
            'dark': {
                'name': 'Dark Theme',
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
                'menu_item_selected': '#0078d4',
                'separator': '#404040',
                'menu_bg': '#2d2d2d',
                'menu_item': '#e0e0e0',
                'menu_item_hover': '#404040',
                'menu_item_selected_active': '#106ebe',
                'scrollbar_bg': '#404040',
                'scrollbar_handle': '#606060',
                'scrollbar_handle_hover': '#808080',
                'terminal_bg': '#0d1117',
                'terminal_text': '#ffffff',
                'success_color': '#27ae60',
                'warning_color': '#f39c12',
                'error_color': '#e74c3c',
                'info_color': '#3498db'
            },
            'light': {
                'name': 'Light Theme',
                'window_bg': '#f8f9fa',
                'bg_primary': '#ffffff',
                'bg_secondary': '#e9ecef',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'text_light': '#ffffff',
                'button_bg': '#007bff',
                'button_hover': '#0056b3',
                'button_pressed': '#004085',
                'input_bg': '#ffffff',
                'input_border': '#ced4da',
                'input_focus': '#007bff',
                'menu_item_selected': '#007bff',
                'separator': '#dee2e6',
                'menu_bg': '#ffffff',
                'menu_item': '#495057',
                'menu_item_hover': '#e9ecef',
                'menu_item_selected_active': '#0056b3',
                'scrollbar_bg': '#e9ecef',
                'scrollbar_handle': '#adb5bd',
                'scrollbar_handle_hover': '#6c757d',
                'terminal_bg': '#ffffff',
                'terminal_text': '#212529',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8'
            }
        }
        
        # Load saved theme preference
        self.load_theme_preference()
    
    def get_theme(self, theme_name=None):
        """Get theme colors by name"""
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, self.themes['dark'])
    
    def set_theme(self, theme_name):
        """Set the current theme and emit signal"""
        if theme_name in self.themes:
            if theme_name != self.current_theme:
                self.current_theme = theme_name
                self.save_theme_preference()
            # Always emit signal to ensure UI updates
            self.theme_changed.emit(theme_name)
            return True
        return False
    
    def get_available_themes(self):
        """Get list of available theme names and display names"""
        return [(name, theme['name']) for name, theme in self.themes.items()]
    
    def get_current_theme_name(self):
        """Get the display name of the current theme"""
        return self.themes[self.current_theme]['name']
    
    def load_theme_preference(self):
        """Load theme preference from config file"""
        try:
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_settings.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                    theme = settings.get('theme', 'dark')
                    if theme in self.themes:
                        self.current_theme = theme
        except Exception:
            # Use default theme if loading fails
            self.current_theme = 'dark'
    
    def save_theme_preference(self):
        """Save theme preference to config file"""
        try:
            # Use config directory from dev root or fallback
            config_dir = get_config_directory()
            config_file = config_dir / "clibdt_settings.json"
            settings = {}
            
            # Load existing settings if file exists
            if config_file.exists():
                with open(config_file, 'r') as f:
                    settings = json.load(f)
            
            # Update theme setting
            settings['theme'] = self.current_theme
            
            # Save back to file
            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception:
            # Silently fail if saving fails
            pass
    
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
            
            /* Progress widget styling */
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

    def get_env_vars_style(self, theme_name=None):
        """Get styled CSS for EnvVarsPanel following AI Theme Instructions"""
        theme = self.get_theme(theme_name)
        
        return f"""
            /* EnvVarsPanel - Compact styling following AI Theme Instructions */
            EnvVarsPanel,
            EnvVarsPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            EnvVarsPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Main title - largest and most prominent */
            EnvVarsPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
                background: transparent !important;
            }}
            
            /* Section titles - medium size */
            EnvVarsPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            /* Section descriptions */
            EnvVarsPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            /* Divider lines */
            EnvVarsPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            EnvVarsPanel QLabel#section_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Variable labels */
            EnvVarsPanel QLabel#var_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                background: transparent !important;
                min-width: 100px !important;
            }}
            
            /* Status label */
            EnvVarsPanel QLabel#status_label {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                font-weight: normal !important;
                background: transparent !important;
                font-style: italic !important;
            }}
            
            /* Input field styling - compact sizing */
            EnvVarsPanel QLineEdit,
            EnvVarsPanel QLineEdit:hover,
            EnvVarsPanel QLineEdit:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 200px !important;
                min-height: 24px !important;
                max-height: 32px !important;
            }}
            
            EnvVarsPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            EnvVarsPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* Button styling - unified gradient system with compact sizing */
            EnvVarsPanel QPushButton,
            EnvVarsPanel QPushButton:hover,
            EnvVarsPanel QPushButton:pressed,
            EnvVarsPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            EnvVarsPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons */
            EnvVarsPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Uninstall/Danger buttons */
            EnvVarsPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
            
            /* Secondary utility buttons */
            EnvVarsPanel QPushButton[btnType="secondary"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268) !important;
                color: {theme['text_light']} !important;
                border: 1px solid #5a6268 !important;
                padding: 6px 12px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="secondary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:0.5 #95a5a6, stop:1 #7f8c8d) !important;
                border: 2px solid #d5dbdb !important;
                color: #ffffff !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="secondary"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #495057) !important;
                border: 1px solid #495057 !important;
            }}
            
            /* Folder/Info buttons */
            EnvVarsPanel QPushButton[btnType="folder"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['info_color']}, stop:1 {theme['info_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['info_color']} !important;
                padding: 6px 8px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="folder"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #85c1e9, stop:0.5 #5dade2, stop:1 #3498db) !important;
                border: 2px solid #a9cce3 !important;
                color: #ffffff !important;
                padding: 7px 9px !important;
            }}
            
            EnvVarsPanel QPushButton[btnType="folder"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c) !important;
                border: 2px solid #1b4f72 !important;
                color: #ffffff !important;
                padding: 8px 10px !important;
            }}
            
            /* Layout spacing following AI Theme Instructions */
            EnvVarsPanel QHBoxLayout {{
                spacing: 6px !important;  /* Compact spacing */
                margin: 0px !important;
                padding: 0px !important;
            }}
        """

    def get_create_project_style(self, theme_name=None):
        """Get styled CSS for CreateProjectPanel following AI Theme Instructions"""
        theme = self.get_theme(theme_name)
        
        return f"""
            /* CreateProjectPanel - Ultra-compact styling with proper hierarchy */
            CreateProjectPanel,
            CreateProjectPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            CreateProjectPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Main title - largest and most prominent */
            CreateProjectPanel QLabel#main_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                padding: 6px 0px !important;
                background: transparent !important;
            }}
            
            /* Divider line for main title */
            CreateProjectPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Section description */
            CreateProjectPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
                background: transparent !important;
            }}
            
            /* Input field labels */
            CreateProjectPanel QLabel#name_label,
            CreateProjectPanel QLabel#version_label,
            CreateProjectPanel QLabel#author_label,
            CreateProjectPanel QLabel#desc_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                background: transparent !important;
                min-width: 120px !important;
            }}
            
            /* Input field styling - responsive resizing */
            CreateProjectPanel QLineEdit,
            CreateProjectPanel QLineEdit:hover,
            CreateProjectPanel QLineEdit:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 200px !important;
                height: 32px !important;
            }}
            
            CreateProjectPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            CreateProjectPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* Progress Bar styling */
            CreateProjectPanel QProgressBar {{
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                text-align: center !important;
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            CreateProjectPanel QProgressBar::chunk {{
                background-color: {theme['button_bg']} !important;
                border-radius: 2px !important;
            }}
            
            /* Dynamic Status Message styling */
            CreateProjectPanel QWidget#status_container {{
                background-color: {theme['bg_secondary']} !important;
                border: 1px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                padding: 8px 12px !important;
                margin: 4px 0px !important;
            }}
            
            CreateProjectPanel QLabel#spinner_label {{
                color: {theme['info_color']} !important;
                font-size: 14px !important;
                font-weight: bold !important;
                background: transparent !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            CreateProjectPanel QLabel#status_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                background: transparent !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Button styling - unified gradient system with responsive sizing */
            CreateProjectPanel QPushButton,
            CreateProjectPanel QPushButton:hover,
            CreateProjectPanel QPushButton:pressed,
            CreateProjectPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            CreateProjectPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons */
            CreateProjectPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            CreateProjectPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            CreateProjectPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Uninstall/Danger buttons */
            CreateProjectPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            CreateProjectPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            CreateProjectPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
        """

    def get_install_tools_style(self, theme_name=None):
        """Get styled CSS for InstallToolsPanel with comprehensive theming"""
        theme = self.get_theme(theme_name)
        
        return f"""
            /* InstallToolsPanel - Ultra-compact styling with proper hierarchy */
            InstallToolsPanel,
            InstallToolsPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            InstallToolsPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Header elements - ONLY these are bold */
            InstallToolsPanel QLabel#install_tools_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                background: transparent !important;
                padding: 6px 0px !important;
            }}
            
            InstallToolsPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            InstallToolsPanel QLabel#install_tools_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 11px !important;
                margin-bottom: 8px !important;
                font-weight: normal !important;
            }}
            

            
            InstallToolsPanel QLabel#custom_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['info_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            InstallToolsPanel QLabel#custom_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            InstallToolsPanel QLabel#custom_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            
            InstallToolsPanel QLabel#url_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                min-width: 80px !important;
            }}
            
            InstallToolsPanel QLabel#path_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                min-width: 100px !important;
                max-width: 100px !important;
                width: 100px !important;
            }}
            
            InstallToolsPanel QLabel#local_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['success_color']} !important;
                margin-bottom: 4px !important;
                padding: 4px 0px !important;
            }}
            
            InstallToolsPanel QLabel#local_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            InstallToolsPanel QLabel#local_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
            }}
            

            

            
            InstallToolsPanel QLabel#section_divider {{
                background-color: {theme['separator']} !important;
                height: 2px !important;
                margin: 8px 0px !important;
            }}
            
            /* Status orbs styling */
            InstallToolsPanel QLabel[toolOrb="true"] {{
                font-size: 10px !important;
                min-width: 10px !important;
                max-width: 10px !important;
                border-radius: 5px !important;
                background-color: transparent !important;
            }}
            
            /* Input field styling - responsive resizing */
            InstallToolsPanel QLineEdit,
            InstallToolsPanel QLineEdit:hover,
            InstallToolsPanel QLineEdit:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 200px !important;
                height: 32px !important;
            }}
            
            InstallToolsPanel QLineEdit#url_input {{
                min-width: 300px !important;
            }}
            
            InstallToolsPanel QLineEdit#path_input {{
                min-width: 200px !important;
            }}
            
            InstallToolsPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            InstallToolsPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* Button styling - unified gradient system with responsive sizing */
            InstallToolsPanel QPushButton,
            InstallToolsPanel QPushButton:hover,
            InstallToolsPanel QPushButton:pressed,
            InstallToolsPanel QPushButton:disabled {{
                border: 1px solid transparent !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            InstallToolsPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="install"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="install"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #58d68d, stop:0.5 #2ecc71, stop:1 #27ae60) !important;
                border: 2px solid #82e0aa !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 9px 17px !important;
                margin: 1px 3px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="install"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                border-radius: 6px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 10px 18px !important;
                margin: 0px 2px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 9px 17px !important;
                margin: 1px 3px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="secondary"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268) !important;
                color: {theme['text_light']} !important;
                border: 1px solid #5a6268 !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="secondary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:0.5 #95a5a6, stop:1 #7f8c8d) !important;
                border: 2px solid #d5dbdb !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 9px 17px !important;
                margin: 1px 3px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="secondary"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #495057) !important;
                border: 1px solid #495057 !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="folder"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['info_color']}, stop:1 {theme['info_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['info_color']} !important;
                padding: 6px 8px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="folder"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #85c1e9, stop:0.5 #5dade2, stop:1 #3498db) !important;
                border: 2px solid #a9cce3 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 7px 9px !important;
                margin: 1px 3px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="folder"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c) !important;
                border: 2px solid #1b4f72 !important;
                border-radius: 6px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 8px 10px !important;
                margin: 0px 2px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 7px 13px !important;
                margin: 1px 3px !important;
            }}
            
            InstallToolsPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                border-radius: 6px !important;
                color: #ffffff !important;
                font-weight: bold !important;
                padding: 8px 14px !important;
                margin: 0px 2px !important;
            }}
            
            /* Ensure buttons don't overlap and have proper spacing */
            InstallToolsPanel QHBoxLayout {{
                spacing: 8px !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            /* Ensure input field expands properly */
            InstallToolsPanel QLineEdit#path_input {{
                min-width: 200px !important;
            }}
            
            /* Status orb styling */
            InstallToolsPanel QLabel[toolOrb="true"] {{
                font-size: 10px !important;
                min-width: 10px !important;
                max-width: 10px !important;
                border-radius: 5px !important;
                background-color: transparent !important;
            }}
        """ 