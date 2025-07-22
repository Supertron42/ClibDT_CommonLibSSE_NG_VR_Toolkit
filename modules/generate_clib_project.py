import os
import json
from pathlib import Path
from datetime import datetime
from modules.utilities.common import VERSION

def generate_clib_project_json(output_path, project_name, version, author, description):
    """
    Generate a clib_project.json file at output_path using the provided metadata.
    This file is used by ClibDT to identify valid projects.
    """
    project_data = {
        "project_name": project_name,
        "version": version,
        "author": author,
        "description": description,
        "created_date": datetime.now().isoformat(),
        "clibdt_version": VERSION,
        "project_type": "commonlibsse-ng",
        "build_system": "xmake",
        "xmake_version": "3.0.1"
    }
    
    output_path = Path(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)
    
    return project_data

def is_valid_clib_project(project_path):
    """
    Check if a directory contains a valid ClibDT project by looking for clib_project.json
    """
    project_path = Path(project_path)
    clib_project_file = project_path / "clib_project.json"
    
    if not clib_project_file.exists():
        return False
    
    try:
        with open(clib_project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation - check for required fields
        required_fields = ["project_name", "version", "project_type"]
        return all(field in data for field in required_fields)
    except (json.JSONDecodeError, IOError):
        return False

def get_project_info(project_path):
    """
    Get project information from clib_project.json
    """
    project_path = Path(project_path)
    clib_project_file = project_path / "clib_project.json"
    
    if not clib_project_file.exists():
        return None
    
    try:
        with open(clib_project_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

if __name__ == "__main__":
    print("=== clib_project.json Generator ===")
    project_name = input("Project name: ").strip() or "MyProject"
    version = input("Version [1.0.0]: ").strip() or "1.0.0"
    author = input("Author [Unknown]: ").strip() or "Unknown"
    description = input("Description [No description provided.]: ").strip() or "No description provided."
    output_path = input("Output path [clib_project.json]: ").strip() or "clib_project.json"
    
    project_data = generate_clib_project_json(output_path, project_name, version, author, description)
    print(f"[OK] clib_project.json generated at {output_path}")
    print(f"Project data: {json.dumps(project_data, indent=2)}") 