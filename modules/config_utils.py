import os
import shutil
from pathlib import Path


def get_config_directory():
    """Get the config directory path, creating it if needed and migrating existing configs"""
    # Get dev root from environment variable
    dev_root = os.environ.get('XSE_CLIBDT_DEVROOT')
    
    if dev_root:
        # Use dev root for config directory
        config_dir = Path(dev_root) / "config"
    else:
        # Fallback to parent directory if dev root not set
        config_dir = Path(__file__).parent.parent / "config"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Check if we need to migrate from old location
    old_config_dir = Path(__file__).parent.parent / "config"
    if old_config_dir.exists() and old_config_dir != config_dir:
        # Migrate existing config files
        migrate_config_files(old_config_dir, config_dir)
    
    return config_dir


def migrate_config_files(old_dir, new_dir):
    """Migrate config files from old directory to new directory"""
    try:
        config_files = [
            "clibdt_settings.json",
            "clibdt_update_prefs.json", 
            "clibdt_refresh_prefs.json",
            "clibdt_tool_paths_config.json",
            "clibdt_launcher_config.json",
            "clibdt_detach_prefs.json",
            "clibdt_build_config.json",
            "clibdt_backup_config.json"
        ]
        
        for config_file in config_files:
            old_file = old_dir / config_file
            new_file = new_dir / config_file
            
            if old_file.exists() and not new_file.exists():
                # Move the file to new location
                shutil.move(str(old_file), str(new_file))
                print(f"[INFO] Migrated config file: {config_file}")
        
        # Try to remove old config directory if it's empty
        try:
            if old_dir.exists() and not any(old_dir.iterdir()):
                old_dir.rmdir()
                print(f"[INFO] Removed empty old config directory: {old_dir}")
        except Exception:
            pass
            
    except Exception as e:
        print(f"[WARN] Could not migrate config files: {e}") 