import os
import sys
from pathlib import Path
from colorama import init, Fore, Style
from modules.helpers import cprint

# Initialize color output
try:
    init()
except ImportError:
    print("[ERROR] Missing 'colorama'. Run: pip install colorama")
    sys.exit(1)


#----------check----------
def check_required_env_vars():
    required = {
        "XSE_CLIBDT_DEVROOT": "Dev Project Dir",
        "XSE_TES5_GAME_PATH": "Skyrim GAME Path",
        "XSE_TES5_MODS_PATH": "Skyrim MODS Path"
    }

    missing_vars = []

    for var, label in required.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append((var, label))
        else:
            path = Path(value)
            if not path.exists() or not path.is_dir():
                missing_vars.append((var, label))

    if missing_vars:
        cprint("[WARNING] Missing or invalid environment variables (run option 1 to set):", Fore.RED)
        for var, label in missing_vars:
            cprint(f"   - {var} ({label})", Fore.LIGHTYELLOW_EX)


#----------set----------
def set_required_env_vars_interactively():
    variables = {
        "XSE_CLIBDT_DEVROOT": "Dev Project Dir",
        "XSE_TES5_GAME_PATH": "Skyrim GAME Path",
        "XSE_TES5_MODS_PATH": "Skyrim MODS Path"
    }

    for var, label in variables.items():
        print()
        path = input(f"Enter {label}: ").strip()

        if not path:
            cprint(f"[SKIP] {var} not set.", Fore.LIGHTBLACK_EX)
            continue

        if not Path(path).exists():
            cprint(f"[ERROR] Invalid path for {label}: {path}", Fore.RED)
            continue

        # Set for session
        os.environ[var] = path

        # Set for persistent registry (Windows only)
        import subprocess
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            subprocess.run(["setx", var, path], shell=True, creationflags=creationflags)
            cprint(f"[OK] Set {var} -> {path}", Fore.GREEN)
        except Exception as e:
            cprint(f"[ERROR] Failed to set {var}: {e}", Fore.RED)


#----------main----------
if __name__ == "__main__":
    check_required_env_vars()
