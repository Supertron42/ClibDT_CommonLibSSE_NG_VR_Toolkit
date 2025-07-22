import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# -------------------- GUI Panel --------------------
from modules.utilities.common import VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QProgressBar, QMessageBox, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from modules.progress_widget import ProgressWidget

init(autoreset=True)

# Global status callback for GUI output
_gui_status_callback = None

def set_gui_status_callback(callback):
    global _gui_status_callback
    _gui_status_callback = callback

def cprint(msg, color=Fore.RESET):
    colored_msg = color + msg + Style.RESET_ALL
    if _gui_status_callback:
        # Send to GUI terminal
        _gui_status_callback(colored_msg)
    else:
        # Fall back to console output
        print(colored_msg)



def prompt_input(msg, default=None):
    val = input(f"{msg} ").strip()
    if val.lower() == "m":
        return None
    return val or default

def get_env_or_prompt(env_key, prompt_msg, default=None):
    injected = os.getenv(env_key)
    if injected:
        cprint(f"[INFO] Using {env_key} from environment: {injected}", Fore.YELLOW)
        return injected
    return prompt_input(prompt_msg, default)

def find_git():
    """Find Git installation in various locations"""
    import shutil
    
    # Check if git is in PATH
    git_path = shutil.which("git")
    if git_path:
        cprint(f"[DEBUG] Found git in PATH: {git_path}", Fore.LIGHTBLACK_EX)
        return git_path
    
    # Check environment variable
    git_env_path = os.getenv("XSE_GIT_ROOT")
    if git_env_path:
        git_exe = Path(git_env_path) / "bin" / "git.exe"
        if git_exe.exists():
            cprint(f"[DEBUG] Found git in XSE_GIT_ROOT: {git_exe}", Fore.LIGHTBLACK_EX)
            return str(git_exe)
    
    # Check dev root tools directory
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        # Check both lowercase and uppercase variants
        git_paths = [
            Path(dev_root) / "tools" / "Git" / "bin" / "git.exe",
            Path(dev_root) / "tools" / "git" / "bin" / "git.exe",
            Path(dev_root) / "tools" / "PortableGit" / "bin" / "git.exe"
        ]
        
        for git_path in git_paths:
            if git_path.exists():
                cprint(f"[DEBUG] Found git in devroot: {git_path}", Fore.LIGHTBLACK_EX)
                return str(git_path)
    
    # Check common installation paths
    common_paths = [
        Path("C:/Program Files/Git/bin/git.exe"),
        Path("C:/Program Files (x86)/Git/bin/git.exe"),
        Path(os.getenv("LocalAppData", "")) / "Programs" / "Git" / "bin" / "git.exe"
    ]
    
    for git_path in common_paths:
        if git_path.exists():
            cprint(f"[DEBUG] Found git in common path: {git_path}", Fore.LIGHTBLACK_EX)
            return str(git_path)
    
    cprint("[DEBUG] Git not found in any location", Fore.LIGHTBLACK_EX)
    return None

def find_github_desktop():
    """Find GitHub Desktop installation in default or tools location"""
    #----------Check environment variable first----------
    gh_env_path = os.getenv("XSE_GITHUB_DESKTOP_PATH")
    if gh_env_path and Path(gh_env_path).exists():
        return gh_env_path
    
    #----------Check default installation path----------
    default_path = Path(os.getenv("LocalAppData", "")) / "GitHubDesktop" / "GitHubDesktop.exe"
    if default_path.exists():
        return str(default_path)
    
    #----------Check tools/GitHubDesktop path----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        tools_path = Path(dev_root) / "tools" / "GitHubDesktop" / "GitHubDesktop.exe"
        if tools_path.exists():
            return str(tools_path)
    
    return None

