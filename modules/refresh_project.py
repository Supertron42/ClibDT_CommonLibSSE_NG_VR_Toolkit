import os
import shutil
import subprocess
import sys
from pathlib import Path
from colorama import init, Fore, Style

#----------import----------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ClibDT import cprint
from modules.git_stage_and_commit import run_git_commit
from modules.xmake_gen import generate_xmake_lua

init(autoreset=True)

def delete_folder(folder: Path):
    def onerror(func, path, exc_info):
        import stat
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            cprint(f"[ERROR] Could not delete {path}: {e}", Fore.RED)

    if folder.exists() and folder.is_dir():
        try:
            shutil.rmtree(folder, onerror=onerror)
            cprint(f"[OK] {folder.name}/ deleted.", Fore.GREEN)
        except Exception as e:
            cprint(f"[ERROR] Failed to delete {folder.name}/: {e}", Fore.RED)
    else:
        cprint(f"[INFO] {folder.name}/ not found. Skipping.", Fore.LIGHTBLACK_EX)


def install_clibutil():
    cprint("--- Installing ClibUtil ---", Fore.CYAN)
    temp = Path("_clibutil_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    subprocess.run(["git", "clone", "--depth=1", "https://github.com/powerof3/ClibUtil.git", str(temp)])
    clib_dest = Path("ClibUtil")
    clib_dest.mkdir(parents=True, exist_ok=True)
    subprocess.call(f"xcopy /E /I /Y \"{temp}\\include\\ClibUtil\" \"{clib_dest}\"", shell=True)
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] ClibUtil installed.", Fore.GREEN)


def install_xbyak():
    cprint("--- Installing xbyak ---", Fore.CYAN)
    temp = Path("_xbyak_temp")
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    subprocess.run(["git", "clone", "--depth=1", "https://github.com/herumi/xbyak.git", str(temp)])
    xbyak_dest = Path("xbyak")
    if xbyak_dest.exists():
        shutil.rmtree(xbyak_dest)
    subprocess.call(f"xcopy /E /I /Y \"{temp}\\xbyak\" \"{xbyak_dest}\"", shell=True)
    shutil.rmtree(temp, ignore_errors=True)
    cprint("[OK] xbyak installed.", Fore.GREEN)


def run_refresh(project_path: Path):
    os.chdir(project_path)
    cprint(f"[OK] Working on project: {project_path}", Fore.GREEN)

    #----------CLEAN----------
    delete_folder(project_path / "build")
    delete_folder(project_path / ".xmake")

    #----------INSTALL DEPS----------
    install_clibutil()
    install_xbyak()

    #----------GIT STAGE/COMMIT----------
    run_git_commit()

    #----------REGENERATE xmake.lua----------
    cprint("--- Regenerating xmake.lua ---", Fore.CYAN)
    name = project_path.name
    version = "1.0.0"
    author = "Unknown"
    desc = "No description provided."
    try:
        generate_xmake_lua(project_path, name, version, author, desc)
        cprint(f"[OK] xmake.lua regenerated at {project_path / 'xmake.lua'}", Fore.GREEN)
    except Exception as e:
        cprint(f"[ERROR] Failed to regenerate xmake.lua: {e}", Fore.RED)

    print()
    input("All done! Press Enter to return...")

#----------main----------
def main():
    print()
    cprint("[REFRESH PROJECT] This will clean, update, and reinitialize your project.", Fore.CYAN)
    cprint("Enter M to return to the main menu.", Fore.LIGHTBLACK_EX)
    print()
    project_path = Path.cwd()
    confirm = input(f"Refresh project at {project_path}? (Y/N): ").strip().lower()
    if confirm == "m":
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return
    if confirm != "y":
        cprint("[INFO] Project refresh cancelled.", Fore.LIGHTBLACK_EX)
        return
    run_refresh(project_path)

main()
