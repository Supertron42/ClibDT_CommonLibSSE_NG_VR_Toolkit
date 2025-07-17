import os
import subprocess
import sys
import tempfile
import textwrap
import shutil
from typing import Optional
from pathlib import Path
from colorama import Fore, Style


def restart_clibdt():
    exe = sys.executable
    args = sys.argv
    subprocess.Popen([exe] + args, creationflags=subprocess.CREATE_NEW_CONSOLE)
    os._exit(0)

def download_with_progress(url: str, dest_path: Path, fallback_url: Optional[str] = None) -> bool:
    import urllib.request

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
        cprint(f"[ERROR] Download failed: {e}", Fore.RED)
        if fallback_url:
            cprint(f"[INFO] Try downloading manually from: {fallback_url}", Fore.YELLOW)
        return False


def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def show_current_env_summary():
    cprint("Current Environment Settings:", Fore.MAGENTA)
    vars = [
        "XSE_CLIBDT_DEVROOT",
        "XSE_TES5_GAME_PATH",
        "XSE_TES5_MODS_PATH"
    ]
    for v in vars:
        val = os.getenv(v)
        if val:
            cprint(f"  {v} = {val}", Fore.GREEN)
        else:
            cprint(f"  {v} = (NOT SET)", Fore.RED)
    print()

def setx(var, value):
    subprocess.call(["setx", var, value], shell=True, stdout=subprocess.DEVNULL)
    try:
        updated = subprocess.check_output(
            ["reg", "query", "HKCU\\Environment", "/v", var],
            text=True
        )
        for line in updated.splitlines():
            if var in line:
                os.environ[var] = line.split()[-1]
                break
    except Exception as e:
        cprint(f"[WARN] Could not patch env var '{var}' into current session: {e}", Fore.YELLOW)

def get_7zip_exe(dev_root: Path) -> Optional[Path]:
    #----------1. Check in dev_root/tools/7zip----------
    local_path = dev_root / "tools" / "7zip" / "7z.exe"
    if local_path.exists():
        return local_path

    #----------2. Check in PATH----------
    from shutil import which
    found = which("7z")
    if found:
        return Path(found)

    #----------3. Check common install paths----------
    common_paths = [
        Path("C:/Program Files/7-Zip/7z.exe"),
        Path("C:/Program Files (x86)/7-Zip/7z.exe")
    ]
    for path in common_paths:
        if path.exists():
            return path

    return None


    #----------7zip----------
    url = "https://www.7-zip.org/a/7z2500-x64.msi"
    msi_name = "7z2500-x64.msi"
    dl_path = dev_root / "downloads" / msi_name

    cprint("[INFO] 7-Zip not found. Downloading MSI installer...", Fore.YELLOW)
    if not download_with_progress(url, dl_path, url):
        cprint("[ERROR] Failed to download 7-Zip installer.", Fore.RED)
        return None

    try:
        cprint("[INFO] Running silent MSI install...", Fore.CYAN)
        subprocess.run(["msiexec", "/i", str(dl_path), "/quiet", f"INSTALLDIR={sevenzip_dir}"], check=True)
        if sevenzip_exe.exists():
            cprint(f"[OK] 7-Zip installed to: {sevenzip_dir}", Fore.GREEN)
            return sevenzip_exe
    except Exception as e:
        cprint(f"[ERROR] MSI install failed: {e}", Fore.RED)

    return None
    

