# modules/install_vstudio_xmake_git.py
import os
import requests
import webbrowser
import subprocess
import shutil
from pathlib import Path
from colorama import init, Fore, Style
import stat
import time
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.console import Console

try:
    from tqdm import tqdm
except ImportError:
    print("[ERROR] Missing module 'tqdm'. Run: pip install tqdm")
    exit(1)

init(autoreset=True)


#----------utility helpers----------
def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_yesno(question):
    while True:
        val = input(f"{question} ").strip().lower()
        if val in {"y", "n", "m"}:
            return val
        cprint("Invalid input. Enter Y, N, or M.", Fore.LIGHTYELLOW_EX)

def download_with_progress(url, dest_file, fallback=None):
    try:
        response = requests.get(url, stream=True, timeout=10)
        total = int(response.headers.get('Content-Length', 0))
        console = Console()
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"📥 {dest_file.name}", total=total)
            with open(dest_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        console.print(f"[green]Download complete! Saved to {dest_file}[/green]")
        return dest_file.exists()
    except Exception as e:
        cprint(f"❌ {dest_file.name} download failed: {e}", Fore.RED)
        if fallback:
            cprint(f"   🔗 Download manually: {fallback}", Fore.YELLOW)
        return False


def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to a read-only file, it attempts to make it writable and retries.
    """
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def robust_rmtree(path, onerror=None, retries=5, delay=3):
    if not path.exists():
        return  # Don't try to delete if it doesn't exist
    
    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=onerror)
            return
        except Exception as e:
            if attempt < retries - 1:
                cprint(f"[WARN] Could not delete {path} (attempt {attempt+1}/{retries}): {e}", Fore.YELLOW)
                cprint(f"[INFO] Waiting {delay} seconds for processes to release lock...", Fore.LIGHTBLACK_EX)
                time.sleep(delay)
            else:
                cprint(f"[ERROR] Failed to delete {path} after {retries} retries. You may need to restart your computer.", Fore.RED)
                raise


#----------main----------
def run_install_tools():
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set. Run the environment setup first.", Fore.RED)
        return

    # Remove self-replication logic (do not copy ClibDT.exe to dev root)
    # (No code here)

    dev_root = Path(dev_root).resolve()
    dl_dir = dev_root / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)

    cprint("[INFO] Installers will be downloaded to:", Fore.CYAN)
    print(f"  {dl_dir}\n")

    failed = False

#----------GIT INSTALL----------
    GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.50.1.windows.1/PortableGit-2.50.1-64-bit.7z.exe"
    GIT_FALLBACK = "https://git-scm.com/download/win"
    GIT_FILE = dl_dir / "PortableGit-2.50.1-64-bit.7z.exe"
    GIT_LABEL = "Git x64 Portable"
    git_install_path = dev_root / "tools" / "Git"
    git_install_path.mkdir(parents=True, exist_ok=True)

    sevenzip_exe = dev_root / "tools" / "7zip" / "7za.exe"
    if not sevenzip_exe.exists():
        cprint(f"[ERROR] 7-Zip not found at: {sevenzip_exe}", Fore.RED)
        return

    answer = prompt_yesno("Install Git now? (Y/N): ")
    if answer == "m":
        return
    if answer == "n":
        cprint("[INFO] Skipping Git installation.", Fore.LIGHTBLACK_EX)
        print()
    elif answer == "y":
        cprint(f"Downloading: {GIT_LABEL}", Fore.YELLOW)
        if download_with_progress(GIT_URL, GIT_FILE, GIT_FALLBACK):
            cprint("[OK] Git archive downloaded.", Fore.GREEN)
            try:
                cprint("[INFO] Extracting Git archive to tools/Git...", Fore.CYAN)
                subprocess.run([
                    str(sevenzip_exe), "x", str(GIT_FILE),
                    f"-o{git_install_path}", "-y", "-aoa"
                ], check=True)

                git_exe = git_install_path / "cmd" / "git.exe"
                if git_exe.exists():
                    subprocess.run(["setx", "XSE_GIT_ROOT", str(git_install_path)], shell=True, check=True)
                    os.environ["XSE_GIT_ROOT"] = str(git_install_path)  # Patch into session
                    cprint(f"[OK] Git installed to: {git_install_path}", Fore.GREEN)
                    cprint(f"[OK] XSE_GIT_ROOT set to: {git_install_path}", Fore.GREEN)
                else:
                    cprint("[ERROR] git.exe not found after extraction.", Fore.RED)
            except subprocess.CalledProcessError as e:
                cprint(f"[ERROR] Extraction failed: {e}", Fore.RED)
        else:
            cprint("[ERROR] Git download failed.", Fore.RED)

    print()


#----------VISUAL STUDIO----------
    answer = prompt_yesno("Install Visual Studio or Build Tools? (Y/N): ")
    if answer == "m":
        return
    if answer == "n":
        cprint("[INFO] Skipping Visual Studio installation.", Fore.LIGHTBLACK_EX)
        print()
    else:
        cprint("Install full VS Community 2022 or just Build Tools? (Choose one)", Fore.CYAN)
        cprint("[INFO] Option 1: 'Full' installs the Visual Studio IDE with code editor, debugger, and other tools.", Fore.LIGHTBLACK_EX)
        print("Full Visual Studio = 1\n")
        cprint("[INFO] Option 2: 'Build Tools' is a minimal setup for compiling only - use this if you know what you're doing.", Fore.LIGHTBLACK_EX)
        print("Build Tools        = 2\n")

        vs_choice = input("Your choice (1 or 2): ").strip().lower()
        if vs_choice == "m":
            return

        if vs_choice == "1":
            cprint("[INFO] Visual Studio must be downloaded and installed manually from the official site.", Fore.LIGHTBLACK_EX)
            answer = prompt_yesno("Open Visual Studio download page now? (Y/N): ")
            if answer.lower() == "m":
                return
            if answer.lower() == "y":
                webbrowser.open("https://visualstudio.microsoft.com/vs/community/")
                cprint("[INFO] Opened Visual Studio download page in browser.", Fore.LIGHTBLACK_EX)

        elif vs_choice == "2":
            buildtools_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
            buildtools_fallback = "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
            buildtools_exe = dl_dir / "vs_BuildTools.exe"

            # Ensure we can write to the file: delete if it exists
            if buildtools_exe.exists():
                try:
                    buildtools_exe.unlink()
                except Exception as e:
                    cprint(f"[ERROR] Could not remove existing {buildtools_exe}: {e}", Fore.RED)
                    cprint("[HINT] Make sure the file is not open in another program and you have write permissions.", Fore.YELLOW)
                    return

            cprint(f"Downloading Build Tools to = {buildtools_exe}", Fore.YELLOW)
            if download_with_progress(buildtools_url, buildtools_exe, buildtools_fallback):
                print()
                install_dir = dev_root / "tools" / "BuildTools"
                
                cprint("[INFO] Launching VS Build Tools installer (GUI/manual mode)...", Fore.CYAN)
                cprint(f"Make sure to install in {dev_root / 'tools' / 'BuildTools'} if you want to contain it in your dev root", Fore.YELLOW)
                cprint(f"Make sure to install in {dev_root / 'tools' / 'BuildTools'} if you want to contain it in your dev root", Fore.YELLOW)
                cprint(f"Make sure to install in {dev_root / 'tools' / 'BuildTools'} if you want to contain it in your dev root", Fore.YELLOW)
                cprint("After installation click 'More ▼' and import VS Build Tools file from this link", Fore.LIGHTBLACK_EX)
                cprint("After installation click 'More ▼' and import VS Build Tools file from this link", Fore.LIGHTBLACK_EX)
                cprint("After installation click 'More ▼' and import VS Build Tools file from this link", Fore.LIGHTBLACK_EX)
                print("     🔗 Nexus Files: https://www.nexusmods.com/skyrimspecialedition/mods/154240")

                try:
                    subprocess.call(str(buildtools_exe))
                except Exception as e:
                    cprint(f"[ERROR] Build Tools launch failed: {e}", Fore.RED)
                    return

                # Loop until valid cl.exe is found
                def find_cl_in_root(install_root):
                    msvc_root = install_root / "VC" / "Tools" / "MSVC"
                    if not msvc_root.exists():
                        return None
                    versions = [d for d in msvc_root.iterdir() if d.is_dir()]
                    if not versions:
                        return None
                    versions.sort(key=lambda d: tuple(int(x) for x in d.name.split(".")), reverse=True)
                    for ver_dir in versions:
                        cl_path = ver_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
                        if cl_path.exists():
                            return cl_path
                    return None

                while True:
                    print()
                    cprint("[MANUAL] Paste the full path to where you installed Build Tools.", Fore.CYAN)
                    cprint(f"Recommended path (set it during installation): {install_dir.resolve()}", Fore.LIGHTBLACK_EX)
                    user_path = input("Where you installed it: ").strip().strip('"')
                    install_root = Path(user_path)
                    cl_path = find_cl_in_root(install_root)

                    if cl_path:
                        subprocess.call(["setx", "XSE_MSVCTOOLS_ROOT", str(install_root)], shell=True)
                        cprint(f"[OK] XSE_MSVCTOOLS_ROOT set to: {install_root}", Fore.GREEN)
                        cprint(f"[OK] Found cl.exe at: {cl_path}", Fore.GREEN)
                        break
                    else:
                        cprint("[ERROR] Could not find cl.exe in that folder.", Fore.RED)
                        cprint("Please ensure you installed all required packages and try again.", Fore.YELLOW)
            else:
                cprint("[ERROR] Invalid choice. Please enter 1 or 2.", Fore.RED)
                return

    

    #----------XMAKE----------
    XMAKE_URL = "https://github.com/xmake-io/xmake/releases/download/v3.0.0/xmake-dev.win64.exe"
    XMAKE_FALLBACK = "https://github.com/xmake-io/xmake/releases"
    XMAKE_FILE = dl_dir / "xmake-dev.win64.exe"
    XMAKE_LABEL = "Install Xmake Dev"

    answer = prompt_yesno(f"Download {XMAKE_LABEL}? (Y/N): ").lower()
    if answer == "m":
        return
    if answer == "n":
        cprint("[INFO] Skipping Xmake installation.", Fore.LIGHTBLACK_EX)
        print()
    elif answer == "y":
        cprint(f"Downloading: {XMAKE_LABEL}", Fore.YELLOW)
        if download_with_progress(XMAKE_URL, XMAKE_FILE, XMAKE_FALLBACK):
            try:
                os.startfile(XMAKE_FILE)
                cprint("[OK] Xmake installer launched. Complete the install manually.", Fore.GREEN)

                # Ask where it was installed
                while True:
                    print()
                    cprint("[MANUAL] Paste the path where Xmake was installed.", Fore.CYAN)
                    print(f"Suggested folder: {dev_root / 'tools' / 'Xmake'}")
                    user_path = input("Enter install path: ").strip().strip('"')
                    xmake_path = Path(user_path) / "xmake.exe"

                    if xmake_path.exists():
                        subprocess.call(["setx", "XSE_XMAKE_ROOT", str(Path(user_path))], shell=True)
                        cprint(f"[OK] XSE_XMAKE_ROOT set to: {user_path}", Fore.GREEN)
                        break
                    else:
                        cprint("[ERROR] xmake.exe not found in that folder. Try again.", Fore.RED)

            except Exception as e:
                cprint(f"[ERROR] Could not launch Xmake installer: {e}", Fore.RED)
        else:
            failed = True




#----------GITHUB DESKTOP----------
    GHD_URL = "https://central.github.com/deployments/desktop/desktop/latest/win32"
    GHD_FALLBACK = "https://desktop.github.com/download/"
    GHD_FILE = dl_dir / "GitHubDesktopSetup.exe"
    GHD_LABEL = "GitHub Desktop Installer"

    answer = prompt_yesno(f"Download {GHD_LABEL}? (Y/N): ").lower()
    if answer == "m":
        return
    if answer == "n":
        cprint("[INFO] Skipping GitHub Desktop installation.", Fore.LIGHTBLACK_EX)
        print()
    elif answer == "y":
        gh_default_path = Path(os.getenv("LocalAppData", "")) / "GitHubDesktop"
        gh_target_path = dev_root / "tools" / "GitHubDesktop"

        print()
        cprint("[INFO] Choose where to install GitHub Desktop:", Fore.CYAN)
        cprint("  1 = Default install to LocalAppData (recommended)", Fore.LIGHTGREEN_EX)
        cprint(f"  2 = Container install to {dev_root / 'tools' / 'GitHubDesktop'}", Fore.LIGHTYELLOW_EX)
        print()

        mode = input("Install mode (1 or 2): ").strip()
        if mode.lower() == "m":
            return

        if mode not in ["1", "2"]:
            cprint("[ERROR] Invalid option. Skipping GitHub Desktop install.", Fore.RED)
            return

        cprint(f"Downloading: {GHD_LABEL}", Fore.YELLOW)
        if download_with_progress(GHD_URL, GHD_FILE, GHD_FALLBACK):
            try:
                os.startfile(GHD_FILE)
                input("[INFO] Press Enter once the GitHub Desktop install finishes...")

                subprocess.call('taskkill /f /im GitHubDesktop.exe >nul 2>&1', shell=True)
                cprint("[INFO] Closed running GitHub Desktop process (if any).", Fore.LIGHTBLACK_EX)

                if mode == "1":
                    exe_path = gh_default_path / "GitHubDesktop.exe"
                    if exe_path.exists():
                        cprint(f"[OK] GitHub Desktop installed to: {exe_path}", Fore.GREEN)
                    else:
                        cprint("[ERROR] Could not find GitHub Desktop in default location. Install may have failed.", Fore.RED)

                elif mode == "2":
                    if gh_default_path.exists():
                        cprint(f"[INFO] Moving GitHub Desktop from {gh_default_path} to {gh_target_path}...", Fore.CYAN)
                        if gh_target_path.exists():
                            shutil.rmtree(gh_target_path)
                        shutil.move(str(gh_default_path), str(gh_target_path))

                        exe_path = gh_target_path / "GitHubDesktop.exe"
                        subprocess.call(["setx", "XSE_GITHUB_DESKTOP_PATH", str(exe_path)], shell=True)
                        cprint(f"[OK] GitHub Desktop moved and registered at: {exe_path}", Fore.GREEN)
                    else:
                        cprint("[ERROR] GitHubDesktop folder not found. Install may have failed or been canceled.", Fore.RED)

            except Exception as e:
                cprint(f"[ERROR] GitHub Desktop install or move failed: {e}", Fore.RED)
        else:
            failed = True



    #----------NINJA----------
    NINJA_URL = "https://github.com/ninja-build/ninja/releases/download/v1.13.1/ninja-win.zip"
    NINJA_FALLBACK = "https://github.com/ninja-build/ninja/releases"
    NINJA_FILE = dl_dir / "ninja-win.zip"
    NINJA_LABEL = "Ninja Build System"

    answer = prompt_yesno(f"Download and install {NINJA_LABEL}? (Y/N): ").lower()
    if answer == "m":
        return
    if answer == "n":
        cprint("[INFO] Skipping Ninja installation.", Fore.LIGHTBLACK_EX)
        print()
    elif answer == "y":
        cprint(f"Downloading: {NINJA_LABEL}", Fore.YELLOW)
        if download_with_progress(NINJA_URL, NINJA_FILE, NINJA_FALLBACK):
            try:
                ninja_install_path = dev_root / "tools" / "Ninja"
                ninja_install_path.mkdir(parents=True, exist_ok=True)
                
                cprint("[INFO] Extracting Ninja to tools/Ninja...", Fore.CYAN)
                
                # Extract the zip file
                import zipfile
                with zipfile.ZipFile(NINJA_FILE, 'r') as zip_ref:
                    zip_ref.extractall(ninja_install_path)
                
                # Check if ninja.exe was extracted
                ninja_exe = ninja_install_path / "ninja.exe"
                if ninja_exe.exists():
                    subprocess.call(["setx", "XSE_NINJA_ROOT", str(ninja_install_path)], shell=True)
                    os.environ["XSE_NINJA_ROOT"] = str(ninja_install_path)  # Patch into session
                    cprint(f"[OK] Ninja installed to: {ninja_install_path}", Fore.GREEN)
                    cprint(f"[OK] XSE_NINJA_ROOT set to: {ninja_install_path}", Fore.GREEN)
                else:
                    cprint("[ERROR] ninja.exe not found after extraction.", Fore.RED)
                    
            except Exception as e:
                cprint(f"[ERROR] Ninja installation failed: {e}", Fore.RED)
        else:
            failed = True

    print()
    input("Press Enter to return to the main menu...")





