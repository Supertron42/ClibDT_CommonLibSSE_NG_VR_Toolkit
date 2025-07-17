import os
import sys
import shutil
import subprocess
from pathlib import Path
from colorama import init, Fore, Style
from modules.git_stage_and_commit import run_git_commit
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

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

def run_with_progress(cmd, description, console, show_progress=True):
    """Run a command with optional progress spinner or simple status message"""
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description, total=None)
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                progress.update(task, completed=True)
                return True
            except subprocess.CalledProcessError as e:
                progress.update(task, completed=True)
                return False
    else:
        #----------For quick operations, just show a simple status message----------
        cprint(f"  {description}", Fore.CYAN)
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
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

def run_create_project():
    console = Console()

    #----------SECTION 1: Resolve Dev Root----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set. Run the setup script first.", Fore.RED)
        return

    dev_root = Path(dev_root).resolve()
    projects_dir = dev_root / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(projects_dir)
    cprint(f"[INFO] Using projects directory: {projects_dir}", Fore.CYAN)

    #----------SECTION 2: Collect Metadata----------
    print()
    cprint("=== PROJECT INFO ===", Fore.CYAN + Style.BRIGHT)

    plugin_name = get_env_or_prompt("__CLIBDT_FORCE_PROJECT_NAME", "Enter your new plugin/project name:")
    if not plugin_name:
        return

    project_dir = projects_dir / plugin_name
    if project_dir.exists():
        cprint("[ERROR] A project with that name already exists.", Fore.RED)
        return

    version     = get_env_or_prompt("__CLIBDT_FORCE_VERSION",     "Enter plugin version [Default: 1.0.0]:", "1.0.0")
    author      = get_env_or_prompt("__CLIBDT_FORCE_AUTHOR",      "Enter author name [Default: Unknown]:", "Unknown")
    description = get_env_or_prompt("__CLIBDT_FORCE_DESC",        "Enter a short description [Default: No description provided.]:", "No description provided.")
    cprint("[OK] Project metadata collected.", Fore.GREEN)

    #----------SECTION 3: Clone Template----------
    print()
    cprint("=== SETTING UP PROJECT ===", Fore.CYAN + Style.BRIGHT)

    if not run_with_progress(
        ["git", "clone", "--recurse-submodules",
                        "https://github.com/Supertron42/CommonLibSSE-NG-VR-Template.git", str(project_dir)],
        "📥 Cloning template repository...",
        console
    ):
        cprint("[ERROR] Git clone failed.", Fore.RED)
        return

    os.chdir(project_dir)
    cprint("[OK] Template repository cloned successfully.", Fore.GREEN)

    #----------Clean up and initialize git----------
    shutil.rmtree(".git", ignore_errors=True)
    run_with_progress(["git", "init"], "🔧 Initializing Git repository...", console, show_progress=False)
    run_with_progress(["git", "add", "."], "📝 Staging files...", console, show_progress=False)
    run_with_progress(["git", "commit", "-m", "Initial commit from CommonLibSSE-NG template"], "💾 Creating initial commit...", console, show_progress=False)
    cprint("[OK] Git repository initialized and configured.", Fore.GREEN)

    #----------SECTION 4: Install Dependencies----------
    print()
    cprint("=== INSTALLING DEPENDENCIES ===", Fore.CYAN + Style.BRIGHT)

    #----------Install ClibUtil----------
    temp_clib = Path.cwd() / "_clibutil_temp"
    if run_with_progress(
        ["git", "clone", "--depth=1", "https://github.com/powerof3/ClibUtil.git", str(temp_clib)],
        "📦 Installing ClibUtil...",
        console,
        show_progress=True
    ):
        clib_dest = Path.cwd() / "ClibUtil"
        clib_dest.mkdir(parents=True, exist_ok=True)
        run_with_progress(
            f"xcopy /E /I /Y \"{temp_clib}\\include\\ClibUtil\" \"{clib_dest}\"",
            "📋 Copying ClibUtil files...",
            console,
            show_progress=False
        )
        shutil.rmtree(temp_clib, ignore_errors=True)
        cprint("[OK] ClibUtil installed successfully.", Fore.GREEN)
    else:
        cprint("[ERROR] Failed to install ClibUtil", Fore.RED)

    #----------Install xbyak----------
    temp_xbyak = Path.cwd() / "_xbyak_temp"
    if run_with_progress(
        ["git", "clone", "--depth=1", "https://github.com/herumi/xbyak.git", str(temp_xbyak)],
        "📦 Installing xbyak...",
        console,
        show_progress=True
    ):
        xbyak_dest = Path.cwd() / "xbyak"
        if xbyak_dest.exists():
            shutil.rmtree(xbyak_dest, ignore_errors=True)
        run_with_progress(
            f"xcopy /E /I /Y \"{temp_xbyak}\\xbyak\" \"{xbyak_dest}\"",
            "📋 Copying xbyak files...",
            console,
            show_progress=False
        )
        shutil.rmtree(temp_xbyak, ignore_errors=True)
        cprint("[OK] xbyak installed successfully.", Fore.GREEN)
    else:
        cprint("[ERROR] Failed to install xbyak", Fore.RED)

    #----------SECTION 5: Generate xmake.lua----------
    print()
    cprint("=== GENERATING CONFIGURATION ===", Fore.CYAN + Style.BRIGHT)
    try:
        from modules.generate_xmakelua import generate_xmake_lua
        # Ensure all metadata is not None
        if None in (plugin_name, version, author, description):
            cprint("[CANCELLED] Metadata entry was skipped. xmake.lua not generated.", Fore.LIGHTBLACK_EX)
            return
        generate_xmake_lua(Path.cwd() / "xmake.lua", plugin_name, version, author, description)
        cprint("[OK] xmake.lua configuration generated.", Fore.GREEN)
    except Exception as e:
        cprint(f"[ERROR] Failed to generate xmake.lua: {e}", Fore.RED)

    #----------SECTION 6: Detach Git----------
    print()
    cprint("=== CLEANING UP ===", Fore.CYAN + Style.BRIGHT)
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
    run_git_commit()

    #----------DONE----------
    print()
    cprint("✅ Project created successfully!", Fore.GREEN)
    cprint(f"📁 Project location: {project_dir}", Fore.CYAN)
    cprint("🚀 Ready to start coding!", Fore.GREEN)
    if not os.getenv("__CLIBDT_FORCE_PROJECT_NAME"):
        input("Press Enter to return...")

