import os
import sys
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def restart_clibdt(extra_args=None):
    """
    Relaunch ClibDT.py from its expected parent folder location.
    Optionally pass CLI args.
    """
    this_file = Path(__file__).resolve()
    clibdt_path = this_file.parent.parent / "ClibDT.py"

    if not clibdt_path.exists():
        cprint(f"[ERROR] Could not find ClibDT.py at expected location: {clibdt_path}", Fore.RED)
        return

    args = [sys.executable, str(clibdt_path)]
    if extra_args:
        args += extra_args

    cprint(f"[INFO] Relaunching ClibDT.py...", Fore.CYAN)
    # Use CREATE_NO_WINDOW to prevent terminal popup
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    subprocess.Popen(args, close_fds=True, creationflags=creationflags)

    # Optional: exit current script if desired
    sys.exit(0)

# Example usage for testing
if __name__ == "__main__":
    restart_clibdt()