def run_with_progress(cmd, description, show_progress=True):
    """Run a command with optional progress spinner or simple status message"""
    # If this is a git command, try to find git first
    if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "git":
        git_path = find_git()
        if git_path:
            # Replace "git" with the full path
            cmd = [git_path] + cmd[1:]
            cprint(f"[DEBUG] Using git from: {git_path}", Fore.LIGHTBLACK_EX)
        else:
            cprint(f"[ERROR] Git not found. Cannot run: {cmd}", Fore.RED)
            return False
    
    if show_progress:
        # Send progress start message to GUI
        cprint(f"  {description}", Fore.CYAN)
        try:
            # Handle both string commands (shell=True) and list commands (shell=False)
            if isinstance(cmd, str):
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=False)
            cprint(f"  [OK] {description}", Fore.GREEN)
            return True
        except subprocess.CalledProcessError as e:
            cprint(f"  [ERROR] {description} failed", Fore.RED)
            if e.stdout:
                cprint(f"  STDOUT: {e.stdout}", Fore.LIGHTBLACK_EX)
            if e.stderr:
                cprint(f"  STDERR: {e.stderr}", Fore.RED)
            return False
        except FileNotFoundError as e:
            cprint(f"  [ERROR] {description} failed - command not found", Fore.RED)
            cprint(f"  Command: {cmd}", Fore.LIGHTBLACK_EX)
            return False
    else:
        #----------For quick operations, just show a simple status message----------
        cprint(f"  {description}", Fore.CYAN)
        try:
            # Handle both string commands (shell=True) and list commands (shell=False)
            if isinstance(cmd, str):
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=False)
            return True
        except subprocess.CalledProcessError as e:
            return False
        except FileNotFoundError as e:
            return False

def force_delete_git_folder(git_path):
    """Forces deletion of a .git folder with retries and error handling."""
    if not git_path.exists():
        return True

    import stat
    import time

    def on_rm_error(func, path, exc_info):
        """Error handler for shutil.rmtree - makes files writable and retries."""
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
            func(path)
        else:
            raise

    #----------Try multiple times with increasing delays----------
    for attempt in range(3):
        try:
            shutil.rmtree(git_path, onerror=on_rm_error)
            return True
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            else:
                cprint(f"[ERROR] Failed to remove .git folder after 3 attempts: {e}", Fore.RED)
                return False

    return True

