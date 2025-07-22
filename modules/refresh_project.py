import os
import shutil
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

#----------import----------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.utilities.logger import cprint
from modules.git_stage_and_commit import run_git_commit
from modules.xmake_gen import generate_xmake_lua

from modules.utilities.common import VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QGroupBox, QTextEdit, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

init(autoreset=True)

def create_clibdt_config(project_path: Path):
    """Create a clibdt_project.json file for a project to mark it as a valid ClibDT project"""
    config_file = project_path / "clibdt_project.json"
    
    if config_file.exists():
        cprint(f"[INFO] clibdt_project.json already exists in {project_path.name}", Fore.LIGHTBLACK_EX)
        return True
    
    try:
        # Create basic config structure
        config = {
            "project_name": project_path.name,
            "version": "1.0.0",
            "author": "ClibDT Refresh Tool",
            "description": "Project refreshed by ClibDT",
            "created_date": datetime.now().isoformat(),
            "clibdt_version": "4.0.1",
            "project_type": "commonlibsse-ng",
            "build_system": "xmake",
            "xmake_version": "3.0.1",
            "dependencies": {
                "clibutil": "latest",
                "xbyak": "latest"
            }
        }
        
        # Write config file
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        cprint(f"[OK] Created clibdt_project.json for {project_path.name}", Fore.GREEN)
        return True
        
    except Exception as e:
        cprint(f"[ERROR] Failed to create clibdt_project.json for {project_path.name}: {e}", Fore.RED)
        return False

def is_valid_clib_project(project_path):
    """Check if a project is a valid ClibDT project (has clibdt_project.json or xmake.lua)"""
    # First check for clibdt_project.json (new standard)
    if (project_path / "clibdt_project.json").exists():
        return True
    
    # Fallback to xmake.lua (legacy)
    if (project_path / "xmake.lua").exists():
        return True
    
    return False

def delete_folder(folder: Path):
    def onerror(func, path, exc_info):
        import stat
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            cprint(f"[ERROR] Could not delete {path}: {e}", Fore.RED)

    if folder.exists() and folder.is_dir():
        try:
            shutil.rmtree(folder, onerror=onerror)
            cprint(f"[OK] {folder.name}/ deleted.", Fore.GREEN)
        except Exception as e:
            cprint(f"[ERROR] Failed to delete {folder.name}/: {e}", Fore.RED)
    else:
        cprint(f"[INFO] {folder.name}/ not found. Skipping.", Fore.LIGHTBLACK_EX)


