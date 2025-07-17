# ------------------ Standard Library ----------------------
import os
import sys
import re
import subprocess
import atexit
import builtins
import webbrowser
from datetime import datetime
from pathlib import Path
import argparse
from colorama import init, Fore, Style, AnsiToWin32
init(autoreset=True) 


parser = argparse.ArgumentParser()
parser.add_argument('--no-pause', action='store_true', help='Disable input pauses for automation')
args, unknown = parser.parse_known_args()
NO_PAUSE = args.no_pause

# ------------------ Add to Module Path --------------------
sys.path.append(str(Path(__file__).parent.resolve()))

#----------requests----------
try:
    import requests
except ImportError:
    requests = None

#----------version----------
VERSION = "4.0.1"
_version_checked = False
_version_message = ""
NEXUS_URL = "https://www.nexusmods.com/skyrimspecialedition/mods/154240"

#----------env var call----------
from modules.env_var_call import check_required_env_vars

#----------project picker----------
def project_picker(require_existing_xmake=True):
    root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not root:
        cprint("[ERROR] Dev root not set. Run option 1 first.", Fore.RED)
        return None
    root_path = Path(root)
    scan_base = root_path / "projects" if (root_path / "projects").exists() else root_path
    if not scan_base.exists():
        cprint(f"[ERROR] Path does not exist: {scan_base}", Fore.RED)
        return None
    projects = []
    for subdir in scan_base.iterdir():
        if subdir.is_dir():
            if require_existing_xmake:
                if (subdir / "xmake.lua").exists():
                    projects.append(subdir)
            else:
                projects.append(subdir)
    if not projects:
        cprint("No valid projects found.", Fore.RED)
        input("Press Enter to return...")
        return None
    print("\n=========================================")
    print("    Select a Project Folder")
    print("=========================================")
    for i, p in enumerate(projects, start=1):
        print(f"{i}. {p.relative_to(scan_base)}")
    print("M. Return to main menu\n")
    userInput = input("Enter project number: ").strip()
    if userInput.lower() == "m":
        return None
    if not userInput.isdigit():
        return None
    idx = int(userInput)
    if not (1 <= idx <= len(projects)):
        return None
    return str(projects[idx - 1])

#----------run py file----------
from contextlib import contextmanager
@contextmanager
def preserve_cwd():
    old_cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_cwd)

def run_py_file(path):
        from pathlib import Path
        # Always resolve relative to the main script's directory
        base_dir = Path(__file__).parent.resolve()
        abs_path = (base_dir / path).resolve() if not Path(path).is_absolute() else Path(path)
        if not abs_path.exists():
            cprint(f"[ERROR] File not found: {abs_path}", Fore.RED)
            input("Press Enter to continue...")
            return
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                code = compile(f.read(), str(abs_path), 'exec')
                exec(code, {"__name__": "__main__", "__file__": str(abs_path)})
        except Exception as e:
            cprint(f"[ERROR] Failed to run: {abs_path}", Fore.RED)
            print(e)
            input("Press Enter to continue...")

#----------download----------
import urllib.request
import ssl
def download_with_progress(url, dest_path, fallback_url=None):
    try:
        with urllib.request.urlopen(url) as response, open(dest_path, 'wb') as out_file:
            file_size = int(response.info().get("Content-Length", -1))
            downloaded = 0
            block_size = 8192

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                percent = downloaded * 100 // file_size if file_size > 0 else 0
                print(f"\r[DL] {percent:3d}% - {dest_path.name}", end="", flush=True)
        print()
        return True
    except Exception as e:
        #----------If it's an SSL error, try again with unverified context----------
        if isinstance(e, ssl.SSLError) or 'CERTIFICATE_VERIFY_FAILED' in str(e):
            cprint("[WARN] SSL certificate verification failed. Retrying insecurely...", Fore.YELLOW)
            try:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(url, context=context) as response, open(dest_path, 'wb') as out_file:
                    file_size = int(response.info().get("Content-Length", -1))
                    downloaded = 0
                    block_size = 8192

                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        percent = downloaded * 100 // file_size if file_size > 0 else 0
                        print(f"\r[DL] {percent:3d}% - {dest_path.name}", end="", flush=True)
                print()
                cprint("[WARN] Downloaded insecurely. Please fix your Python certificates!", Fore.YELLOW)
                return True
            except Exception as e2:
                cprint(f"[ERROR] Download failed (even insecurely): {e2}", Fore.RED)
                if fallback_url:
                    cprint(f"[INFO] Try downloading manually from: {fallback_url}", Fore.YELLOW)
                return False
        cprint(f"[ERROR] Download failed: {e}", Fore.RED)
        if fallback_url:
            cprint(f"[INFO] Try downloading manually from: {fallback_url}", Fore.YELLOW)
        return False