def install_clibutil_direct():
    """Install ClibUtil directly without temporary folders using git sparse checkout"""
    cprint("[INFO] Installing ClibUtil dependency...", Fore.CYAN)
    
    clib_dest = Path.cwd() / "ClibUtil"
    if clib_dest.exists():
        cprint("[INFO] Removing existing ClibUtil directory...", Fore.CYAN)
        shutil.rmtree(clib_dest, ignore_errors=True)
    
    clib_dest.mkdir(parents=True, exist_ok=True)
    cprint(f"[INFO] Installing to: {clib_dest}", Fore.CYAN)
    
    try:
        # Initialize git repository in destination
        subprocess.run(["git", "init"], cwd=clib_dest, capture_output=True, text=True, check=True)
        
        # Add remote
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/powerof3/ClibUtil.git"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True)
        
        # Enable sparse checkout
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True)
        
        # Configure sparse checkout to only get the include/ClibUtil folder
        sparse_checkout_file = clib_dest / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sparse_checkout_file, 'w') as f:
            f.write("include/ClibUtil/\n")
        
        # Fetch and checkout
        subprocess.run(["git", "fetch", "--depth=1", "origin"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True)
        subprocess.run(["git", "checkout", "FETCH_HEAD"], 
                      cwd=clib_dest, capture_output=True, text=True, check=True)
        
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
        
        cprint("[OK] ClibUtil installed successfully.", Fore.GREEN)
        return True
        
    except (subprocess.CalledProcessError, Exception) as e:
        cprint(f"[WARN] Sparse checkout failed, trying fallback method: {e}", Fore.YELLOW)
        # Fallback: use the old method with temporary folder
        return install_clibutil_fallback()


def install_xbyak_direct():
    """Install xbyak directly without temporary folders using git sparse checkout"""
    cprint("[INFO] Installing xbyak dependency...", Fore.CYAN)
    
    xbyak_dest = Path.cwd() / "xbyak"
    if xbyak_dest.exists():
        cprint("[INFO] Removing existing xbyak directory...", Fore.CYAN)
        shutil.rmtree(xbyak_dest, ignore_errors=True)
    
    xbyak_dest.mkdir(parents=True, exist_ok=True)
    cprint(f"[INFO] Installing to: {xbyak_dest}", Fore.CYAN)
    
    try:
        # Initialize git repository in destination
        subprocess.run(["git", "init"], cwd=xbyak_dest, capture_output=True, text=True, check=True)
        
        # Add remote
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/herumi/xbyak.git"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True)
        
        # Enable sparse checkout
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True)
        
        # Configure sparse checkout to only get the xbyak folder
        sparse_checkout_file = xbyak_dest / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sparse_checkout_file, 'w') as f:
            f.write("xbyak/\n")
        
        # Fetch and checkout
        subprocess.run(["git", "fetch", "--depth=1", "origin"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True)
        subprocess.run(["git", "checkout", "FETCH_HEAD"], 
                      cwd=xbyak_dest, capture_output=True, text=True, check=True)
        
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
        
        cprint("[OK] xbyak installed successfully.", Fore.GREEN)
        return True
        
    except (subprocess.CalledProcessError, Exception) as e:
        cprint(f"[WARN] Sparse checkout failed, trying fallback method: {e}", Fore.YELLOW)
        # Fallback: use the old method with temporary folder
        return install_xbyak_fallback()


def install_clibutil_fallback():
    """Fallback method using temporary folder (old approach)"""
    cprint("[INFO] Using fallback method for ClibUtil...", Fore.YELLOW)
    temp_clib = Path.cwd() / "_clibutil_temp"
    if temp_clib.exists():
        shutil.rmtree(temp_clib, ignore_errors=True)
    
    if run_with_progress(
        ["git", "clone", "--depth=1", "https://github.com/powerof3/ClibUtil.git", str(temp_clib)],
        "Installing ClibUtil (fallback)...",
        show_progress=True
    ):
        clib_dest = Path.cwd() / "ClibUtil"
        clib_dest.mkdir(parents=True, exist_ok=True)
        
        run_with_progress(
            f"xcopy /E /I /Y \"{temp_clib}\\include\\ClibUtil\" \"{clib_dest}\"",
            "Copying ClibUtil files (fallback)...",
            show_progress=False
        )
        
        shutil.rmtree(temp_clib, ignore_errors=True)
        cprint("[OK] ClibUtil installed successfully (fallback).", Fore.GREEN)
        return True
    else:
        shutil.rmtree(temp_clib, ignore_errors=True)
        return False


def install_xbyak_fallback():
    """Fallback method using temporary folder (old approach)"""
    cprint("[INFO] Using fallback method for xbyak...", Fore.YELLOW)
    temp_xbyak = Path.cwd() / "_xbyak_temp"
    if temp_xbyak.exists():
        shutil.rmtree(temp_xbyak, ignore_errors=True)
    
    if run_with_progress(
        ["git", "clone", "--depth=1", "https://github.com/herumi/xbyak.git", str(temp_xbyak)],
        "Installing xbyak (fallback)...",
        show_progress=True
    ):
        xbyak_dest = Path.cwd() / "xbyak"
        if xbyak_dest.exists():
            shutil.rmtree(xbyak_dest, ignore_errors=True)
        
        run_with_progress(
            f"xcopy /E /I /Y \"{temp_xbyak}\\xbyak\" \"{xbyak_dest}\"",
            "Copying xbyak files (fallback)...",
            show_progress=False
        )
        
        shutil.rmtree(temp_xbyak, ignore_errors=True)
        cprint("[OK] xbyak installed successfully (fallback).", Fore.GREEN)
        return True
    else:
        shutil.rmtree(temp_xbyak, ignore_errors=True)
        return False

def run_create_project():

    #----------SECTION 1: Resolve Dev Root----------
    cprint("=== RESOLVING DEVELOPMENT ROOT ===", Fore.CYAN + Style.BRIGHT)
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set. Run the setup script first.", Fore.RED)
        return

    dev_root = Path(dev_root).resolve()
    cprint(f"[INFO] Development root: {dev_root}", Fore.CYAN)
    
    projects_dir = dev_root / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    cprint(f"[INFO] Projects directory: {projects_dir}", Fore.CYAN)
    
    os.chdir(projects_dir)
    cprint(f"[INFO] Changed to projects directory: {projects_dir}", Fore.CYAN)
    
    # Clean up any existing temporary directories from previous failed runs
    # No longer needed since we use direct installation without temp folders
    # temp_dirs = ["_clibutil_temp", "_xbyak_temp"]
    # for temp_dir in temp_dirs:
    #     temp_path = Path.cwd() / temp_dir
    #     if temp_path.exists():
    #         cprint(f"[INFO] Cleaning up leftover temporary directory from previous run: {temp_dir}", Fore.CYAN)
    #         force_delete_git_folder(temp_path)

    #----------SECTION 2: Collect Metadata----------
    print()
    cprint("=== PROJECT INFO ===", Fore.CYAN + Style.BRIGHT)

    plugin_name = get_env_or_prompt("__CLIBDT_FORCE_PROJECT_NAME", "Enter your new plugin/project name:")
    if not plugin_name:
        cprint("[CANCELLED] Project creation cancelled.", Fore.YELLOW)
        return

    project_dir = projects_dir / plugin_name
    cprint(f"[INFO] Project directory: {project_dir}", Fore.CYAN)
    
    if project_dir.exists():
        cprint("[ERROR] A project with that name already exists.", Fore.RED)
        return

    version     = get_env_or_prompt("__CLIBDT_FORCE_VERSION",     "Enter plugin version [Default: 1.0.0]:", "1.0.0")
    author      = get_env_or_prompt("__CLIBDT_FORCE_AUTHOR",      "Enter author name [Default: Unknown]:", "Unknown")
    description = get_env_or_prompt("__CLIBDT_FORCE_DESC",        "Enter a short description [Default: No description provided.]:", "No description provided.")
    
    cprint(f"[INFO] Project name: {plugin_name}", Fore.CYAN)
    cprint(f"[INFO] Version: {version}", Fore.CYAN)
    cprint(f"[INFO] Author: {author}", Fore.CYAN)
    cprint(f"[INFO] Description: {description}", Fore.CYAN)
    cprint("[OK] Project metadata collected.", Fore.GREEN)

    #----------SECTION 3: Clone Template----------
    print()
    cprint("=== SETTING UP PROJECT ===", Fore.CYAN + Style.BRIGHT)

    cprint(f"[INFO] Cloning template to: {project_dir}", Fore.CYAN)
    if not run_with_progress(
        ["git", "clone", "--recurse-submodules",
                        "https://github.com/PrismaUI-SKSE/PrismaUI-Example-Plugin.git", str(project_dir)],
        "Cloning template repository..."
    ):
        cprint("[ERROR] Git clone failed.", Fore.RED)
        return

    os.chdir(project_dir)
    cprint(f"[INFO] Changed to project directory: {project_dir}", Fore.CYAN)
    cprint("[OK] Template repository cloned successfully.", Fore.GREEN)

    #----------Clean up and initialize git----------
    cprint("[INFO] Cleaning up template Git history...", Fore.CYAN)
    shutil.rmtree(".git", ignore_errors=True)
    cprint("[OK] Template Git history removed.", Fore.GREEN)
    
    cprint("[INFO] Initializing new Git repository...", Fore.CYAN)
    run_with_progress(["git", "init"], "Initializing Git repository...", show_progress=False)
    run_with_progress(["git", "add", "."], "Staging files...", show_progress=False)
    run_with_progress(["git", "commit", "-m", "Initial commit from PrismaUI Example Plugin template"], "Creating initial commit...", show_progress=False)
    cprint("[OK] Git repository initialized and configured.", Fore.GREEN)

    #----------SECTION 4: Install Dependencies----------
    print()
    cprint("=== INSTALLING DEPENDENCIES ===", Fore.CYAN + Style.BRIGHT)

    #----------Install ClibUtil----------
    if install_clibutil_direct():
        cprint("[OK] ClibUtil installed successfully.", Fore.GREEN)
    else:
        cprint("[ERROR] Failed to install ClibUtil", Fore.RED)
        return

    #----------Install xbyak----------
    if install_xbyak_direct():
        cprint("[OK] xbyak installed successfully.", Fore.GREEN)
    else:
        cprint("[ERROR] Failed to install xbyak", Fore.RED)
        return

    #----------SECTION 5: Generate Configuration Files----------
    print()
    cprint("=== GENERATING CONFIGURATION ===", Fore.CYAN + Style.BRIGHT)
    try:
        from modules.generate_xmakelua import generate_xmake_lua
        from modules.generate_clib_project import generate_clib_project_json
        
        # Ensure all metadata is not None
        if None in (plugin_name, version, author, description):
            cprint("[CANCELLED] Metadata entry was skipped. Configuration files not generated.", Fore.LIGHTBLACK_EX)
            return
        
        # Generate clib_project.json for project detection
        clib_project_path = Path.cwd() / "clib_project.json"
        cprint(f"[INFO] Generating clib_project.json at: {clib_project_path}", Fore.CYAN)
        generate_clib_project_json(clib_project_path, plugin_name, version, author, description)
        cprint("[OK] clib_project.json generated.", Fore.GREEN)
        
        # Generate clibdt_project.json for ClibDT project detection
        clibdt_project_path = Path.cwd() / "clibdt_project.json"
        cprint(f"[INFO] Generating clibdt_project.json at: {clibdt_project_path}", Fore.CYAN)
        
        # Create clibdt_project.json with the same structure as refresh_project.py
        clibdt_config = {
            "project_name": plugin_name,
            "version": version,
            "author": author,
            "description": description,
            "created_date": datetime.now().isoformat(),
                            "clibdt_version": VERSION,
            "project_type": "commonlibsse-ng",
            "build_system": "xmake",
            "xmake_version": "3.0.1",
            "dependencies": {
                "clibutil": "latest",
                "xbyak": "latest"
            }
        }
        
        with open(clibdt_project_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(clibdt_config, f, indent=2)
        
        cprint("[OK] clibdt_project.json generated.", Fore.GREEN)
        
        # Generate xmake.lua for build configuration
        xmake_path = Path.cwd() / "xmake.lua"
        cprint(f"[INFO] Generating xmake.lua at: {xmake_path}", Fore.CYAN)
        generate_xmake_lua(xmake_path, plugin_name, version, author, description)
        cprint("[OK] xmake.lua configuration generated.", Fore.GREEN)
    except Exception as e:
        cprint(f"[ERROR] Failed to generate configuration files: {e}", Fore.RED)

    #----------SECTION 6: Detach Git----------
    print()
    cprint("=== CLEANING UP ===", Fore.CYAN + Style.BRIGHT)
    cprint("[INFO] Detaching from template Git history...", Fore.CYAN)
    if Path(".git").exists():
        if force_delete_git_folder(Path(".git")):
            cprint("[OK] Template Git history removed.", Fore.GREEN)
        else:
            cprint("[WARNING] Could not remove .git folder. You may need to close any programs using it.", Fore.YELLOW)
    else:
        cprint("[OK] No .git folder found. Nothing to remove.", Fore.GREEN)

    #----------SECTION 7: Git Commit----------
    print()
    cprint("=== FINALIZING PROJECT ===", Fore.CYAN + Style.BRIGHT)
    
    # Initialize git repository
    cprint("[INFO] Initializing new Git repository...", Fore.CYAN)
    run_with_progress(["git", "init"], "Initializing Git repository...", show_progress=False)
    cprint("[OK] Git repository initialized.", Fore.GREEN)
    
    # Stage all files
    cprint("[INFO] Staging all project files...", Fore.CYAN)
    run_with_progress(["git", "add", "."], "Staging files...", show_progress=False)
    cprint("[OK] Files staged successfully.", Fore.GREEN)
    
    # Check if there are staged changes
    git_path = find_git()
    if git_path:
        result = subprocess.run([git_path, "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            cprint("[INFO] Ready to commit your changes.", Fore.CYAN)
            
            # Use default commit message to avoid thread issues
            commit_msg = "Initial commit from PrismaUI Example Plugin template"
            cprint(f"[INFO] Creating commit with message: {commit_msg}", Fore.CYAN)
            run_with_progress(["git", "commit", "-m", commit_msg], "Creating initial commit...", show_progress=False)
            cprint("[OK] Changes committed successfully.", Fore.GREEN)
        else:
            cprint("[INFO] No changes to commit. Working tree is clean.", Fore.GREEN)
    else:
        cprint("[WARNING] Git not found. Skipping commit check.", Fore.YELLOW)

    #----------SECTION 8: Final Cleanup----------
    print()
    cprint("=== FINAL CLEANUP ===", Fore.CYAN + Style.BRIGHT)
    
    # No temporary directories to clean up since we use direct installation
    # temp_dirs = ["_clibutil_temp", "_xbyak_temp"]
    # for temp_dir in temp_dirs:
    #     temp_path = Path.cwd() / temp_dir
    #     if temp_path.exists():
    #         cprint(f"[INFO] Removing leftover temporary directory: {temp_dir}", Fore.CYAN)
    #         if force_delete_git_folder(temp_path):
    #             cprint(f"[OK] Removed {temp_dir}", Fore.GREEN)
    #         else:
    #             cprint(f"[WARNING] Could not remove {temp_dir}. You may need to remove it manually.", Fore.YELLOW)
    
    #----------DONE----------
    print()
    cprint("=== PROJECT CREATION COMPLETE ===", Fore.GREEN + Style.BRIGHT)
    cprint("Project created successfully!", Fore.GREEN)
    cprint(f"Project location: {project_dir}", Fore.CYAN)
    cprint("Ready to start coding!", Fore.GREEN)
    if not os.getenv("__CLIBDT_FORCE_PROJECT_NAME"):
        input("Press Enter to return...")

class CreateProjectPanel(QWidget):
    project_created = pyqtSignal()
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.theme_manager = theme_manager
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Header with styling and divider line
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Create New Project")
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
        desc = QLabel("Create a new CommonLibSSE-NG project with all dependencies.")
        desc.setObjectName("section_desc")
        layout.addWidget(desc)
        
        # Project Info section
        project_section = QWidget()
        project_section.setObjectName("project_section")
        project_layout = QVBoxLayout(project_section)
        project_layout.setContentsMargins(0, 0, 0, 8)
        project_layout.setSpacing(8)
        
        # Project Name
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel("Project Name:")
        name_label.setObjectName("name_label")
        name_label.setFixedWidth(120)
        name_row.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        self.name_edit.setObjectName("name_edit")
        self.name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_edit.setMinimumWidth(200)
        self.name_edit.setMinimumHeight(24)
        self.name_edit.setMaximumHeight(32)
        name_row.addWidget(self.name_edit)
        project_layout.addLayout(name_row)
        
        # Version
        version_row = QHBoxLayout()
        version_row.setSpacing(8)
        version_row.setContentsMargins(0, 0, 0, 0)
        
        version_label = QLabel("Version:")
        version_label.setObjectName("version_label")
        version_label.setFixedWidth(120)
        version_row.addWidget(version_label)
        
        self.version_edit = QLineEdit("1.0.0")
        self.version_edit.setObjectName("version_edit")
        self.version_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.version_edit.setMinimumWidth(200)
        self.version_edit.setMinimumHeight(24)
        self.version_edit.setMaximumHeight(32)
        version_row.addWidget(self.version_edit)
        project_layout.addLayout(version_row)
        
        # Author
        author_row = QHBoxLayout()
        author_row.setSpacing(8)
        author_row.setContentsMargins(0, 0, 0, 0)
        
        author_label = QLabel("Author:")
        author_label.setObjectName("author_label")
        author_label.setFixedWidth(120)
        author_row.addWidget(author_label)
        
        self.author_edit = QLineEdit("Unknown")
        self.author_edit.setObjectName("author_edit")
        self.author_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.author_edit.setMinimumWidth(200)
        self.author_edit.setMinimumHeight(24)
        self.author_edit.setMaximumHeight(32)
        author_row.addWidget(self.author_edit)
        project_layout.addLayout(author_row)
        
        # Description
        desc_row = QHBoxLayout()
        desc_row.setSpacing(8)
        desc_row.setContentsMargins(0, 0, 0, 0)
        
        desc_label = QLabel("Description:")
        desc_label.setObjectName("desc_label")
        desc_label.setFixedWidth(120)
        desc_row.addWidget(desc_label)
        
        self.desc_edit = QLineEdit("No description provided.")
        self.desc_edit.setObjectName("desc_edit")
        self.desc_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.desc_edit.setMinimumWidth(200)
        self.desc_edit.setMinimumHeight(24)
        self.desc_edit.setMaximumHeight(32)
        desc_row.addWidget(self.desc_edit)
        project_layout.addLayout(desc_row)
        
        layout.addWidget(project_section)
        
        # Add ProgressWidget
        self.progress_widget = ProgressWidget(self, title="Creating Project", show_cancel=True)
        self.progress_widget.completed.connect(self._on_progress_completed)
        self.progress_widget.cancelled.connect(self._on_progress_cancelled)
        layout.addWidget(self.progress_widget)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        self.create_btn = QPushButton("Create Project")
        self.create_btn.setProperty("btnType", "success")
        self.create_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.create_btn.setMinimumHeight(24)
        self.create_btn.setMaximumHeight(32)
        self.create_btn.clicked.connect(self.on_create)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("btnType", "uninstall")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setMinimumHeight(24)
        self.stop_btn.setMaximumHeight(32)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setEnabled(False)
        
        btn_row.addWidget(self.create_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)
        
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
    
    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)
    
    def on_create(self):
        # Validate inputs
        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name.")
            return
        dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
        if dev_root:
            project_dir = Path(dev_root) / "projects" / project_name
            if project_dir.exists():
                QMessageBox.critical(self, "Project Exists", f"A project with the name '{project_name}' already exists.")
                return
        self.create_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.name_edit.setEnabled(False)
        self.version_edit.setEnabled(False)
        self.author_edit.setEnabled(False)
        self.desc_edit.setEnabled(False)
        version = self.version_edit.text().strip()
        author = self.author_edit.text().strip()
        description = self.desc_edit.text().strip()
        def project_creation_op(progress_callback, status_callback):
            import time
            from modules.generate_xmakelua import generate_xmake_lua
            from modules.generate_clib_project import generate_clib_project_json
            # Section 1: Resolve Dev Root
            status_callback("Step 1/6: Resolving development root...")
            progress_callback(5, 100)
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if not dev_root:
                raise Exception("XSE_CLIBDT_DEVROOT is not set. Run the setup script first.")
            dev_root = Path(dev_root).resolve()
            projects_dir = dev_root / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            os.chdir(projects_dir)
            # Section 2: Collect Metadata
            status_callback("Step 2/6: Collecting project metadata...")
            progress_callback(10, 100)
            plugin_name = project_name
            project_dir = projects_dir / plugin_name
            if project_dir.exists():
                raise Exception("A project with that name already exists.")
            # Section 3: Clone Template
            status_callback("Step 3/6: Cloning project template...")
            progress_callback(20, 100)
            import subprocess, shutil
            result = subprocess.run([
                "git", "clone", "--recurse-submodules",
                "https://github.com/PrismaUI-SKSE/PrismaUI-Example-Plugin.git", str(project_dir)
            ], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            os.chdir(project_dir)
            # Clean up and initialize git
            status_callback("Step 3/6: Initializing Git repository...")
            progress_callback(30, 100)
            shutil.rmtree(".git", ignore_errors=True)
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit from PrismaUI Example Plugin template"], check=True)
            # Section 4: Install Dependencies
            status_callback("Step 4/6: Installing ClibUtil dependency...")
            progress_callback(40, 100)
            if not install_clibutil_direct():
                raise Exception("Failed to install ClibUtil")
            status_callback("Step 4/6: Installing xbyak dependency...")
            progress_callback(50, 100)
            if not install_xbyak_direct():
                raise Exception("Failed to install xbyak")
            # Section 5: Generate Configuration Files
            status_callback("Step 5/6: Generating configuration files...")
            progress_callback(70, 100)
            try:
                clib_project_path = Path.cwd() / "clib_project.json"
                generate_clib_project_json(clib_project_path, plugin_name, version, author, description)
                clibdt_project_path = Path.cwd() / "clibdt_project.json"
                clibdt_config = {
                    "project_name": plugin_name,
                    "version": version,
                    "author": author,
                    "description": description,
                    "created_date": datetime.now().isoformat(),
                    "clibdt_version": VERSION,
                    "project_type": "commonlibsse-ng",
                    "build_system": "xmake",
                    "xmake_version": "3.0.1",
                    "dependencies": {
                        "clibutil": "latest",
                        "xbyak": "latest"
                    }
                }
                with open(clibdt_project_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(clibdt_config, f, indent=2)
                xmake_path = Path.cwd() / "xmake.lua"
                generate_xmake_lua(xmake_path, plugin_name, version, author, description)
            except Exception as e:
                raise Exception(f"Failed to generate configuration files: {e}")
            # Section 6: Clean up
            status_callback("Step 6/6: Finalizing project setup...")
            progress_callback(90, 100)
            if Path(".git").exists():
                force_delete_git_folder(Path(".git"))
            status_callback("Project creation completed successfully!")
            progress_callback(100, 100)
            return True
        self.progress_widget.start_operation(project_creation_op)
    
    def on_stop(self):
        if self.progress_widget and self.progress_widget.is_running():
            self.progress_widget.cancel_operation()
            self.stop_btn.setEnabled(False)
            self.name_edit.setEnabled(True)
            self.version_edit.setEnabled(True)
            self.author_edit.setEnabled(True)
            self.desc_edit.setEnabled(True)
            QMessageBox.warning(self, "Cancelled", "Project creation was cancelled.")
    
    def _on_progress_completed(self):
        # Re-enable inputs and buttons
        self.create_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.name_edit.setEnabled(True)
        self.version_edit.setEnabled(True)
        self.author_edit.setEnabled(True)
        self.desc_edit.setEnabled(True)
        QMessageBox.information(self, "Project Created", "Project created successfully!")
        self.name_edit.clear()
        self.version_edit.setText("1.0.0")
        self.author_edit.setText("Unknown")
        self.desc_edit.setText("No description provided.")
        self.project_created.emit()
    
    def _on_progress_cancelled(self):
        self.create_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.name_edit.setEnabled(True)
        self.version_edit.setEnabled(True)
        self.author_edit.setEnabled(True)
        self.desc_edit.setEnabled(True)
        QMessageBox.warning(self, "Cancelled", "Project creation was cancelled.")
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def apply_theme(self):
        """Apply current theme to the panel"""
        if self.theme_manager:
            self.setStyleSheet(self.theme_manager.get_create_project_style())
        else:
            # Fallback styling
            try:
                from modules.theme_manager import ThemeManager
                fallback_manager = ThemeManager()
                self.setStyleSheet(fallback_manager.get_create_project_style())
            except Exception:
                # Ultimate fallback with basic styling
                self.setStyleSheet("""
                    QWidget {
                        background-color: #1e1e1e;
                        color: #e0e0e0;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QLabel {
                        background-color: transparent;
                        color: #e0e0e0;
                        font-size: 11px;
                    }
                    QLineEdit {
                        background-color: #2d2d2d;
                        color: #e0e0e0;
                        border: 2px solid #404040;
                        border-radius: 4px;
                        padding: 6px 8px;
                        font-size: 11px;
                    }
                    QPushButton {
                        background-color: #0078d4;
                        color: #ffffff;
                        border: 1px solid #0078d4;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                """)

