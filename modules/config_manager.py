from pathlib import Path
import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """Centralized configuration management for ClibDT"""
    
    def __init__(self):
        # Use config folder in parent root
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
    
    def get_config_path(self, filename: str) -> Path:
        """Get full path for a config file"""
        return self.config_dir / filename
    
    def save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Save data to a JSON config file"""
        try:
            config_file = self.get_config_path(filename)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save config {filename}: {e}")
            return False
    
    def load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load data from a JSON config file"""
        try:
            config_file = self.get_config_path(filename)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load config {filename}: {e}")
            return None
    
    def save_text(self, filename: str, content: str) -> bool:
        """Save text content to a config file"""
        try:
            config_file = self.get_config_path(filename)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save config {filename}: {e}")
            return False
    
    def load_text(self, filename: str) -> Optional[str]:
        """Load text content from a config file"""
        try:
            config_file = self.get_config_path(filename)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load config {filename}: {e}")
            return None
    
    def file_exists(self, filename: str) -> bool:
        """Check if a config file exists"""
        return self.get_config_path(filename).exists()
    
    def delete_file(self, filename: str) -> bool:
        """Delete a config file"""
        try:
            config_file = self.get_config_path(filename)
            if config_file.exists():
                config_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete config {filename}: {e}")
            return False

# Global config manager instance
config_manager = ConfigManager() 