#----------env----------
def verify_env_before_continue():
    try:
        check_required_env_vars()
    except Exception:
        cprint("[WARN] Could not validate required environment variables", Fore.YELLOW)


#----------banner----------
def print_banner():
    print()
    cprint(r"       ██████╗██╗     ██╗██████╗     ██████╗ ████████╗", Fore.CYAN)
    cprint(r"      ██╔════╝██║     ██║██╔══██╗    ██╔══██╗╚══██╔══╝", Fore.CYAN)
    cprint(r"      ██║     ██║     ██║██████╔╝    ██║  ██║   ██║   ", Fore.CYAN)
    cprint(r"      ██║     ██║     ██║██╔══██╗    ██║  ██║   ██║   ", Fore.CYAN)
    cprint(r"       ██████╗███████╗██║██████╔╝    ██████╔╝   ██║   ", Fore.CYAN)
    cprint(r"       ╚═════╝╚══════╝╚═╝╚═════╝     ╚═════╝    ╚═╝   ", Fore.CYAN)
    cprint(r"             CommonLibSSE-NG Developers Toolkit ", Fore.GREEN)

#----------version----------
def print_version_status():
    global _version_checked, _version_message

    if not _version_checked:
        print()
        msg = f"           Supertron 2025 © -- v{VERSION}"
        color = Fore.LIGHTBLUE_EX

        if not requests:
            _version_message = f"{msg} (requests module missing)"
            _version_checked = True
            cprint(_version_message, Fore.RED)
            return

        try:
            res = requests.get(NEXUS_URL, timeout=5)
            if "<div class=\"stat\">" in res.text:
                match = re.search(r'<div class="stat">([\d\.]+)</div>', res.text)
                if match:
                    online = match.group(1)
                    if online != VERSION:
                        msg += f" (update available: v{online})"
                        color = Fore.RED
                    else:
                        msg += " (up to date)"
                else:
                    msg += " (version check failed)"
                    color = Fore.RED
            else:
                msg += " (parse failed)"
                color = Fore.RED
        except:
            msg += " (network error)"
            color = Fore.RED

        _version_message = msg
        _version_checked = True
        cprint(_version_message, color)
    else:
        cprint(_version_message, Fore.CYAN)



#----------last backup----------
def print_last_backup_info():
    # Check both possible locations for last_backup_path.txt
    candidates = []
    localappdata = os.getenv("LOCALAPPDATA")
    if localappdata:
        candidates.append(Path(localappdata) / "ClibDT" / "last_backup_path.txt")
    candidates.append(Path.home() / ".local" / "share" / "ClibDT" / "last_backup_path.txt")

    best_timestamp = None
    best_path = None
    for path in candidates:
        if path.exists():
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
                if len(lines) < 2 or not lines[1].strip():
                    continue
                timestamp = lines[1].strip()
                # Try parsing as ISO format
                try:
                    dt = datetime.fromisoformat(timestamp)
                except Exception:
                    continue
                if not best_timestamp or dt > best_timestamp:
                    best_timestamp = dt
                    best_path = path
            except Exception:
                continue
    if best_timestamp:
        # Convert to local time for display
        if best_timestamp.tzinfo is not None:
            local_time = best_timestamp.astimezone()
            now = datetime.now(local_time.tzinfo)
        else:
            local_time = best_timestamp
            now = datetime.now()
        days_old = (now - best_timestamp).days
        if days_old < 7:
            color = Fore.GREEN
        elif days_old < 30:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        # Always use 24-hour clock
        cprint(f"Last Backup: {local_time.strftime('%Y-%m-%d %H:%M:%S')}", color)
    else:
        cprint("Last Backup: Never", Fore.RED)



#----------logger----------

import tempfile, shutil
import io
def atomic_write(path, data, mode='w', encoding='utf-8'):
    dirpath = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(mode=mode, encoding=encoding, dir=dirpath, delete=False) as tf:
        tf.write(data)
        tempname = tf.name
    shutil.move(tempname, path)

