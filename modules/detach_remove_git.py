import os
import shutil
from pathlib import Path
from colorama import init, Fore, Style
import stat

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def confirm(prompt, default="n"):
    resp = input(Style.RESET_ALL + prompt).strip().lower()
    if resp == "m":
        return "m"
    if not resp:
        return default.lower()
    return resp

def force_rmtree(path, retries=3):
    import time
    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=on_rm_error)
            return True
        except Exception as e:
            if attempt < retries - 1:
                cprint(f"[WARN] Could not delete {path} (attempt {attempt+1}/{retries}): {e}", Fore.YELLOW)
                cprint("[INFO] Retrying after making files writable...", Fore.LIGHTBLACK_EX)
                make_all_writable(path)
                time.sleep(1)
            else:
                cprint(f"[ERROR] Failed to delete {path} after {retries} attempts: {e}", Fore.RED)
                return False

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        cprint(f"[ERROR] Could not forcibly delete {path}: {e}", Fore.RED)

def make_all_writable(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), stat.S_IWRITE)
            except Exception:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IWRITE)
            except Exception:
                pass

def run_detach_remove_git():
    cprint("\n[DETACH GIT] Remove Git History from Project", Fore.CYAN + Style.BRIGHT)
    cprint("[INFO] Current folder:", Fore.YELLOW)
    cprint(f"  {os.getcwd()}\n", Fore.LIGHTBLACK_EX)

    git_folder = Path(".git")
    if not git_folder.exists() or not git_folder.is_dir():
        cprint("[OK] No .git folder found. Nothing to remove.", Fore.GREEN)
        input(Style.RESET_ALL + "Press Enter to return to the main menu...")
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return

    cprint("[CAUTION] This will permanently remove all Git history from this project!", Fore.RED + Style.BRIGHT)
    cprint("[WARNING] This cannot be undone.", Fore.RED)
    cprint("[INFO] Enter M to return to the main menu.", Fore.LIGHTBLACK_EX)
    print()

    resp = confirm("Delete .git folder and detach from Git? (Y/N): ", default="n")
    if resp == "m":
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    if resp != "y":
        cprint("[INFO] Kept existing .git folder. No changes made.", Fore.LIGHTBLACK_EX)
        input(Style.RESET_ALL + "Press Enter to return to the main menu...")
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return

    try:
        #----------Robust force delete----------
        if force_rmtree(git_folder):
            if git_folder.exists():
                cprint("[ERROR] Failed to remove .git folder. Check permissions and try again.", Fore.RED)
            else:
                cprint("[OK] .git folder removed successfully. Project is now detached from Git.", Fore.GREEN)
        else:
            cprint("[ERROR] Could not remove .git folder after multiple attempts.", Fore.RED)
    except Exception as e:
        cprint(f"[ERROR] Exception while removing .git: {e}", Fore.RED)

    print()
    input(Style.RESET_ALL + "Press Enter to return to the main menu...")
    cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)

if __name__ == "__main__":
    run_detach_remove_git()
