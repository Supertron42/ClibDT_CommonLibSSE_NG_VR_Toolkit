import os
import subprocess
import shutil
import sys
from pathlib import Path
from colorama import init, Fore, Style
from tqdm import tqdm

init(autoreset=True)

#----------Output Helpers----------
def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def pause():
    input("\nPress Enter to continue...")

#----------External Module Imports----------
from modules.backup_function_call import backup_project_snapshot
from modules.msvc_toolchain_check import (
    detect_msvc,
    install_msvc_build_tools_silent,
    get_dev_and_toolchain_roots
)

#----------Tool Existence Check----------
def find_xmake():
    xmake_path = shutil.which("xmake")
    if xmake_path:
        return xmake_path

    xmake_root = os.environ.get("XSE_XMAKE_ROOT")
    if xmake_root:
        alt = Path(xmake_root) / "xmake.exe"
        if alt.exists():
            return str(alt)
    return None

def find_ninja():
    #----------1. Check PATH----------
    ninja_path = shutil.which("ninja")
    if ninja_path:
        return ninja_path
    #----------2. Check XSE_NINJA_ROOT----------
    ninja_root = os.environ.get("XSE_NINJA_ROOT")
    if ninja_root:
        alt = Path(ninja_root) / "ninja.exe"
        if alt.exists():
            return str(alt)
    #----------3. Check devroot/tools/Ninja----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        alt = Path(dev_root) / "tools" / "Ninja" / "ninja.exe"
        if alt.exists():
            return str(alt)
    return None

