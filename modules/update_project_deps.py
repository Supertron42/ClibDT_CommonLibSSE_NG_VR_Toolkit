import os
import subprocess
import shutil
from pathlib import Path
from colorama import init, Fore, Style
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_yesno(message, default="n"):
    val = input(f"{message} ").strip().lower()
    if val == "m":
        return "M"
    return val if val else default.lower()

def run_with_progress(cmd, description, console, show_progress=True):
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=None)
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                progress.update(task, completed=True)
                return result
            except subprocess.CalledProcessError as e:
                progress.update(task, completed=True)
                return None
    else:
        
        cprint(f"  {description}", Fore.CYAN)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return None

def update_project_deps():
    console = Console()
    
    #----------dev root----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] Missing environment variable: XSE_CLIBDT_DEVROOT", Fore.RED)
        input("\nPress Enter to return...")
        return

    dev_root_path = Path(dev_root).resolve()
    project_root = Path.cwd().resolve()

    if not str(project_root).startswith(str(dev_root_path)):
        cprint("[ERROR] This script must be run inside a subfolder of your dev projects root:", Fore.RED)
        cprint(f"        {dev_root_path}", Fore.YELLOW)
        input("\nPress Enter to return...")
        return

    if not (project_root / "xmake.lua").exists():
        cprint("[ERROR] This script must be run from a folder containing xmake.lua", Fore.RED)
        input("\nPress Enter to return...")
        return

    cprint("[OK] Project folder confirmed.", Fore.GREEN)
    print()

    #----------xmake repo --update----------
    cprint("=== UPDATING PACKAGE INDEX ===", Fore.CYAN + Style.BRIGHT)
    do_repo = prompt_yesno("Update xmake's package repository index? [Y/n]: ", "y")
    if do_repo == "m":
        return
    if do_repo == "y":
        result = run_with_progress(
            ["xmake", "repo", "--update"],
            "📦 Updating xmake package index...",
            console,
            show_progress=True
        )

        if result and result.returncode == 0:
            cprint("[OK] Package index updated successfully.", Fore.GREEN)
        elif result and "refusing to merge unrelated histories" in result.stderr:
            cprint("[ERROR] Detected unrelated Git histories in xmake-repo.", Fore.RED)
            xmake_repo_path = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.xmake"),
                "repos", "xmake-repo"
            )
            if os.path.exists(xmake_repo_path):
                shutil.rmtree(xmake_repo_path)
                cprint(f"[INFO] Removed corrupted repo: {xmake_repo_path}", Fore.YELLOW)

            cprint("[INFO] Retrying package index update...", Fore.CYAN)
            retry = run_with_progress(
                ["xmake", "repo", "--update"],
                "📦 Retrying package index update...",
                console,
                show_progress=True
            )
            if retry and retry.returncode == 0:
                cprint("[OK] Package index updated after fixing repo.", Fore.GREEN)
            else:
                cprint("[ERROR] Retry failed. Please investigate manually.", Fore.RED)
        else:
            cprint("[ERROR] Failed to update package index.", Fore.RED)
    else:
        cprint("[INFO] Skipped updating package index.", Fore.LIGHTBLACK_EX)

    #----------xmake require --upgrade----------
    print()
    cprint("=== UPGRADING PROJECT DEPENDENCIES ===", Fore.YELLOW + Style.BRIGHT)
    cprint("   This will update all required libraries to their latest versions.", Fore.LIGHTYELLOW_EX)
    cprint("   Warning: This may change library versions and could affect compatibility.", Fore.LIGHTYELLOW_EX)
    do_upgrade = prompt_yesno("Upgrade all project dependencies to latest versions? [Y/n]: ", "n")
    if do_upgrade == "m":
        return
    if do_upgrade == "y":
        result = run_with_progress(
            ["xmake", "require", "--upgrade"],
            "⬆️  Upgrading project dependencies...",
            console,
            show_progress=True
        )
        if result and result.returncode == 0:
            cprint("[OK] Dependencies upgraded successfully.", Fore.GREEN)
        else:
            cprint("[ERROR] Failed to upgrade dependencies.", Fore.RED)
    else:
        cprint("[INFO] Skipped upgrading dependencies.", Fore.LIGHTBLACK_EX)

    print()
    cprint("✅ All operations completed!", Fore.GREEN)
    input("\nPress Enter to return...")

if __name__ == "__main__":
    update_project_deps()
