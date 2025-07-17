import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone
from colorama import Fore, Style, init

try:
    from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

init(autoreset=True)

localappdata = os.getenv("LOCALAPPDATA")
if not localappdata:
    APPDATA_DIR = Path.home() / ".local" / "share" / "ClibDT"
else:
    APPDATA_DIR = Path(localappdata) / "ClibDT"
LAST_BACKUP_PATH_FILE = APPDATA_DIR / "last_backup_path.txt"

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_input(msg, default=None):
    val = input(f"{msg} ").strip()
    if val.lower() == "m":
        return "M"
    return val or default

def should_copy_by_mtime(src: Path, dst: Path) -> bool:
    return not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime

def collect_files_to_copy(dev_root: Path, backup_root: Path, smart: bool) -> list[tuple[Path, Path]]:
    tasks = []
    for dirpath, _, filenames in os.walk(dev_root):
        for name in filenames:
            src = Path(dirpath) / name
            rel_path = src.relative_to(dev_root)
            dst = backup_root / rel_path
            if not smart or should_copy_by_mtime(src, dst):
                tasks.append((src, dst))
    return tasks

def run_backup_dev_root():
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set.", Fore.RED)
        return

    dev_root = Path(dev_root).resolve()
    if not dev_root.exists():
        cprint(f"[ERROR] Dev root does not exist: {dev_root}", Fore.RED)
        return

    dev_root_name = dev_root.name
    cprint("=== SKSE Dev Backup Utility ===", Fore.CYAN)
    cprint(f"[INFO] Source folder: {dev_root}", Fore.CYAN)

    last_path = None
    if LAST_BACKUP_PATH_FILE.exists():
        try:
            last_path = LAST_BACKUP_PATH_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
        except Exception:
            pass

    dest_base = prompt_input(f"Enter destination base folder [{last_path or 'required'}]:", last_path)
    if dest_base == "M":
        cprint("[CANCELLED] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    if not dest_base:
        cprint("[CANCELLED] No destination provided.", Fore.YELLOW)
        return

    dest_base = Path(dest_base).expanduser().resolve()
    backup_root = dest_base / dev_root_name
    backup_root.mkdir(parents=True, exist_ok=True)

    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with open(LAST_BACKUP_PATH_FILE, "w", encoding="utf-8") as f:
        f.write(f"{dest_base}\n{timestamp}")

    print()
    mode = prompt_input("Backup mode: Smart (S - only new/diff) or Full (F)? [Default: S]:", "S").upper()
    if mode == "M":
        cprint("[CANCELLED] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    smart = mode != "F"

    cprint("[INFO] Scanning files...", Fore.LIGHTBLACK_EX)
    tasks = collect_files_to_copy(dev_root, backup_root, smart)

    if not tasks:
        cprint("[OK] Nothing to back up. Everything is up to date.", Fore.GREEN)
        input("\nPress Enter to return...")
        return

    print()
    cprint(f"[INFO] Press Ctrl+C to cancel. Total files to copy: {len(tasks)}", Fore.LIGHTBLACK_EX)
    cprint(f"Starting backup ({'Smart' if smart else 'Full'})...\n", Fore.CYAN)

    try:
        if RICH_AVAILABLE:
            console = Console()
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Backing up", total=len(tasks))
                for src, dst in tasks:
                    try:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        time.sleep(0.001)
                    except PermissionError:
                        cprint(f"[SKIPPED] File in use: {src}", Fore.YELLOW)
                    except Exception as e:
                        cprint(f"[ERROR] Failed to copy {src} → {dst}: {e}", Fore.RED)
                    progress.update(task, advance=1)
        elif tqdm:
            iterator = tqdm(tasks, desc="Backing up", unit="file")
            for src, dst in iterator:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    time.sleep(0.001)
                except PermissionError:
                    cprint(f"[SKIPPED] File in use: {src}", Fore.YELLOW)
                except Exception as e:
                    cprint(f"[ERROR] Failed to copy {src} → {dst}: {e}", Fore.RED)
        else:
            for src, dst in tasks:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    time.sleep(0.001)
                except PermissionError:
                    cprint(f"[SKIPPED] File in use: {src}", Fore.YELLOW)
                except Exception as e:
                    cprint(f"[ERROR] Failed to copy {src} → {dst}: {e}", Fore.RED)

    except KeyboardInterrupt:
        cprint("\n[ABORTED] Backup canceled by user.", Fore.RED)
        return

    print()
    cprint(f"[COMPLETE] Backup finished successfully: {backup_root}", Fore.GREEN)
    input("\nPress Enter to return...")

if __name__ == "__main__":
    run_backup_dev_root()
