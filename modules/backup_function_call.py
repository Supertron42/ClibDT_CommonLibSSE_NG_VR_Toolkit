import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

#----------Color Print Helper----------
def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

#----------Read Last External Backup Path----------
def read_last_backup_path():
    try:
        localappdata = os.getenv("LOCALAPPDATA")
        if not localappdata:
            return None
        path = Path(localappdata) / "ClibDT" / "last_backup_path.txt"
        if not path.exists():
            return None
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            return Path(lines[0].strip())
    except Exception:
        pass
    return None

#----------Create Project Backup ZIP----------
def backup_project_snapshot():
    project_root = Path.cwd()
    src_dir = project_root / "src"
    xmake_file = project_root / "xmake.lua"
    backup_dir = project_root / "backups"
    backup_dir.mkdir(exist_ok=True)

    if not src_dir.exists() or not xmake_file.exists():
        cprint("[SKIP] Cannot create project snapshot: missing src/ or xmake.lua", Fore.YELLOW)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = backup_dir / backup_name

    cprint(f"[INFO] Creating local backup: {backup_path.name}", Fore.CYAN)
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in src_dir.rglob("*"):
            if path.is_file():
                arcname = path.relative_to(project_root)
                zipf.write(path, arcname)
        zipf.write(xmake_file, xmake_file.relative_to(project_root))

    dest_root = read_last_backup_path()
    if dest_root and dest_root.drive and Path(dest_root.drive).exists():
        try:
            dest_project = dest_root / project_root.name / "_backups"
            dest_project.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, dest_project / backup_name)
            cprint("[OK] Snapshot also copied to external Dev backup location.", Fore.GREEN)
        except Exception as e:
            cprint(f"[WARNING] Error backing up externally: {e}", Fore.YELLOW)
    else:
        cprint("[INFO] External backup path unavailable or drive missing. Skipping copy.", Fore.LIGHTBLACK_EX)

#----------Entry Point----------
def main():
    backup_project_snapshot()

if __name__ == "__main__":
    main()