class FullTeeLogger(io.TextIOBase):
    def __init__(self, log_path):
        self.terminal_out = sys.stdout
        self.terminal_err = sys.stderr
        try:
            self.logfile = open(log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            self.logfile = None
        self.original_input = __builtins__.input  # Always use the real input
        self._encoding = getattr(self.terminal_out, 'encoding', 'utf-8')

    @property
    def encoding(self):
        return self._encoding

    def write(self, message):
        self.terminal_out.write(message)
        if self.logfile:
            try:
                self.logfile.write(message)
            except Exception:
                pass
        return len(message)

    def flush(self):
        self.terminal_out.flush()
        if self.logfile:
            try:
                self.logfile.flush()
            except Exception:
                pass

    def isatty(self):
        return True

    def writable(self):
        return True

    def readable(self):
        return False

    def seekable(self):
        return False

    def fileno(self):
        return self.terminal_out.fileno() if hasattr(self.terminal_out, 'fileno') else 1

    def input(self, prompt=""):
        self.write(prompt)
        user_input = self.original_input(prompt)
        #----------Do not log user keystrokes----------
        return user_input

    def close(self):
        if self.logfile:
            try:
                self.logfile.write("\n--- LOG CLOSED ---\n")
                self.logfile.close()
            except Exception:
                pass


def setup_full_logger():
    if getattr(sys, 'frozen', False):
        log_path = Path(sys.executable).resolve().parent / "ClibDT.log"
    else:
        log_path = Path(__file__).resolve().parent / "ClibDT.log"

    logger = FullTeeLogger(log_path)
    #----------Do NOT wrap logger with AnsiToWin32: it is not a true file object and will cause linter/runtime errors.----------
    sys.stdout = logger
    sys.stderr = logger
    atexit.register(logger.close)
    print(f"[LOGGING] Output is being saved to: {log_path}")


def safe_input(prompt):
    if NO_PAUSE:
        print(prompt)
        return ''
    return input(prompt)


def safe_cprint(msg, color=Fore.RESET):
    try:
        print(color + msg + Style.RESET_ALL)
    except Exception:
        print(msg)

cprint = safe_cprint

def get_menu_choice(valid_choices):
    while True:
        choice = safe_input("\nChoose an option: ").strip().lower()
        if choice in valid_choices:
            return choice
        cprint("Invalid selection. Try again.", Fore.RED)
        if NO_PAUSE:
            return None

def safe_chdir(path):
    try:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            cprint(f"[ERROR] Path does not exist or is not a directory: {path}", Fore.RED)
            return False
        os.chdir(p)
        return True
    except Exception as e:
        cprint(f"[ERROR] Failed to change directory: {e}", Fore.RED)
        return False

if __name__ == "__main__":

    try:
        setup_full_logger()
    except Exception as logerr:
        import traceback
        print("[FATAL] Failed to set up logger:", file=sys.__stderr__)
        traceback.print_exc(file=sys.__stderr__)
        input("Press Enter to exit...")
        raise SystemExit(1)

    try:
        if os.name == "nt":
            import shutil
            cols, lines = shutil.get_terminal_size(fallback=(120, 30))
            new_lines = int(lines * 1.2)
            os.system(f"mode con: lines={new_lines} cols={cols}")
    except Exception:
        pass
    def main_menu():
        valid_choices = {"p","1","2","3","4","5","6","7","8","9","10","11","0","m"}
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            verify_env_before_continue()
            print_banner()
            print_version_status()

            # ---------------- MENU UI ------------------
            print("\n1. Set Environment Variables (required)")
            print("2. Install VS (or Build Tools), Git, Xmake, GitHub Desktop")
            print("3. Create a New Project")
            print("4. Update Project Dependencies")
            print("5. Build Project (Debug or Release)")
            print("6. Regenerate xmake.lua")
            print("7. Git Stage & Commit Project")
            print("8. Detach Git (Remove history)")
            print("9. Smart Backup Dev Folder")
            print("10. Refresh Existing Project")
            print("11. Clear Environment Variables")
            print("0. Exit")
            print()
            print("Enter P to open Nexus Mods page\n")
            cprint("Enter M to return to this menu", Fore.LIGHTBLACK_EX)
            print_last_backup_info()

            def pick_project_folder():
                root = os.getenv("XSE_CLIBDT_DEVROOT")
                if not root:
                    cprint("[ERROR] Dev root not set. Run option 1 first.", Fore.RED)
                    input("Press Enter to return...")
                    return None
                root_path = Path(root)
                scan_base = root_path / "projects" if (root_path / "projects").exists() else root_path
                if not scan_base.exists():
                    cprint(f"[ERROR] Path does not exist: {scan_base}", Fore.RED)
                    input("Press Enter to return...")
                    return None
                projects = [subdir for subdir in scan_base.iterdir() if subdir.is_dir()]
                if not projects:
                    cprint("No project folders found. Create a project first.", Fore.RED)
                    input("Press Enter to return...")
                    return None
                print()
                print("    Select a Project Folder", Fore.LIGHTBLUE_EX)
                print()
                for i, p in enumerate(projects, start=1):
                    print(f"{i}. {p.relative_to(scan_base)}")
                print("M. Return to main menu\n")
                userInput = input("Enter project number: ").strip()
                if userInput.lower() == "m":
                    return None
                if not userInput.isdigit():
                    return None
                idx = int(userInput)
                if not (1 <= idx <= len(projects)):
                    return None
                return str(projects[idx - 1])

            choice = get_menu_choice(valid_choices)
            if not choice:
                break

            # ---------------- ROUTING ------------------
            if choice == "p":
                webbrowser.open(NEXUS_URL)

            elif choice == "1":
                try:
                    from modules.set_environment_variables import run_set_env_vars
                    run_set_env_vars()
                except Exception as e:
                    cprint(f"[ERROR] Failed to run environment setup: {e}", Fore.RED)
                    input("Press Enter to continue...")


            elif choice == "2":
                try:
                    from modules.install_vstudio_xmake_git import run_install_tools
                    run_install_tools()
                except Exception as e:
                    cprint(f"[ERROR] Failed to run install tools script: {e}", Fore.RED)
                    input("Press Enter to continue...")


            elif choice == "3":
                try:
                    from modules.create_project import run_create_project
                    run_create_project()
                except Exception as e:
                    cprint(f"[ERROR] Failed to create project: {e}", Fore.RED)
                    input("Press Enter to continue...")


            elif choice == "4":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    try:
                        from modules.update_project_deps import update_project_deps
                        update_project_deps()
                    except Exception as e:
                        cprint(f"[ERROR] Failed to update project dependencies: {e}", Fore.RED)
                        input("Press Enter to continue...")
                else:
                    input("Press Enter to return...")



            elif choice == "5":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    try:
                        from modules.build_project import run_build_project
                        run_build_project()
                    except Exception as e:
                        cprint(f"[ERROR] Failed to build project: {e}", Fore.RED)
                        input("Press Enter to continue...")
                else:
                    input("Press Enter to return...")


            elif choice == "6":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    try:
                        from modules.regenerate_xmakelua import run_regenerate_xmake
                        run_regenerate_xmake()
                    except Exception as e:
                        cprint(f"[ERROR] Failed to run regenerate_xmakelua: {e}", Fore.RED)
                        input("Press Enter to continue...")
                else:
                    input("Press Enter to return...")

            elif choice == "7":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    try:
                        from modules.git_stage_and_commit import run_git_commit
                        run_git_commit()
                    except Exception as e:
                        cprint(f"[ERROR] Failed to run git commit helper: {e}", Fore.RED)
                        input("Press Enter to continue...")
                else:
                    input("Press Enter to return...")

            elif choice == "8":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    run_py_file("modules/detach_remove_git.py")
                else:
                    input("Press Enter to return...")

            elif choice == "9":
                run_py_file("modules/backup_dev_root.py")

            elif choice == "10":
                path = pick_project_folder()
                if path and Path(path).exists():
                    os.chdir(path)
                    run_py_file("modules/refresh_project.py")
                else:
                    input("Press Enter to return...")



            elif choice == "11":
                from modules import delete_env_vars
                delete_env_vars.main()

            elif choice == "0":
                break

            else:
                cprint("Invalid selection. Try again.", Fore.RED)
                input("Press Enter...")

    try:
        main_menu()
    except Exception:
        import traceback
        print("[FATAL] Unhandled exception occurred:")
        traceback.print_exc()
        input("Press Enter to exit...")



