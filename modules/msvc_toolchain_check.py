import subprocess
import shutil
import os
import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

#----------output----------
def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

#----------download----------
def download_with_progress(url, dest_path):
    import requests
    from tqdm import tqdm

    response = requests.get(url, stream=True)
    total = int(response.headers.get('content-length', 0))
    with open(dest_path, 'wb') as file, tqdm(
        desc=dest_path.name,
        total=total,
        unit='B',
        unit_scale=True,
        unit_divisor=1024
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

#----------env----------
def set_env_variable(key, value):
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        subprocess.run(["setx", key, value], check=True, creationflags=creationflags)
        cprint(f"[OK] Set environment variable {key} = {value}", Fore.GREEN)
    except Exception as e:
        cprint(f"[ERROR] Failed to set environment variable {key}: {e}", Fore.RED)

def get_dev_and_toolchain_roots():
    dev_env = "XSE_CLIBDT_DEVROOT"
    tools_env = "XSE_MSVCTOOLS_ROOT"

    dev_root = os.environ.get(dev_env)
    tools_root = os.environ.get(tools_env)

    if not dev_root or Path(dev_root).name.startswith("."):
        dev_root = str(Path("C:/sksedev"))
        set_env_variable(dev_env, dev_root)

    if not tools_root or Path(tools_root).name.startswith("."):
        tools_root = str(Path(dev_root) / "msvc-toolchain")
        set_env_variable(tools_env, tools_root)

    tools_path = Path(tools_root)
    tools_path.mkdir(parents=True, exist_ok=True)

    cprint(f"[OK] {dev_env} = {dev_root}", Fore.GREEN)
    cprint(f"[OK] {tools_env} = {tools_path}", Fore.GREEN)

    return Path(dev_root), tools_path

#----------install----------
def install_msvc_build_tools_silent(tools_path: Path) -> bool:
    vs_installer_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
    CACHE_DIR = Path(os.getenv("LOCALAPPDATA", "")) / "ClibDT" / "cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    bootstrapper = CACHE_DIR / "vs_BuildTools.exe"

    if not bootstrapper.exists():
        cprint("[INFO] Downloading Build Tools installer...", Fore.GREEN)
        try:
            download_with_progress(vs_installer_url, bootstrapper)
        except Exception as e:
            cprint(f"[ERROR] Failed to download vs_BuildTools.exe: {e}", Fore.RED)
            return False
    else:
        cprint("[INFO] Using cached MSVC installer.", Fore.LIGHTBLACK_EX)

    cprint(f"[INFO] Installing Build Tools to:\n  {tools_path}", Fore.LIGHTBLACK_EX)

    try:
        cmd = [
            str(bootstrapper),
            "--installPath", str(tools_path),
            "--add", "Microsoft.VisualStudio.Workload.VCTools",
            "--includeRecommended"
        ]
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        cprint(f"[ERROR] Build Tools installer failed to run: {e}", Fore.RED)
        return False

#----------detect----------
def detect_msvc() -> tuple[bool, dict | None]:
    cprint("=== Validating MSVC toolchain (cl.exe + lib.exe) ===", Fore.LIGHTCYAN_EX)
    dev_root, tools_path = get_dev_and_toolchain_roots()

    def scan_for_msvc_toolchain(base: Path) -> tuple[Path, Path] | None:
        msvc_root = base / "VC" / "Tools" / "MSVC"
        if not msvc_root.exists():
            return None

        versions = []
        for ver_dir in msvc_root.iterdir():
            try:
                _ = tuple(int(p) for p in ver_dir.name.split('.'))  # validate it's a version
                cl = ver_dir / "bin/Hostx64/x64/cl.exe"
                lib = ver_dir / "bin/Hostx64/x64/lib.exe"
                if cl.exists() and lib.exists():
                    versions.append((ver_dir.name, cl, lib))
            except:
                continue

        if not versions:
            return None

        versions.sort(key=lambda x: tuple(int(p) for p in x[0].split('.')), reverse=True)
        _, cl_path, lib_path = versions[0]
        return cl_path.parent, lib_path.parent

    #----------FIRST PRIORITY: user-defined MSVC install path----------
    result = scan_for_msvc_toolchain(tools_path)
    if result:
        cl_dir, _ = result
        env = os.environ.copy()
        env["PATH"] = str(cl_dir) + os.pathsep + env["PATH"]
        # Set environment variable for this session and permanently
        os.environ["XSE_MSVCTOOLS_ROOT"] = str(tools_path)
        set_env_variable("XSE_MSVCTOOLS_ROOT", str(tools_path))
        cprint(f"[OK] Found cl.exe in XSE_MSVCTOOLS_ROOT and added to PATH:\n  {cl_dir}", Fore.GREEN)
        return True, env

    #----------OPTIONAL FALLBACK: Check common installation paths----------
    user_set = os.environ.get("XSE_MSVCTOOLS_ROOT")
    if not user_set:
        common_paths = [
            # VS2022 Community (most common)
            Path("C:/Program Files/Microsoft Visual Studio/2022/Community"),
            # VS2022 Professional/Enterprise
            Path("C:/Program Files/Microsoft Visual Studio/2022/Professional"),
            Path("C:/Program Files/Microsoft Visual Studio/2022/Enterprise"),
            # VS2022 Build Tools (64-bit)
            Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools"),
            # VS2022 Build Tools (32-bit - typical install path)
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools"),
            # VS2022 32-bit installations
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Community"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Professional"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Enterprise"),
            # VS2019 (fallback)
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Community"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Professional"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Enterprise"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools"),
            # VS2017 (legacy fallback)
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Community"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Enterprise"),
            Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools"),
        ]
        
        for path in common_paths:
            result = scan_for_msvc_toolchain(path)
            if result:
                cl_dir, _ = result
                env = os.environ.copy()
                env["PATH"] = str(cl_dir) + os.pathsep + env["PATH"]
                # Set environment variable for this session and permanently
                os.environ["XSE_MSVCTOOLS_ROOT"] = str(path)
                set_env_variable("XSE_MSVCTOOLS_ROOT", str(path))
                cprint(f"[OK] Found cl.exe in {path.name} and added to PATH:\n  {cl_dir}", Fore.GREEN)
                return True, env

    #----------THIRD OPTION: vswhere----------
    vswhere_path = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere_path.exists():
        try:
            vswhere_url = "https://github.com/microsoft/vswhere/releases/latest/download/vswhere.exe"
            vswhere_path.parent.mkdir(parents=True, exist_ok=True)
            from urllib.request import urlretrieve
            urlretrieve(vswhere_url, vswhere_path)
            cprint("[OK] Downloaded vswhere.exe.", Fore.GREEN)
        except Exception as e:
            cprint(f"[WARNING] Could not download vswhere.exe: {e}", Fore.YELLOW)

    try:
        if vswhere_path.exists():
            output = subprocess.check_output([
                str(vswhere_path),
                "-latest",
                "-products", "*",
                "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property", "installationPath"
            ], encoding="utf-8").strip()

            vs_path = Path(output)
            result = scan_for_msvc_toolchain(vs_path)
            if result:
                cl_dir, _ = result
                env = os.environ.copy()
                env["PATH"] = str(cl_dir) + os.pathsep + env["PATH"]
                # Set environment variable for this session and permanently
                os.environ["XSE_MSVCTOOLS_ROOT"] = str(vs_path)
                set_env_variable("XSE_MSVCTOOLS_ROOT", str(vs_path))
                cprint(f"[OK] MSVC found via vswhere and added to PATH:\n  {cl_dir}", Fore.GREEN)
                return True, env
    except Exception as e:
        cprint(f"[WARNING] vswhere detection failed: {e}", Fore.YELLOW)

    #----------FINAL: try to install----------
    cprint("[WARNING] No valid MSVC toolchain found. Attempting to install...", Fore.YELLOW)
    success = install_msvc_build_tools_silent(tools_path)
    if success:
        cprint("[INFO] Toolchain installed. Please re-run your build.", Fore.CYAN)
        return False, None
    else:
        cprint("[ERROR] Could not install Build Tools.", Fore.RED)
        return False, None

#----------main----------
def main():
    ok, env = detect_msvc()
    if ok:
        cprint("[OK] Toolchain usable in current session.", Fore.GREEN)

if __name__ == "__main__":
    main()