def run_set_env_vars():
    print()
    cprint("[INFO] Enter M to return to main menu.", Fore.LIGHTBLACK_EX)
    print()

    show_current_env_summary()

    # === REQUIRED: DEV ROOT FOLDER ===
    dev_root = None
    current_dev = os.getenv("XSE_CLIBDT_DEVROOT")
    if current_dev:
        cprint(f"[INFO] Dev root is already set to: {current_dev}", Fore.LIGHTBLACK_EX)
        answer = input("Do you want to keep it? (Y/N): ").strip().lower()
        if answer == "m":
            return
        if answer == "y":
            dev_root = Path(current_dev).resolve()

    while not dev_root:
        default_dev = r"C:\ClibDT"
        cprint("Enter where you want to set or create your ClibDT dev root.", Fore.CYAN)
        cprint(f"This path will contain all your tools and projects.\nDefault = {default_dev}", Fore.LIGHTBLACK_EX)
        user_input = input(f"Press Enter to use default, or enter custom path: ").strip() or default_dev
        if user_input.lower() == "m":
            return
        dev_root = Path(user_input).resolve()
        dev_root.mkdir(parents=True, exist_ok=True)
        setx("XSE_CLIBDT_DEVROOT", str(dev_root))
        cprint(f"[OK] XSE_CLIBDT_DEVROOT set to: {dev_root}", Fore.GREEN)

    for sub in ["tools", "projects", "output", "downloads"]:
        folder = dev_root / sub
        if not folder.exists():
            folder.mkdir(parents=True)
            cprint(f"[OK] Created folder: {folder}", Fore.LIGHTGREEN_EX)
    print()

    # --- Copy bundled 7zip if not present ---
    bundled_7zip = (Path(__file__).parent.parent / "tools" / "7zip").resolve()
    target_7zip = dev_root / "tools" / "7zip"
    if bundled_7zip.exists() and not target_7zip.exists():
        import shutil
        shutil.copytree(bundled_7zip, target_7zip)
        cprint(f"[OK] 7-Zip installed to: {target_7zip}", Fore.GREEN)

    # === REQUIRED: GAME FOLDER PATH (skse_loader.exe) ===
    current_game = os.getenv("XSE_TES5_GAME_PATH")
    if current_game:
        cprint(f"[INFO] Game path is already set to: {current_game}", Fore.LIGHTBLACK_EX)
        answer = input("Do you want to keep it? (Y to keep / N to change): ").strip().lower()
        if answer == "m":
            return
        if answer == "y":
            game_path = Path(current_game).resolve()
        else:
            game_path = None
    else:
        game_path = None
        print()
    while not game_path:
        cprint("Enter the full path to your Skyrim game folder (where skse64_loader.exe is):", Fore.CYAN)
        cprint("Any path you enter will download SKSE to that folder if not detected.", Fore.LIGHTBLACK_EX)
        suggested_path = dev_root / "tools" / "SKSE"
        cprint(f"Default = {suggested_path}", Fore.LIGHTBLACK_EX)
        user_input = input("Press Enter to use default, or enter custom path: ").strip()
        if user_input.lower() == "m":
            return
        game_path = Path(user_input or suggested_path).resolve()

        skse_loader = None
        for fname in ["skse_loader.exe", "skse64_loader.exe"]:
            candidate = game_path / fname
            if candidate.exists():
                skse_loader = candidate
                break

        if skse_loader:
            setx("XSE_TES5_GAME_PATH", str(game_path))
            cprint(f"[OK] XSE_TES5_GAME_PATH set to: {game_path}", Fore.GREEN)
        else:
            cprint("[ERROR] skse_loader.exe or skse64_loader.exe not found in the given path.", Fore.RED)
            cprint("Would you like to download SKSE to that folder?", Fore.YELLOW)
            dl = input("Download SKSE? (Y/N): ").strip().lower()
            if dl != "y":
                game_path = None
                continue

            print()
            cprint("Which version of Skyrim are you mostly targeting?", Fore.CYAN)
            cprint("[Note] CommonLibSSE-NG (VR) can support all versions.\n", Fore.LIGHTBLACK_EX)
            print("1. Anniversary Edition: https://skse.silverlock.org/beta/skse64_2_02_06.7z")
            print("2. Anniversary GOG   : https://skse.silverlock.org/beta/skse64_2_02_06_gog.7z")
            print("3. Special Edition   : https://skse.silverlock.org/beta/skse64_2_00_20.7z")
            print("4. Skyrim VR         : https://skse.silverlock.org/beta/sksevr_2_00_12.7z")
            print()

            skse_links = {
                "1": ("skse64_2_02_06.7z", "https://skse.silverlock.org/beta/skse64_2_02_06.7z"),
                "2": ("skse64_2_02_06_gog.7z", "https://skse.silverlock.org/beta/skse64_2_02_06_gog.7z"),
                "3": ("skse64_2_00_20.7z", "https://skse.silverlock.org/beta/skse64_2_00_20.7z"),
                "4": ("sksevr_2_00_12.7z", "https://skse.silverlock.org/beta/sksevr_2_00_12.7z")
            }

            choice = input("Enter option number (1-4): ").strip()
            if choice not in skse_links:
                cprint("[INFO] Invalid option selected. Please try again.", Fore.YELLOW)
                game_path = None
                continue

            filename, url = skse_links[choice]
            skse_archive = game_path / filename
            game_path.mkdir(parents=True, exist_ok=True)

            cprint(f"[INFO] Downloading {filename} to {game_path}", Fore.CYAN)
            if not download_with_progress(url, skse_archive, url):
                cprint("[ERROR] Download failed. Try again or download manually.", Fore.RED)
                game_path = None
                continue

            sevenzip_exe = get_7zip_exe(dev_root)
            if not sevenzip_exe:
                cprint("[ERROR] 7-Zip not found in PATH or known locations. Please install 7-Zip and try again.", Fore.RED)
                game_path = None
                continue

            try:
                tmp_extract_dir = game_path / "_skse_tmp"
                tmp_extract_dir.mkdir(parents=True, exist_ok=True)

                subprocess.run([
                    str(sevenzip_exe), "x", str(skse_archive),
                    f"-o{tmp_extract_dir}", "-y", "-aoa"
                ], check=True)
                cprint("[OK] SKSE archive extracted to temp folder.", Fore.GREEN)

                #----------Find SKSE subfolder----------
                inner_skse_dir = None
                for sub in tmp_extract_dir.iterdir():
                    if sub.is_dir() and (sub / "skse64_loader.exe").exists():
                        inner_skse_dir = sub
                        break
                    elif sub.is_dir() and (sub / "skse").is_dir():
                        inner_skse_dir = sub / "skse"
                        break

                if inner_skse_dir and inner_skse_dir.exists():
                    for item in inner_skse_dir.iterdir():
                        dest = game_path / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)
                    cprint("[OK] SKSE files moved to SKSE or GAME folder.", Fore.GREEN)
                else:
                    cprint("[ERROR] Could not find valid SKSE subfolder in archive.", Fore.RED)
                    game_path = None
                    continue

                #----------Cleanup----------
                shutil.rmtree(tmp_extract_dir)
                skse_archive.unlink(missing_ok=True)

            except Exception as e:
                cprint(f"[ERROR] Extraction failed: {e}", Fore.RED)
                game_path = None
                continue


            #----------Recheck for loader after extraction----------
            skse_loader = None
            for fname in ["skse_loader.exe", "skse64_loader.exe"]:
                found = list(game_path.rglob(fname))
                if found:
                    skse_loader = found[0]
                    game_path = skse_loader.parent  #----------Set game_path to correct folder----------
                    break

            if skse_loader:
                setx("XSE_TES5_GAME_PATH", str(game_path))
                cprint(f"[OK] XSE_TES5_GAME_PATH set to: {game_path}", Fore.GREEN)
            else:
                cprint("[ERROR] skse_loader.exe still not found after extraction.", Fore.RED)
                game_path = None
            print()

    #----------MODS FOLDER PATH----------
    current_mods = os.getenv("XSE_TES5_MODS_PATH")
    if current_mods:
        cprint(f"[INFO] Mods path is already set to: {current_mods}", Fore.LIGHTBLACK_EX)
        answer = input("Do you want to keep it? (Y to keep / N to change): ").strip().lower()
        if answer == "m":
            return
        if answer == "y":
            mods_path = Path(current_mods).resolve()
        else:
            mods_path = None
    else:
        mods_path = None

        if not mods_path:
            default_mods = dev_root / "output"
            cprint("Enter the full path to your Skyrim mods folder (MO2 and Vortex supported):", Fore.CYAN)
            cprint(f"This is where your compiled projects will be installed.\nDefault = {default_mods}", Fore.LIGHTBLACK_EX)
            user_input = input(f"Press Enter to use default, or enter custom path: ").strip()
            if user_input.lower() == "m":
                return
            mods_path = Path(user_input or default_mods).resolve()
            mods_path.mkdir(parents=True, exist_ok=True)
            setx("XSE_TES5_MODS_PATH", str(mods_path))
            cprint(f"[OK] XSE_TES5_MODS_PATH set to: {mods_path}", Fore.GREEN)

    #----------FINAL SUMMARY AND EXIT----------
    print()
    cprint("Required environment variable setup complete!", Fore.MAGENTA)
    show_current_env_summary()

    cprint("You will need to restart ClibDT for all changes to take effect.", Fore.YELLOW)
    answer = input("Restart ClibDT now? (Y/N): ").strip().lower()
    if answer == "y":
        restart_clibdt()