def install_clibutil():
    cprint("--- Installing ClibUtil ---", Fore.CYAN)
    temp = Path("_clibutil_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    
    try:
        # Add timeout to git clone
        result = subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/powerof3/ClibUtil.git", str(temp)],
            timeout=60,  # 60 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to clone ClibUtil: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git clone timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to clone ClibUtil: {e}", Fore.RED)
        return False
    
    clib_dest = Path("ClibUtil")
    clib_dest.mkdir(parents=True, exist_ok=True)
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    
    try:
        result = subprocess.run(
            f"xcopy /E /I /Y \"{temp}\\include\\ClibUtil\" \"{clib_dest}\"",
            shell=True,
            creationflags=creationflags,
            timeout=30,  # 30 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to copy ClibUtil: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Copy operation timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to copy ClibUtil: {e}", Fore.RED)
        return False
    
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] ClibUtil installed.", Fore.GREEN)
    return True


def install_xbyak():
    cprint("--- Installing xbyak ---", Fore.CYAN)
    temp = Path("_xbyak_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    
    try:
        # Add timeout to git clone
        result = subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/herumi/xbyak.git", str(temp)],
            timeout=60,  # 60 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to clone xbyak: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git clone timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to clone xbyak: {e}", Fore.RED)
        return False
    
    xbyak_dest = Path("xbyak")
    if xbyak_dest.exists():
        shutil.rmtree(xbyak_dest)
    
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    
    try:
        result = subprocess.run(
            f"xcopy /E /I /Y \"{temp}\\xbyak\" \"{xbyak_dest}\"",
            shell=True,
            creationflags=creationflags,
            timeout=30,  # 30 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to copy xbyak: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Copy operation timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to copy xbyak: {e}", Fore.RED)
        return False
    
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] xbyak installed.", Fore.GREEN)
    return True


def install_clibutil_direct():
    """Install ClibUtil directly without temporary folders using git sparse checkout"""
    cprint("--- Installing ClibUtil ---", Fore.CYAN)
    
    clib_dest = Path("ClibUtil")
    if clib_dest.exists():
        shutil.rmtree(clib_dest, ignore_errors=True)
    
    clib_dest.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize git repository in destination
        subprocess.run(["git", "init"], cwd=clib_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Add remote
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/powerof3/ClibUtil.git"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Enable sparse checkout
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Configure sparse checkout to only get the include/ClibUtil folder
        sparse_checkout_file = clib_dest / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sparse_checkout_file, 'w') as f:
            f.write("include/ClibUtil/\n")
        
        # Fetch and checkout
        subprocess.run(["git", "fetch", "--depth=1", "origin"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True, timeout=60)
        subprocess.run(["git", "checkout", "FETCH_HEAD"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Move files from include/ClibUtil to root of ClibUtil directory
        include_clibutil = clib_dest / "include" / "ClibUtil"
        if include_clibutil.exists():
            # Move all files from include/ClibUtil to the root of clib_dest
            for item in include_clibutil.iterdir():
                if item.is_file():
                    shutil.move(str(item), str(clib_dest / item.name))
                elif item.is_dir():
                    shutil.move(str(item), str(clib_dest / item.name))
            
            # Remove the include directory structure
            shutil.rmtree(clib_dest / "include", ignore_errors=True)
        
        # Remove git repository
        shutil.rmtree(clib_dest / ".git", ignore_errors=True)
        
        cprint("[OK] ClibUtil installed.", Fore.GREEN)
        return True
        
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git operation timed out", Fore.RED)
        if clib_dest.exists():
            shutil.rmtree(clib_dest, ignore_errors=True)
        return False
    except subprocess.CalledProcessError as e:
        cprint(f"[ERROR] Failed to install ClibUtil: {e.stderr}", Fore.RED)
        if clib_dest.exists():
            shutil.rmtree(clib_dest, ignore_errors=True)
        return False
    except Exception as e:
        cprint(f"[WARN] Sparse checkout failed, trying fallback method: {e}", Fore.YELLOW)
        # Fallback: use the old method with temporary folder
        return install_clibutil_fallback()


def install_xbyak_direct():
    """Install xbyak directly without temporary folders using git sparse checkout"""
    cprint("--- Installing xbyak ---", Fore.CYAN)
    
    xbyak_dest = Path("xbyak")
    if xbyak_dest.exists():
        shutil.rmtree(xbyak_dest, ignore_errors=True)
    
    xbyak_dest.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize git repository in destination
        subprocess.run(["git", "init"], cwd=xbyak_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Add remote
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/herumi/xbyak.git"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Enable sparse checkout
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Configure sparse checkout to only get the xbyak folder
        sparse_checkout_file = xbyak_dest / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sparse_checkout_file, 'w') as f:
            f.write("xbyak/\n")
        
        # Fetch and checkout
        subprocess.run(["git", "fetch", "--depth=1", "origin"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True, timeout=60)
        subprocess.run(["git", "checkout", "FETCH_HEAD"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True, timeout=30)
        
        # Move files from xbyak subdirectory to root of xbyak directory
        xbyak_subdir = xbyak_dest / "xbyak"
        if xbyak_subdir.exists():
            # Move all files from xbyak subdirectory to the root of xbyak_dest
            for item in xbyak_subdir.iterdir():
                if item.is_file():
                    shutil.move(str(item), str(xbyak_dest / item.name))
                elif item.is_dir():
                    shutil.move(str(item), str(xbyak_dest / item.name))
            
            # Remove the xbyak subdirectory
            shutil.rmtree(xbyak_subdir, ignore_errors=True)
        
        # Remove git repository
        shutil.rmtree(xbyak_dest / ".git", ignore_errors=True)
        
        cprint("[OK] xbyak installed.", Fore.GREEN)
        return True
        
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git operation timed out", Fore.RED)
        if xbyak_dest.exists():
            shutil.rmtree(xbyak_dest, ignore_errors=True)
        return False
    except subprocess.CalledProcessError as e:
        cprint(f"[ERROR] Failed to install xbyak: {e.stderr}", Fore.RED)
        if xbyak_dest.exists():
            shutil.rmtree(xbyak_dest, ignore_errors=True)
        return False
    except Exception as e:
        cprint(f"[WARN] Sparse checkout failed, trying fallback method: {e}", Fore.YELLOW)
        # Fallback: use the old method with temporary folder
        return install_xbyak_fallback()


def install_clibutil_fallback():
    """Fallback method using temporary folder (old approach)"""
    cprint("[INFO] Using fallback method for ClibUtil...", Fore.YELLOW)
    temp = Path("_clibutil_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    
    try:
        # Add timeout to git clone
        result = subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/powerof3/ClibUtil.git", str(temp)],
            timeout=60,  # 60 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to clone ClibUtil: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git clone timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to clone ClibUtil: {e}", Fore.RED)
        return False
    
    clib_dest = Path("ClibUtil")
    clib_dest.mkdir(parents=True, exist_ok=True)
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    
    try:
        result = subprocess.run(
            f"xcopy /E /I /Y \"{temp}\\include\\ClibUtil\" \"{clib_dest}\"",
            shell=True,
            creationflags=creationflags,
            timeout=30,  # 30 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to copy ClibUtil: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Copy operation timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to copy ClibUtil: {e}", Fore.RED)
        return False
    
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] ClibUtil installed (fallback).", Fore.GREEN)
    return True


def install_xbyak_fallback():
    """Fallback method using temporary folder (old approach)"""
    cprint("[INFO] Using fallback method for xbyak...", Fore.YELLOW)
    temp = Path("_xbyak_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    
    try:
        # Add timeout to git clone
        result = subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/herumi/xbyak.git", str(temp)],
            timeout=60,  # 60 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to clone xbyak: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Git clone timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to clone xbyak: {e}", Fore.RED)
        return False
    
    xbyak_dest = Path("xbyak")
    if xbyak_dest.exists():
        shutil.rmtree(xbyak_dest)
    
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    
    try:
        result = subprocess.run(
            f"xcopy /E /I /Y \"{temp}\\xbyak\" \"{xbyak_dest}\"",
            shell=True,
            creationflags=creationflags,
            timeout=30,  # 30 second timeout
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            cprint(f"[ERROR] Failed to copy xbyak: {result.stderr}", Fore.RED)
            return False
    except subprocess.TimeoutExpired:
        cprint("[ERROR] Copy operation timed out", Fore.RED)
        return False
    except Exception as e:
        cprint(f"[ERROR] Failed to copy xbyak: {e}", Fore.RED)
        return False
    
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] xbyak installed (fallback).", Fore.GREEN)
    return True


def run_refresh(project_path: Path):
    try:
        os.chdir(project_path)
        cprint(f"[OK] Working on project: {project_path}", Fore.GREEN)

        #----------CREATE CLIBDT CONFIG IF NEEDED----------
        # Always create clibdt_project.json for better project detection
        if not (project_path / "clibdt_project.json").exists():
            cprint("--- Creating ClibDT Configuration ---", Fore.CYAN)
            if create_clibdt_config(project_path):
                cprint(f"[OK] {project_path.name} is now a valid ClibDT project", Fore.GREEN)
            else:
                cprint(f"[WARN] Could not create config for {project_path.name}, continuing anyway", Fore.YELLOW)
        else:
            cprint(f"[INFO] clibdt_project.json already exists in {project_path.name}", Fore.LIGHTBLACK_EX)

        #----------CLEAN----------
        delete_folder(project_path / "build")
        delete_folder(project_path / ".xmake")

        #----------INSTALL DEPS----------
        clibutil_success = install_clibutil_direct()
        xbyak_success = install_xbyak_direct()
        
        if not clibutil_success or not xbyak_success:
            cprint("[WARN] Some dependencies failed to install, but continuing...", Fore.YELLOW)

        #----------GIT STAGE/COMMIT----------
        try:
            run_git_commit_nonblocking()
        except Exception as e:
            cprint(f"[WARN] Git operations failed: {e}", Fore.YELLOW)

        #----------REGENERATE xmake.lua----------
        cprint("--- Regenerating xmake.lua ---", Fore.CYAN)
        name = project_path.name
        version = "1.0.0"
        author = "Unknown"
        desc = "No description provided."
        try:
            generate_xmake_lua(project_path, name, version, author, desc)
            cprint(f"[OK] xmake.lua regenerated at {project_path / 'xmake.lua'}", Fore.GREEN)
        except Exception as e:
            cprint(f"[ERROR] Failed to regenerate xmake.lua: {e}", Fore.RED)

        cprint("[OK] Project refresh completed successfully!", Fore.GREEN)
        
    except Exception as e:
        cprint(f"[ERROR] Project refresh failed: {e}", Fore.RED)
        raise

#----------main----------
def main():
    """CLI entry point for backward compatibility"""
    projects_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not projects_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT environment variable not set.", Fore.RED)
        return
    
    projects_path = Path(projects_root) / "projects"
    if not projects_path.exists():
        cprint(f"[ERROR] Projects directory not found: {projects_path}", Fore.RED)
        return
    
    # Get ALL projects in the projects folder (not just valid ones)
    all_projects = [d for d in projects_path.iterdir() if d.is_dir()]
    
    if not all_projects:
        cprint("[ERROR] No projects found in projects directory.", Fore.RED)
        return
    
    print("\n=========================================")
    print("    Refresh Project Dependencies")
    print("=========================================")
    for i, p in enumerate(all_projects, 1):
        status_icon = "✅" if is_valid_clib_project(p) else "🆕"
        print(f"{i}. {status_icon} {p.name}")
    print("M. Return to main menu\n")
    
    choice = input("Select a project to refresh: ").strip()
    if choice.lower() == "m":
        return
    
    try:
        project_idx = int(choice) - 1
        if 0 <= project_idx < len(all_projects):
            project_path = all_projects[project_idx]
            run_refresh(project_path)
        else:
            cprint("[ERROR] Invalid project selection.", Fore.RED)
    except ValueError:
        cprint("[ERROR] Invalid input. Please enter a number.", Fore.RED)
    
    input("Press Enter to return...")

if __name__ == "__main__":
    main()

class RefreshThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, project_path, status_callback=None):
        super().__init__()
        self.project_path = Path(project_path)
        self.status_callback = status_callback
    
    def run(self):
        try:
            def status(msg):
                self.progress_signal.emit(msg)
                if self.status_callback:
                    self.status_callback(msg)
            
            # Validate project path
            if not self.project_path.exists():
                self.finished_signal.emit(False, f"Project path does not exist: {self.project_path}")
                return
            
            # Change to project directory
            try:
                os.chdir(self.project_path)
                status(f"[INFO] Refreshing project in {self.project_path}")
            except Exception as e:
                self.finished_signal.emit(False, f"Failed to change to project directory: {e}")
                return
            
            # Run the refresh operation directly without stdout capture
            # This avoids the blocking input() issue
            try:
                # Create ClibDT config if needed
                # Always create clibdt_project.json for better project detection
                if not (self.project_path / "clibdt_project.json").exists():
                    status("--- Creating ClibDT Configuration ---")
                    if create_clibdt_config(self.project_path):
                        status(f"[OK] {self.project_path.name} is now a valid ClibDT project")
                    else:
                        status(f"[WARN] Could not create config for {self.project_path.name}, continuing anyway")
                else:
                    status(f"[INFO] clibdt_project.json already exists in {self.project_path.name}")
                
                # Clean build folders
                status("--- Cleaning Build Folders ---")
                delete_folder(self.project_path / "build")
                delete_folder(self.project_path / ".xmake")
                
                # Install dependencies
                status("--- Installing Dependencies ---")
                clibutil_success = install_clibutil_direct()
                xbyak_success = install_xbyak_direct()
                
                if not clibutil_success or not xbyak_success:
                    status("[WARN] Some dependencies failed to install, but continuing...")
                
                # Git operations
                try:
                    status("--- Git Operations ---")
                    run_git_commit_nonblocking()
                except Exception as e:
                    status(f"[WARN] Git operations failed: {e}")
                
                # Regenerate xmake.lua
                status("--- Regenerating xmake.lua ---")
                name = self.project_path.name
                version = "1.0.0"
                author = "Unknown"
                desc = "No description provided."
                
                try:
                    generate_xmake_lua(self.project_path, name, version, author, desc)
                    status(f"[OK] xmake.lua regenerated at {self.project_path / 'xmake.lua'}")
                except Exception as e:
                    status(f"[ERROR] Failed to regenerate xmake.lua: {e}")
                
                status("[OK] Project refresh completed successfully!")
                self.finished_signal.emit(True, "Project refreshed successfully!")
                
            except Exception as e:
                status(f"[ERROR] Refresh operation failed: {e}")
                self.finished_signal.emit(False, f"Refresh failed: {e}")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Thread error: {e}")

class RefreshProjectPanel(QWidget):
    def __init__(self, parent=None, status_callback=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = None
        self.selected_project_path = None
        self._projects_loaded = False
        # Load user preferences
        self.load_preferences()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Title row with divider
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Refresh Project")
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
        desc = QLabel("Refresh project dependencies, update config, and regenerate xmake.lua.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)

        # Section: Project Selection
        project_section = QWidget()
        project_section.setObjectName("project_section")
        project_layout = QVBoxLayout(project_section)
        project_layout.setContentsMargins(0, 0, 0, 8)
        project_layout.setSpacing(8)

        project_row = QHBoxLayout()
        project_row.setSpacing(8)
        project_row.setContentsMargins(0, 0, 0, 0)



        self.project_combo = QComboBox()
        self.project_combo.setEditable(False)
        self.project_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.project_combo.setObjectName("project_combo")
        self.project_combo.setToolTip("Select the project to refresh")
        self.project_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setMinimumHeight(24)
        self.project_combo.setMaximumHeight(32)
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        project_row.addWidget(self.project_combo)
        project_layout.addLayout(project_row)
        layout.addWidget(project_section)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)

        self.refresh_btn = QPushButton("Refresh Project")
        self.refresh_btn.setProperty("btnType", "success")
        self.refresh_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.refresh_btn.setMinimumHeight(24)
        self.refresh_btn.setMaximumHeight(32)
        # self.refresh_btn.clicked.connect(self.on_refresh)  # Implement as needed
        btn_row.addWidget(self.refresh_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("btnType", "uninstall")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setMinimumHeight(24)
        self.stop_btn.setMaximumHeight(32)
        self.stop_btn.setEnabled(False)
        # self.stop_btn.clicked.connect(self.on_stop)  # Implement as needed
        btn_row.addWidget(self.stop_btn)

        layout.addLayout(btn_row)
        layout.addStretch()
        self.setLayout(layout)
        self.apply_theme()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            main_window = self.window()
            theme_manager = getattr(main_window, 'theme_manager', None)
            if theme_manager:
                self.set_theme_manager(theme_manager)
        except Exception:
            pass
        self.apply_theme()
        if not self._projects_loaded:
            self.load_projects()
            self._projects_loaded = True

    def load_projects(self):
        try:
            from modules.refresh_project import is_valid_clib_project
        except ImportError:
            def is_valid_clib_project(project_path):
                return (project_path / "xmake.lua").exists()

        dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
        self.project_combo.clear()
        if not dev_root:
            self.project_combo.addItem("No dev root found")
            return

        projects_path = Path(dev_root) / "projects"
        if not projects_path.exists():
            self.project_combo.addItem("No projects folder found")
            return

        projects = []
        for item in projects_path.iterdir():
            if item.is_dir() and is_valid_clib_project(item):
                projects.append(item.name)

        if not projects:
            self.project_combo.addItem("No valid ClibDT projects found")
            return

        projects.sort()
        self.project_combo.addItems(projects)
        
        # Select last used project if available
        if hasattr(self, 'last_project') and self.last_project in projects:
            self.project_combo.setCurrentText(self.last_project)
        elif projects:
            self.project_combo.setCurrentText(projects[0])

    def on_project_changed(self, project_name):
        if project_name and not project_name.startswith("No ") and not project_name.startswith("Error"):
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if dev_root:
                self.selected_project_path = Path(dev_root) / "projects" / project_name
                self.last_project = project_name
                self.save_preferences()
        else:
            self.selected_project_path = None

    def load_preferences(self):
        """Load user preferences from a simple config file"""
        self.last_project = None
        
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_refresh_prefs.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    prefs = json.load(f)
                    self.last_project = prefs.get('last_project', None)
        except Exception:
            # If loading fails, use defaults
            pass

    def save_preferences(self):
        """Save user preferences to a simple config file"""
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_file = config_dir / "clibdt_refresh_prefs.json"
            config_data = {
                'last_project': self.last_project,
                'clibdt_version': VERSION
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            # If saving fails, just continue
            pass

    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def apply_theme(self):
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            theme = {
                'window_bg': '#1e1e1e',
                'text_primary': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'separator': '#404040',
                'success_color': '#27ae60',
                'error_color': '#e74c3c',
                'warning_color': '#f39c12',
                'info_color': '#3498db',
                'button_bg': '#0078d4',
                'button_hover': '#106ebe',
                'button_pressed': '#005a9e',
                'input_bg': '#2d2d2d',
                'input_border': '#404040',
                'input_focus': '#0078d4',
                'text_light': '#ffffff',
            }
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['window_bg']};
                color: {theme['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel#main_title {{
                font-size: 18px;
                font-weight: bold;
                color: {theme['text_primary']};
                margin-bottom: 4px;
                padding: 6px 0px;
            }}
            QLabel#title_divider {{
                background-color: {theme['separator']};
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            QLabel#section_desc {{
                color: {theme['text_secondary']};
                font-size: 10px;
                margin-bottom: 6px;
            }}
            QLabel#status_label {{
                color: {theme['info_color']};
                font-size: 11px;
                margin-bottom: 6px;
            }}
            QComboBox, QComboBox:hover, QComboBox:focus {{
                background-color: {theme['input_bg']};
                color: {theme['text_primary']};
                border: 2px solid {theme['input_border']};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
                margin: 0px;
                font-weight: normal;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {theme['button_hover']};
                background-color: {theme['input_bg']};
            }}
            QComboBox:focus {{
                border-color: {theme['input_focus']};
                background-color: {theme['input_bg']};
            }}
            QPushButton, QPushButton:hover, QPushButton:pressed, QPushButton:disabled {{
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
                margin: 2px 4px;
            }}
            QPushButton:disabled {{
                background-color: {theme['text_secondary']};
                color: {theme['text_secondary']};
                opacity: 0.6;
            }}
            QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']});
                color: {theme['text_light']};
                border: 1px solid {theme['success_color']};
                padding: 6px 12px;
            }}
            QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71);
                border: 2px solid #a9dfbf;
                color: #ffffff;
                padding: 7px 13px;
            }}
            QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                border: 2px solid #1e8449;
                color: #ffffff;
                padding: 8px 14px;
            }}
            QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                color: {theme['text_light']};
                border: 1px solid {theme['error_color']};
                padding: 6px 12px;
            }}
            QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b);
                border: 2px solid #f1948a;
                color: #ffffff;
            }}
            QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']});
                border: 1px solid {theme['error_color']};
                opacity: 0.8;
            }}
        """)

def run_git_commit_nonblocking():
    """Non-blocking version of git commit for use in threads"""
    try:
        # Check if we're in a git repository
        result = subprocess.run(["git", "status"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            cprint("  🔧 Initializing Git repository...", Fore.CYAN)
            subprocess.run(["git", "init"], capture_output=True, text=True, timeout=10)

        # Stage all changes
        cprint("  📝 Staging files...", Fore.CYAN)
        subprocess.run(["git", "add", "."], capture_output=True, text=True, timeout=30)

        # Check for staged changes
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True, timeout=10)
        if result.returncode != 0:
            # There are changes to commit - use default message
            commit_msg = "Auto-commit from ClibDT refresh"
            cprint(f"  💾 Creating commit: {commit_msg}", Fore.CYAN)
            result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                cprint("[OK] Changes committed successfully.", Fore.GREEN)
            else:
                cprint(f"[WARN] Commit failed: {result.stderr}", Fore.YELLOW)
        else:
            cprint("[OK] No changes to commit. Working tree is clean.", Fore.GREEN)
            
    except subprocess.TimeoutExpired:
        cprint("[WARN] Git operation timed out", Fore.YELLOW)
    except Exception as e:
        cprint(f"[WARN] Git operation failed: {e}", Fore.YELLOW)
