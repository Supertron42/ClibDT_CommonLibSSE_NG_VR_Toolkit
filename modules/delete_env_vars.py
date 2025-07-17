from pathlib import Path
from colorama import init, Fore, Style
import sys
import os
import getpass
import platform

init(autoreset=True, strip=False, convert=True)

ENV_VARS = [
    "XSE_CLIBDT_DEVROOT",
    "XSE_TES5_GAME_PATH",
    "XSE_TES5_MODS_PATH",
    "XSE_GIT_ROOT",
    "XSE_MSVCTOOLS_ROOT",
    "XSE_XMAKE_ROOT",
    "XSE_GITHUB_DESKTOP_PATH",
]

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def confirm_prompt() -> bool:
    print()
    cprint("WARNING: This will delete all ClibDT-related environment variables for THIS SESSION ONLY.\n", Fore.LIGHTRED_EX)
    cprint("The following environment variables will be removed from this session:", Fore.YELLOW)
    for var in ENV_VARS:
        print(f"  - {var}")
    print()
    return input("Are you sure you want to remove these for this session? [y/N]: ").strip().lower() == "y"

def delete_env_vars():
    cprint("\nDeleting environment variables from current session...\n", Fore.CYAN)
    for var in ENV_VARS:
        if var in os.environ:
            del os.environ[var]
            cprint(f"[OK] Removed from current session: {var}", Fore.GREEN)
        else:
            cprint(f"[INFO] {var} not set in current session.", Fore.LIGHTBLACK_EX)
    #----------SAFEGUARD: Ensure USERPROFILE/HOME is still set----------
    if platform.system() == "Windows":
        if "USERPROFILE" not in os.environ or not os.environ["USERPROFILE"]:
            user = getpass.getuser()
            fallback = f"C:\\Users\\{user}"
            os.environ["USERPROFILE"] = fallback
            cprint(f"[WARN] USERPROFILE was missing; restored to {fallback}", Fore.YELLOW)
    else:
        if "HOME" not in os.environ or not os.environ["HOME"]:
            user = getpass.getuser()
            fallback = f"/home/{user}"
            os.environ["HOME"] = fallback
            cprint(f"[WARN] HOME was missing; restored to {fallback}", Fore.YELLOW)

def main():
    if not confirm_prompt():
        cprint("Cancelled by user. No changes made.", Fore.YELLOW)
        return
    delete_env_vars()
    cprint("\n[DONE] Environment cleanup complete for this session.", Fore.MAGENTA)
    input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    main()