def find_cl_exe():
    """
    Robustly find cl.exe (MSVC compiler) in typical locations, env vars, devroot, and via vswhere.
    Returns the path to cl.exe if found, else None.
    """
    from shutil import which
    #----------1. Check common install locations----------
    common_paths = [
        #----------VS2022 Community (most common)----------
        Path("C:/Program Files/Microsoft Visual Studio/2022/Community"),
        #----------VS2022 Professional/Enterprise----------
        Path("C:/Program Files/Microsoft Visual Studio/2022/Professional"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Enterprise"),
        #----------VS2022 Build Tools (64-bit)----------
        Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools"),
        #----------VS2022 Build Tools (32-bit - typical install path)----------
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools"),
        #----------VS2022 32-bit installations----------
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Community"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Professional"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Enterprise"),
        #----------VS2019----------
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Community"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Professional"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/Enterprise"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools"),
        #----------VS2017----------
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Community"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/Enterprise"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools"),
    ]
    def check_msvc_path(base_path):
        msvc_root = base_path / "VC" / "Tools" / "MSVC"
        if not msvc_root.exists():
            return None
        try:
            versions = [d for d in msvc_root.iterdir() if d.is_dir()]
        except PermissionError as e:
            cprint(f"[WARN] Permission denied accessing {msvc_root}: {e}", Fore.YELLOW)
            return None
        except Exception as e:
            cprint(f"[WARN] Error accessing {msvc_root}: {e}", Fore.YELLOW)
            return None
        if not versions:
            return None
        versions.sort(key=lambda d: tuple(int(x) for x in d.name.split(".")), reverse=True)
        for ver_dir in versions:
            cl_path = ver_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
            if cl_path.exists():
                return cl_path
        return None
    #----------1. Check all common install locations----------
    for path in common_paths:
        cl_path = check_msvc_path(path)
        if cl_path:
            cprint(f"[OK] Found cl.exe at: {cl_path}", Fore.GREEN)
            return str(cl_path)
    #----------2. Check devroot/tools/BuildTools----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        devroot_path = Path(dev_root) / "tools" / "BuildTools"
        cl_path = check_msvc_path(devroot_path)
        if cl_path:
            cprint(f"[OK] Found cl.exe in devroot at: {cl_path}", Fore.GREEN)
            return str(cl_path)
    #----------3. Check XSE_MSVCTOOLS_ROOT env var----------
    msvc_env_root = os.environ.get("XSE_MSVCTOOLS_ROOT")
    if msvc_env_root:
        cl_path = check_msvc_path(Path(msvc_env_root))
        if cl_path:
            cprint(f"[OK] Found cl.exe from XSE_MSVCTOOLS_ROOT at: {cl_path}", Fore.GREEN)
            return str(cl_path)
        else:
            cprint(f"[WARN] XSE_MSVCTOOLS_ROOT is set but cl.exe not found in: {msvc_env_root}", Fore.YELLOW)
    #----------4. Try vswhere as fallback----------
    vswhere_path = which("vswhere")
    if not vswhere_path:
        vswhere_path = str(Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe")
    if Path(vswhere_path).exists():
        result = subprocess.run([vswhere_path, "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            vs_path = Path(result.stdout.strip())
            cl_path = check_msvc_path(vs_path)
            if cl_path:
                cprint(f"[OK] Found cl.exe via vswhere at: {cl_path}", Fore.GREEN)
                return str(cl_path)
    cprint("[ERROR] Could not find cl.exe in any known location.", Fore.RED)
    return None

#----------Validate Skyrim Environment Vars----------
def validate_skyrim_env():
    ninja_path = find_ninja()
    if not ninja_path:
        cprint('[WARNING] Ninja not found. Some builds may be slower or fail.', Fore.YELLOW)
    else:
        cprint(f'[OK] Found Ninja at: {ninja_path}', Fore.GREEN)
        # Add Ninja directory to PATH for this process
        ninja_dir = str(Path(ninja_path).parent)
        os.environ["PATH"] = f"{ninja_dir};" + os.environ["PATH"]
    cprint("=== Checking Skyrim environment variables ===", Fore.LIGHTCYAN_EX)
    updated = False

    for var, label in [("XSE_TES5_GAME_PATH", "Game"), ("XSE_TES5_MODS_PATH", "Mods")]:
        val = os.getenv(var)
        if val:
            cprint(f"[OK] {label} path: {val}", Fore.GREEN)
        else:
            resp = input(f"{label} path not set. Set now? [Y/n]: ").strip().lower()
            if resp == "y":
                new_path = input(f"Enter full {label} path: ").strip()
                if new_path:
                    subprocess.run(["setx", var, new_path], check=True)
                    cprint(f"[INFO] {label} path set permanently.", Fore.CYAN)
                    updated = True
                else:
                    cprint(f"[WARNING] No {label} path provided.", Fore.YELLOW)

    if updated:
        cprint("[CAUTION] Paths updated. Please re-run this script.", Fore.YELLOW)
        pause()
        sys.exit(0)
    else:
        cprint("[OK] Skyrim path validation complete.", Fore.GREEN)

#----------Build Mode Selection----------
def choose_build_mode():
    cprint("=== Choose Build Mode ===", Fore.LIGHTCYAN_EX)
    print("  1. Debug\n  2. Release\n  3. Releasedbg\n  m. Return to menu")
    mode = input("Choose a build type [Default: 2]: ").strip().lower()
    if mode == "m":
        return "__menu__"
    return { "1": "debug", "2": "release", "3": "releasedbg" }.get(mode or "2", "release")

#----------Skyrim Runtime Selection----------
def choose_runtime():
    cprint("=== Choose Skyrim Runtime Target ===", Fore.LIGHTCYAN_EX)
    print("  1. SE only\n  2. AE only\n  3. SE + AE (dual)\n  4. VR only\n  m. Return to menu")
    choice = input("Choose runtime [Default: 3]: ").strip().lower()
    if choice == "m":
        return "__menu__"
    return {
        "1": ["--skyrim_se=y"],
        "2": ["--skyrim_ae=y"],
        "3": ["--skyrim_se=y", "--skyrim_ae=y"],
        "4": ["--skyrim_vr=y"]
    }.get(choice or "3", ["--skyrim_se=y", "--skyrim_ae=y"])

#----------Clean Build Folder (Optional)----------
def on_rm_error(func, path, exc_info):
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        cprint(f"[ERROR] Failed to delete {path}: {e}", Fore.RED)

def maybe_clean():
    do_clean = input("Clean project? (deletes Build and .xmake folders)? (Y/N): ").strip().lower()
    if do_clean == "m":
        return "__menu__"

    if do_clean == "y" or do_clean == "":
        for folder in ["build", ".xmake"]:
            path = Path(folder)
            if path.exists() and path.is_dir():
                try:
                    shutil.rmtree(path, onerror=on_rm_error)
                    cprint(f"[OK] {folder}/ folder deleted.", Fore.GREEN)
                except Exception as e:
                    cprint(f"[ERROR] Failed to delete {folder}/: {e}", Fore.RED)
            else:
                cprint(f"[INFO] {folder}/ not found. Skipping.", Fore.LIGHTBLACK_EX)
    else:
        cprint("[INFO] Skipping clean step.", Fore.LIGHTBLACK_EX)

#----------Full Build Process (Either env or vcvars shell)----------
def run_xmake_in_vcvars_env(build_mode, runtime_flags, env=None):
    import re
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
    from rich.console import Console
    console = Console()
    runtime_str = " ".join(runtime_flags)
    xmake_path = find_xmake()

    if not xmake_path:
        cprint("[ERROR] xmake could not be found.", Fore.RED)
        pause()
        return

    #----------FIX: Set XMAKE_GLOBALDIR to a user-writable directory (devroot/.xmake)----------
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        xmake_globaldir = str(Path(dev_root) / ".xmake")
        os.environ["XMAKE_GLOBALDIR"] = xmake_globaldir
        Path(xmake_globaldir).mkdir(parents=True, exist_ok=True)
        cprint(f"[INFO] Set XMAKE_GLOBALDIR to {xmake_globaldir}", Fore.LIGHTBLACK_EX)

    #----------Ensure Ninja is on PATH if found----------
    ninja_path = find_ninja()
    if ninja_path:
        ninja_dir = str(Path(ninja_path).parent)
        os.environ["PATH"] = f"{ninja_dir};" + os.environ["PATH"]
        cprint(f"[INFO] Added Ninja to PATH: {ninja_dir}", Fore.LIGHTBLACK_EX)

    def stream_xmake(cmd, env):
        progress_re = re.compile(r"\[\s*(\d+)%\]: (.+)")
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        if proc.stdout is not None:
            for line in proc.stdout:
                line = line.rstrip()
                match = progress_re.match(line)
                if match:
                    percent = int(match.group(1))
                    desc = match.group(2)
                    cprint(f"[ {percent:3d}% ]: {desc}", Fore.CYAN)
                else:
                    print(line)
        proc.wait()
        if proc.returncode != 0:
            cprint("[ERROR] xmake build failed.", Fore.RED)
        else:
            cprint("[OK] Build completed.", Fore.GREEN)
        return proc.returncode

    if env:
        cmd = [xmake_path]
        cprint("[INFO] Running xmake with injected MSVC env...", Fore.CYAN)
        stream_xmake(cmd, env)
    else:
        tools_root = os.environ.get("XSE_MSVCTOOLS_ROOT")
        if not tools_root:
            _, tools_root = get_dev_and_toolchain_roots()

        vcvarsall = Path(tools_root) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
        if not vcvarsall.exists():
            cprint("[ERROR] vcvarsall.bat not found — toolchain not initialized.", Fore.RED)
            pause()
            return

        cmd = f'call "{vcvarsall}" x64 && "{xmake_path}"'
        cprint("[INFO] Running xmake inside MSVC shell via vcvarsall...", Fore.CYAN)
        # Use a temp batch file to stream output
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".bat", delete=False) as tf:
            tf.write(cmd)
            tf_path = tf.name
        proc = subprocess.Popen(["cmd", "/c", tf_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        progress_re = re.compile(r"\[\s*(\d+)%\]: (.+)")
        if proc.stdout is not None:
            for line in proc.stdout:
                line = line.rstrip()
                match = progress_re.match(line)
                if match:
                    percent = int(match.group(1))
                    desc = match.group(2)
                    cprint(f"[ {percent:3d}% ]: {desc}", Fore.CYAN)
                else:
                    print(line)
        proc.wait()
        if proc.returncode != 0:
            cprint("[ERROR] xmake build failed.", Fore.RED)
        else:
            cprint("[OK] Build completed.", Fore.GREEN)
        os.remove(tf_path)
        return

#----------Full Build Pipeline Orchestrator----------
def run_build_project():
    xmake_path = find_xmake()
    if xmake_path:
        os.environ["PATH"] = f"{Path(xmake_path).parent};" + os.environ["PATH"]

    cprint(f"[INFO] Running from project folder:\n  {os.getcwd()}", Fore.CYAN)

    if not Path("xmake.lua").exists():
        cprint("[ERROR] No xmake.lua found in current directory.", Fore.RED)
        pause()
        return

    result = maybe_clean()
    if result == "__menu__":
        return

    xmake_path = find_xmake()
    if not xmake_path:
        cprint("[ERROR] xmake is not installed or not in PATH or XSE_XMAKE_ROOT.", Fore.RED)
        pause()
        return

    try:
        ok, env = detect_msvc()
    except Exception as e:
        cprint(f"[ERROR] Failed to detect MSVC: {e}", Fore.RED)
        pause()
        return

    if not ok:
        cprint("[INFO] Attempting to install MSVC Build Tools sandboxed...", Fore.YELLOW)
        _, tools_path = get_dev_and_toolchain_roots()
        success = install_msvc_build_tools_silent(tools_path)
        if not success:
            cprint("[FATAL] Could not install MSVC Build Tools. Cannot continue.", Fore.RED)
            pause()
            return
        else:
            cprint("[INFO] Build Tools were installed. Please re-run this script.", Fore.CYAN)
            pause()
            return

    validate_skyrim_env()
    #----------Ensure Ninja is on PATH if found----------
    ninja_path = find_ninja()
    if ninja_path:
        ninja_dir = str(Path(ninja_path).parent)
        os.environ["PATH"] = f"{ninja_dir};" + os.environ["PATH"]
        cprint(f"[INFO] Added Ninja to PATH: {ninja_dir}", Fore.LIGHTBLACK_EX)

    build_mode = choose_build_mode()
    if build_mode == "__menu__":
        return

    runtime_flags = choose_runtime()
    if runtime_flags == "__menu__":
        return

    backup_project_snapshot()

    cprint(f"[OK] Build mode set to: {build_mode}", Fore.GREEN)
    cprint("[OK] Runtime flags set.", Fore.GREEN)

    cmd = [xmake_path, "f", "-m", build_mode, "--toolchain=msvc", *runtime_flags]
    cprint("[INFO] Pre-generating .xmake/ config...", Fore.CYAN)
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        cprint("[ERROR] Failed to run xmake f", Fore.RED)
        pause()
        return

    run_xmake_in_vcvars_env(build_mode, runtime_flags, env)

    cprint("[INFO] Endorsements appreciated ❤️", Fore.GREEN)
    cprint("https://www.nexusmods.com/skyrimspecialedition/mods/154240", Fore.CYAN)
    pause()

if __name__ == "__main__":
    run_build_project()
