import os
import subprocess
import shutil
import sys
import json
from pathlib import Path
from colorama import init, Fore, Style
from tqdm import tqdm
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QGroupBox, QProgressBar, QTextEdit, QMessageBox, QFileDialog, QLineEdit, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

init(autoreset=True)

#----------Output Helpers----------
# Global status callback for GUI output
_gui_status_callback = None

def set_gui_status_callback(callback):
    global _gui_status_callback
    _gui_status_callback = callback

def cprint(msg, color=Fore.RESET):
    """Print colored text with GUI callback support"""
    colored_msg = color + msg + Style.RESET_ALL
    if _gui_status_callback:
        # Send to GUI terminal
        _gui_status_callback(colored_msg)
    else:
        # Fall back to console output
        print(colored_msg)

def verbose_print(msg, level="INFO"):
    """Print verbose debug messages if verbose mode is enabled"""
    # Disabled verbose debugging - only keep essential logging
    pass

def pause():
    input("\nPress Enter to continue...")

#----------External Module Imports----------
from modules.utilities.common import VERSION
from modules.backup_function_call import backup_project_snapshot
from modules.msvc_toolchain_check import (
    detect_msvc,
    install_msvc_build_tools_silent,
    get_dev_and_toolchain_roots
)

def set_env_variable(key, value):
    """Set environment variable both for current session and permanently"""
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        subprocess.run(["setx", key, value], shell=True, check=True, creationflags=creationflags)
        os.environ[key] = value
        return True
    except Exception as e:
        cprint(f"[WARN] Failed to set environment variable {key}: {e}", Fore.YELLOW)
        return False

def validate_and_set_env_vars():
    """Validate and set environment variables for all tools"""
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[WARN] XSE_CLIBDT_DEVROOT not set", Fore.YELLOW)
        return
    
    # Check and set Xmake
    xmake_path = find_xmake()
    if xmake_path and not os.getenv("XSE_XMAKE_ROOT"):
        xmake_root = str(Path(xmake_path).parent)
        set_env_variable("XSE_XMAKE_ROOT", xmake_root)
        cprint(f"[INFO] Set XSE_XMAKE_ROOT to: {xmake_root}", Fore.GREEN)
    
    # Check and set Ninja (prioritize working ninja)
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        # Check tools/Ninja location first (working ninja)
        tools_ninja = Path(dev_root) / "tools" / "Ninja" / "ninja.exe"
        if tools_ninja.exists():
            ninja_root = str(tools_ninja.parent)
            set_env_variable("XSE_NINJA_ROOT", ninja_root)
            cprint(f"[INFO] Set XSE_NINJA_ROOT to tools/Ninja location: {ninja_root}", Fore.GREEN)
        else:
            # Fallback to find_ninja() which will check other locations
            ninja_path = find_ninja()
            if ninja_path and not os.getenv("XSE_NINJA_ROOT"):
                ninja_root = str(Path(ninja_path).parent)
                set_env_variable("XSE_NINJA_ROOT", ninja_root)
                cprint(f"[INFO] Set XSE_NINJA_ROOT to: {ninja_root}", Fore.GREEN)
    else:
        # Fallback to find_ninja() if dev_root not set
        ninja_path = find_ninja()
        if ninja_path and not os.getenv("XSE_NINJA_ROOT"):
            ninja_root = str(Path(ninja_path).parent)
            set_env_variable("XSE_NINJA_ROOT", ninja_root)
            cprint(f"[INFO] Set XSE_NINJA_ROOT to: {ninja_root}", Fore.GREEN)
    
    # Check and set MSVC toolchain
    if not os.getenv("XSE_MSVCTOOLS_ROOT"):
        try:
            ok, env = detect_msvc()
            if ok:
                # MSVC was found, the detect_msvc function should have set the env var
                msvc_root = os.getenv("XSE_MSVCTOOLS_ROOT")
                if msvc_root:
                    cprint(f"[INFO] MSVC toolchain found at: {msvc_root}", Fore.GREEN)
        except Exception as e:
            cprint(f"[WARN] Could not detect MSVC toolchain: {e}", Fore.YELLOW)

#----------Tool Existence Check----------
def find_xmake():
    """Find xmake installation"""
    # First check PATH
    xmake_path = shutil.which("xmake")
    if xmake_path:
        return xmake_path

    # Check environment variable
    xmake_root = os.environ.get("XSE_XMAKE_ROOT")
    if xmake_root:
        alt = Path(xmake_root) / "xmake.exe"
        if alt.exists():
            return str(alt)
    
    # Check devroot tools directory
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        # Check lowercase first
        devroot_xmake = Path(dev_root) / "tools" / "xmake" / "xmake.exe"
        if devroot_xmake.exists():
            set_env_variable("XSE_XMAKE_ROOT", str(devroot_xmake.parent))
            return str(devroot_xmake)
        
        # Check uppercase variant
        devroot_xmake = Path(dev_root) / "tools" / "Xmake" / "xmake.exe"
        if devroot_xmake.exists():
            set_env_variable("XSE_XMAKE_ROOT", str(devroot_xmake.parent))
            return str(devroot_xmake)
    
    return None

def find_ninja():
    """Find ninja installation"""
    # Check PATH
    ninja_path = shutil.which("ninja")
    if ninja_path:
        return ninja_path
    
    # Check XSE_NINJA_ROOT
    ninja_root = os.environ.get("XSE_NINJA_ROOT")
    if ninja_root:
        alt = Path(ninja_root) / "ninja.exe"
        if alt.exists():
            return str(alt)
    
    # Check devroot/tools/Ninja
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if dev_root:
        # Check the expected location first (working ninja)
        alt = Path(dev_root) / "tools" / "Ninja" / "ninja.exe"
        if alt.exists():
            set_env_variable("XSE_NINJA_ROOT", str(alt.parent))
            return str(alt)
        
        # Check BuildTools location as fallback
        buildtools_ninja = Path(dev_root) / "tools" / "BuildTools" / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "Ninja" / "ninja.exe"
        if buildtools_ninja.exists():
            set_env_variable("XSE_NINJA_ROOT", str(buildtools_ninja.parent))
            return str(buildtools_ninja)
    
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
def validate_skyrim_env(status_callback=None):
    """Validate Skyrim environment variables"""
    def status(msg):
        if status_callback:
            status_callback(msg)
    
    # Check Ninja
    ninja_path = find_ninja()
    if not ninja_path:
        status('[WARNING] Ninja not found. Some builds may be slower or fail.')
    else:
        status(f'[OK] Found Ninja at: {ninja_path}')
        # Add Ninja directory to PATH for this process
        ninja_dir = str(Path(ninja_path).parent)
        os.environ["PATH"] = f"{ninja_dir};" + os.environ["PATH"]
    
    # Check environment variables
    env_vars = [
        ("XSE_TES5_GAME_PATH", "Game"),
        ("XSE_TES5_MODS_PATH", "Mods")
    ]
    
    for var, label in env_vars:
        val = os.getenv(var)
        if val:
            status(f"[OK] {label} path: {val}")
        else:
            status(f"[WARNING] {label} path not set: {var}")

    status("[OK] Skyrim path validation complete.")

#----------Clean Build Folder (Optional)----------
def on_rm_error(func, path, exc_info):
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        # Don't use cprint here to avoid duplication
        # cprint(f"[ERROR] Failed to delete {path}: {e}", Fore.RED)
        pass

def clean_project(status_callback=None):
    def status(msg):
        if status_callback:
            status_callback(msg)
        # Don't call cprint to avoid duplication
        # cprint(msg)
    
    for folder in ["build", ".xmake"]:
        path = Path(folder)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path, onerror=on_rm_error)
                status(f"[OK] {folder}/ folder deleted.")
            except Exception as e:
                status(f"[ERROR] Failed to delete {folder}/: {e}")
        else:
            status(f"[INFO] {folder}/ not found. Skipping.")

#----------Build Thread Class----------
class BuildThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, build_mode, runtime_flags, clean_build, status_callback=None, project_path=None, toolchain_path=None):
        super().__init__()
        self.build_mode = build_mode
        self.runtime_flags = runtime_flags
        self.clean_build = clean_build
        self.status_callback = status_callback
        self.project_path = project_path
        self.toolchain_path = toolchain_path
    
    def run(self):
        try:
            def status(msg):
                # Only emit the signal, let the main thread handle the callback
                self.progress_signal.emit(msg)
            
            # Don't set global callback - use only signal-based communication
            # set_gui_status_callback(self.status_callback)
            
            # Redirect stdout and stderr to capture all output
            import sys
            from io import StringIO
            
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = StringIO()
            captured_error = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_error
            
            try:
                # Check for xmake.lua
                if not self.project_path or not (Path(self.project_path) / "xmake.lua").exists():
                    self.finished_signal.emit(False, "No xmake.lua found in current directory or project path.")
                    return
                
                # Change to project directory
                os.chdir(self.project_path)
                status(f"[INFO] Changed to project directory: {self.project_path}")
                
                # Clean if requested
                if self.clean_build:
                    status("Cleaning project...")
                    clean_project(status)
                
                # Find xmake and add to PATH
                xmake_path = find_xmake()
                if not xmake_path:
                    self.finished_signal.emit(False, "xmake is not installed or not in PATH or XSE_XMAKE_ROOT.")
                    return
                
                # Add xmake directory to PATH
                xmake_dir = str(Path(xmake_path).parent)
                os.environ["PATH"] = f"{xmake_dir};" + os.environ["PATH"]
                
                # Set up MSVC environment using vcvarsall.bat
                status("[INFO] Setting up MSVC environment...")
                msvc_root = None
                
                # Find MSVC installation
                if self.toolchain_path and Path(self.toolchain_path).exists():
                    msvc_root = Path(self.toolchain_path)
                    status(f"[INFO] Using custom toolchain path: {self.toolchain_path}")
                else:
                    # Auto-detect MSVC
                    ok, detected_env = detect_msvc()
                    if ok and detected_env:
                        msvc_root = Path(detected_env.get("XSE_MSVCTOOLS_ROOT", ""))
                        status(f"[INFO] Auto-detected MSVC at: {msvc_root}")
                    else:
                        # Try to find in common locations
                        common_paths = [
                            Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools"),
                            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools"),
                            Path("C:/Program Files/Microsoft Visual Studio/2022/Community"),
                            Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/Community"),
                        ]
                        for path in common_paths:
                            if path.exists():
                                msvc_root = path
                                status(f"[INFO] Found MSVC at: {msvc_root}")
                                break
                
                if not msvc_root or not msvc_root.exists():
                    self.finished_signal.emit(False, "Could not find MSVC installation.")
                    return
                
                # Set up environment using vcvarsall.bat
                vcvarsall_path = msvc_root / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
                if not vcvarsall_path.exists():
                    self.finished_signal.emit(False, f"vcvarsall.bat not found at: {vcvarsall_path}")
                    return
                
                status(f"[INFO] Using vcvarsall.bat: {vcvarsall_path}")
                
                # Run vcvarsall.bat to get environment variables
                try:
                    # Create a temporary batch file to capture environment
                    temp_bat = Path("temp_env.bat")
                    with open(temp_bat, "w") as f:
                        f.write(f'@echo off\n')
                        f.write(f'call "{vcvarsall_path}" x64\n')
                        f.write(f'set\n')
                    
                    # Run the batch file and capture output
                    result = subprocess.run([str(temp_bat)], capture_output=True, text=True, shell=True)
                    temp_bat.unlink()  # Clean up
                    
                    if result.returncode != 0:
                        self.finished_signal.emit(False, f"Failed to run vcvarsall.bat: {result.stderr}")
                        return
                    
                    # Parse environment variables from output
                    env = os.environ.copy()
                    for line in result.stdout.splitlines():
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env[key.strip()] = value.strip()
                    
                    status("[OK] MSVC environment set up successfully")
                    
                except Exception as e:
                    self.finished_signal.emit(False, f"Failed to set up MSVC environment: {e}")
                    return
                
                # Ensure the environment has the updated PATH
                if env:
                    # Add xmake and ninja to the environment PATH
                    xmake_dir = str(Path(xmake_path).parent)
                    
                    ninja_path = find_ninja()
                    if ninja_path:
                        ninja_dir = str(Path(ninja_path).parent)
                        env["PATH"] = f"{xmake_dir};{ninja_dir};" + env.get("PATH", "")
                    else:
                        env["PATH"] = f"{xmake_dir};" + env.get("PATH", "")
                
                # MSVC environment is now set up via vcvarsall.bat above
                
                # Validate environment
                validate_skyrim_env(status)
                
                # Check for Ninja
                ninja_path = find_ninja()
                if ninja_path:
                    status(f"[INFO] Found Ninja at: {ninja_path}")
                    
                    # Ensure ninja is in the environment PATH for the build
                    ninja_dir = str(Path(ninja_path).parent)
                    if env and ninja_dir not in env.get("PATH", ""):
                        env["PATH"] = f"{ninja_dir};" + env.get("PATH", "")
                    
                    # Also ensure it's in the current process PATH
                    if ninja_dir not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = f"{ninja_dir};" + os.environ.get("PATH", "")
                else:
                    status("[WARNING] Ninja not found. Some builds may be slower or fail.")
                
                # Backup project
                backup_project_snapshot()
                
                status(f"[OK] Build mode set to: {self.build_mode}")
                status("[OK] Runtime flags set.")
                
                # Set XMAKE_GLOBALDIR to a user-writable location
                dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
                if dev_root:
                    # Use the dev root's .xmake directory for global config
                    xmake_globaldir = str(Path(dev_root) / ".xmake")
                    os.environ["XMAKE_GLOBALDIR"] = xmake_globaldir
                    Path(xmake_globaldir).mkdir(parents=True, exist_ok=True)
                    status(f"[INFO] Set XMAKE_GLOBALDIR to {xmake_globaldir}")
                else:
                    # Fallback to user's home directory
                    xmake_globaldir = str(Path.home() / ".xmake")
                    os.environ["XMAKE_GLOBALDIR"] = xmake_globaldir
                    Path(xmake_globaldir).mkdir(parents=True, exist_ok=True)
                    status(f"[INFO] Set XMAKE_GLOBALDIR to {xmake_globaldir} (fallback)")
                
                # Pre-generate config
                cmd = [xmake_path, "f", "-m", self.build_mode, "--toolchain=msvc", *self.runtime_flags]
                status("[INFO] Pre-generating .xmake/ config...")
                status(f"[DEBUG] Command: {' '.join(cmd)}")
                status(f"[DEBUG] Working directory: {os.getcwd()}")
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    error_msg = f"Failed to run xmake f (return code: {result.returncode})"
                    if result.stdout:
                        error_msg += f"\nSTDOUT: {result.stdout}"
                    if result.stderr:
                        error_msg += f"\nSTDERR: {result.stderr}"
                    self.finished_signal.emit(False, error_msg)
                    return
                
                # Run build
                status("[INFO] Starting build...")
                
                # Build command
                cmd = [xmake_path]
                status(f"[DEBUG] Build command: {' '.join(cmd)}")
                status(f"[DEBUG] Working directory: {os.getcwd()}")
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
                proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=creationflags)
                
                import re
                progress_re = re.compile(r"\[\s*(\d+)%\]: (.+)")
                
                if proc.stdout is not None:
                    for line in proc.stdout:
                        line = line.rstrip()
                        match = progress_re.match(line)
                        if match:
                            percent = int(match.group(1))
                            desc = match.group(2)
                            status(f"[ {percent:3d}% ]: {desc}")
                        else:
                            status(line)
                
                proc.wait()
                
                if proc.returncode != 0:
                    self.finished_signal.emit(False, "xmake build failed.")
                else:
                    status("[OK] Build completed successfully!")
                    self.finished_signal.emit(True, "Build completed successfully!")
                    
            except Exception as e:
                self.finished_signal.emit(False, f"Build failed with error: {e}")
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # No global callback to clear
                # set_gui_status_callback(None)
                
        except Exception as e:
            self.finished_signal.emit(False, f"Thread initialization failed: {e}")

#----------GUI Panel----------
class BuildProjectPanel(QWidget):
    def __init__(self, parent=None, status_callback=None, theme_manager=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.build_thread = None
        self.selected_project_path = None
        self.theme_manager = theme_manager
        # Load user preferences
        self.load_preferences()
        
        # Main layout with proper spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title with styling and divider
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title_row.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Build Project")
        title.setObjectName("build_project_title")
        title_row.addWidget(title)
        
        # Add divider line
        title_divider = QLabel()
        title_divider.setObjectName("title_divider")
        title_divider.setFixedHeight(2)
        title_divider.setMinimumWidth(120)
        title_row.addWidget(title_divider)
        
        title_row.addStretch()  # Push divider to the left
        layout.addLayout(title_row)
        
        # Description
        desc = QLabel("Compile a CommonLibSSE-NG project with xmake and MSVC toolchain.")
        desc.setObjectName("build_project_desc")
        layout.addWidget(desc)
        
        # Project Selection
        project_row = QHBoxLayout()
        project_row.setSpacing(8)
        project_row.setContentsMargins(0, 0, 0, 0)
        
        project_label = QLabel("Project:")
        project_label.setObjectName("project_label")
        project_label.setFixedWidth(60)
        project_row.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setEditable(False)
        self.project_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.project_combo.setObjectName("project_combo")
        self.project_combo.setToolTip("Select the project to compile.")
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        project_row.addWidget(self.project_combo)
        layout.addLayout(project_row)
        
        # Build Mode Selection
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_row.setContentsMargins(0, 0, 0, 0)
        
        mode_label = QLabel("Build Mode:")
        mode_label.setObjectName("build_mode_label")
        mode_label.setFixedWidth(60)
        mode_row.addWidget(mode_label)
        
        self.build_mode_combo = QComboBox()
        self.build_mode_combo.addItems(["Release", "Debug", "Releasedbg"])
        self.build_mode_combo.setCurrentText(self.last_build_mode)
        self.build_mode_combo.currentTextChanged.connect(self.save_preferences)
        mode_row.addWidget(self.build_mode_combo)
        layout.addLayout(mode_row)
        
        # Runtime Selection
        runtime_row = QHBoxLayout()
        runtime_row.setSpacing(8)
        runtime_row.setContentsMargins(0, 0, 0, 0)
        
        runtime_label = QLabel("Runtime:")
        runtime_label.setObjectName("runtime_label")
        runtime_label.setFixedWidth(60)
        runtime_row.addWidget(runtime_label)
        
        self.runtime_combo = QComboBox()
        self.runtime_combo.addItems(["SE + AE (dual)", "SE only", "AE only", "VR only"])
        self.runtime_combo.setCurrentText(self.last_runtime)
        self.runtime_combo.currentTextChanged.connect(self.save_preferences)
        runtime_row.addWidget(self.runtime_combo)
        layout.addLayout(runtime_row)
        
        # Clean Build Option
        self.clean_checkbox = QCheckBox("Clean build (delete build and .xmake folders)")
        self.clean_checkbox.setObjectName("clean_checkbox")
        self.clean_checkbox.setChecked(self.last_clean_build)
        self.clean_checkbox.setToolTip("Delete build/.xmake folders before compiling.")
        self.clean_checkbox.toggled.connect(self.save_preferences)
        layout.addWidget(self.clean_checkbox)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("build_progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%p% %")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Button row with proper spacing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Start Build button
        self.build_btn = QPushButton("Start Build")
        self.build_btn.setProperty("btnType", "success")
        self.build_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.build_btn.setFixedHeight(32)
        self.build_btn.clicked.connect(self.start_build)
        btn_row.addWidget(self.build_btn)

        # Stop Build button
        self.stop_btn = QPushButton("Stop Build")
        self.stop_btn.setProperty("btnType", "uninstall")
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setFixedHeight(32)
        self.stop_btn.clicked.connect(self.stop_build)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)
        
        layout.addLayout(btn_row)
        
        # Regenerate xmake.lua section with divider
        regenerate_title_row = QHBoxLayout()
        regenerate_title_row.setSpacing(8)
        regenerate_title_row.setContentsMargins(0, 0, 0, 0)
        
        regenerate_title = QLabel("Regenerate xmake.lua")
        regenerate_title.setObjectName("section_title")
        regenerate_title_row.addWidget(regenerate_title)
        
        # Add divider line
        regenerate_title_divider = QLabel()
        regenerate_title_divider.setObjectName("section_title_divider")
        regenerate_title_divider.setFixedHeight(1)
        regenerate_title_divider.setMinimumWidth(100)
        regenerate_title_row.addWidget(regenerate_title_divider)
        
        regenerate_title_row.addStretch()  # Push divider to the left
        layout.addLayout(regenerate_title_row)
        
        regenerate_desc = QLabel("Regenerate xmake.lua file for the selected project with new metadata.")
        regenerate_desc.setObjectName("section_desc")
        layout.addWidget(regenerate_desc)
        
        # Metadata input fields
        metadata_row1 = QHBoxLayout()
        metadata_row1.setSpacing(8)
        metadata_row1.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel("Project Name:")
        name_label.setObjectName("metadata_label")
        name_label.setFixedWidth(80)
        metadata_row1.addWidget(name_label)
        
        self.project_name_input = QComboBox()
        self.project_name_input.setObjectName("project_name_input")
        self.project_name_input.setEditable(True)
        self.project_name_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.project_name_input.setPlaceholderText("Select project or enter custom name")
        metadata_row1.addWidget(self.project_name_input)
        
        version_label = QLabel("Version:")
        version_label.setObjectName("metadata_label")
        version_label.setFixedWidth(50)
        metadata_row1.addWidget(version_label)
        
        self.version_input = QLineEdit()
        self.version_input.setObjectName("version_input")
        self.version_input.setPlaceholderText("1.0.0")
        metadata_row1.addWidget(self.version_input)
        
        layout.addLayout(metadata_row1)
        
        metadata_row2 = QHBoxLayout()
        metadata_row2.setSpacing(8)
        metadata_row2.setContentsMargins(0, 0, 0, 0)
        
        author_label = QLabel("Author:")
        author_label.setObjectName("metadata_label")
        author_label.setFixedWidth(80)
        metadata_row2.addWidget(author_label)
        
        self.author_input = QLineEdit()
        self.author_input.setObjectName("author_input")
        self.author_input.setPlaceholderText("Enter author name")
        metadata_row2.addWidget(self.author_input)
        
        layout.addLayout(metadata_row2)
        
        metadata_row3 = QHBoxLayout()
        metadata_row3.setSpacing(8)
        metadata_row3.setContentsMargins(0, 0, 0, 0)
        
        desc_label = QLabel("Description:")
        desc_label.setObjectName("metadata_label")
        desc_label.setFixedWidth(80)
        metadata_row3.addWidget(desc_label)
        
        self.description_input = QLineEdit()
        self.description_input.setObjectName("description_input")
        self.description_input.setPlaceholderText("Enter project description")
        metadata_row3.addWidget(self.description_input)
        
        layout.addLayout(metadata_row3)
        
        # Regenerate button row
        regenerate_btn_row = QHBoxLayout()
        regenerate_btn_row.setSpacing(8)
        regenerate_btn_row.setContentsMargins(0, 0, 0, 0)
        
        # Regenerate xmake.lua button
        self.regenerate_btn = QPushButton("Regenerate xmake.lua")
        self.regenerate_btn.setProperty("btnType", "secondary")
        self.regenerate_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.regenerate_btn.setFixedWidth(180)
        self.regenerate_btn.setFixedHeight(32)
        self.regenerate_btn.clicked.connect(self.regenerate_xmake_lua)
        regenerate_btn_row.addWidget(self.regenerate_btn)
        
        layout.addLayout(regenerate_btn_row)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect to theme manager if provided
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def showEvent(self, event):
        """Override showEvent to apply theme when panel becomes visible"""
        super().showEvent(event)
        # Ensure we're connected to the main window's theme manager
        try:
            main_window = self.window()
            theme_manager = getattr(main_window, 'theme_manager', None)
            if theme_manager:
                self.set_theme_manager(theme_manager)
        except Exception:
            pass
        # Apply theme when panel is shown
        self.apply_theme()
        
        # Load projects when panel is first shown (lazy loading)
        if not hasattr(self, '_projects_loaded'):
            self.load_projects()
            self.load_project_names_for_regenerate()
            self._projects_loaded = True
    
    def load_projects(self):
        """Load available projects from dev_root/projects folder"""
        try:
            # Import the new project detection module
            try:
                from modules.refresh_project import is_valid_clib_project
            except ImportError:
                # Fallback to old xmake.lua detection if module not available
                def is_valid_clib_project(project_path):
                    return (project_path / "xmake.lua").exists()
            
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if not dev_root:
                self.project_combo.addItem("No dev root found")
                return
            
            projects_path = Path(dev_root) / "projects"
            if not projects_path.exists():
                self.project_combo.addItem("No projects folder found")
                return
            
            projects = []
            for item in projects_path.iterdir():
                if item.is_dir() and is_valid_clib_project(item):
                    projects.append(item.name)
            
            if not projects:
                self.project_combo.addItem("No valid ClibDT projects found")
                return
            
            projects.sort()
            self.project_combo.addItems(projects)
            
            # Select last used project if available
            if hasattr(self, 'last_project') and self.last_project in projects:
                self.project_combo.setCurrentText(self.last_project)
            elif projects:
                self.project_combo.setCurrentText(projects[0])
                
        except Exception as e:
            self.project_combo.addItem(f"Error loading projects: {e}")
    
    def on_project_changed(self, project_name):
        """Handle project selection change"""
        if project_name and not project_name.startswith("No ") and not project_name.startswith("Error"):
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if dev_root:
                self.selected_project_path = Path(dev_root) / "projects" / project_name
                self.last_project = project_name
                self.save_preferences()
                
                # Populate metadata fields with project info
                self.populate_metadata_fields()
    
    def load_project_names_for_regenerate(self):
        """Load available project names for the regenerate dropdown"""
        try:
            # Clear existing items
            self.project_name_input.clear()
            
            # Add projects from dev root
            dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
            if dev_root:
                projects_path = Path(dev_root) / "projects"
                if projects_path.exists():
                    # Import the new project detection module
                    try:
                        from modules.refresh_project import is_valid_clib_project
                    except ImportError:
                        # Fallback to old xmake.lua detection if module not available
                        def is_valid_clib_project(project_path):
                            return (project_path / "xmake.lua").exists()
                    
                    projects = []
                    for item in projects_path.iterdir():
                        if item.is_dir() and is_valid_clib_project(item):
                            projects.append(item.name)
                    
                    projects.sort()
                    for project_name in projects:
                        self.project_name_input.addItem(project_name)
            
        except Exception as e:
            self.status(f"[ERROR] Failed to load project names: {e}")
    
    def populate_metadata_fields(self):
        """Populate metadata fields with current project information"""
        if not self.selected_project_path:
            return
            
        # Set project name to folder name by default
        project_name = self.selected_project_path.name
        self.project_name_input.setCurrentText(project_name)
        
        # Try to read existing xmake.lua to extract current metadata
        xmake_file = self.selected_project_path / "xmake.lua"
        if xmake_file.exists():
            try:
                with open(xmake_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract version
                    import re
                    version_match = re.search(r'set_version\("([^"]+)"\)', content)
                    if version_match:
                        self.version_input.setText(version_match.group(1))
                    else:
                        self.version_input.setText("1.0.0")
                    
                    # Extract description
                    desc_match = re.search(r'set_description\("([^"]+)"\)', content)
                    if desc_match:
                        self.description_input.setText(desc_match.group(1))
                    else:
                        self.description_input.setText("No description provided.")
                    
                    # Extract author (harder to parse, use default)
                    self.author_input.setText("Unknown")
                    
            except Exception:
                # If parsing fails, use defaults
                self.version_input.setText("1.0.0")
                self.description_input.setText("No description provided.")
                self.author_input.setText("Unknown")
        else:
            # No existing xmake.lua, use defaults
            self.version_input.setText("1.0.0")
            self.description_input.setText("No description provided.")
            self.author_input.setText("Unknown")
    
    def regenerate_xmake_lua(self):
        """Regenerate xmake.lua file for the selected project"""
        if not self.selected_project_path:
            self.status("[ERROR] Please select a project to regenerate xmake.lua for.")
            return
        
        # Validate inputs
        project_name = self.project_name_input.currentText().strip()
        version = self.version_input.text().strip()
        author = self.author_input.text().strip()
        description = self.description_input.text().strip()
        
        if not project_name:
            self.status("[ERROR] Please enter a project name.")
            return
        
        if not version:
            self.status("[ERROR] Please enter a version number.")
            return
        
        if not author:
            self.status("[ERROR] Please enter an author name.")
            return
        
        if not description:
            self.status("[ERROR] Please enter a description.")
            return
        
        # Check for spaces in project name
        if " " in project_name:
            self.status("[ERROR] Project name cannot contain spaces.")
            return
        
        try:
            # Import the generate_xmakelua module
            from modules.generate_xmakelua import generate_xmake_lua
            
            # Generate the xmake.lua file
            xmake_file = self.selected_project_path / "xmake.lua"
            generate_xmake_lua(xmake_file, project_name, version, author, description)
            
            self.status(f"[SUCCESS] xmake.lua regenerated for project: {project_name}")
            self.status(f"[INFO] File location: {xmake_file}")
            
        except ImportError:
            self.status("[ERROR] Could not import generate_xmakelua module.")
        except Exception as e:
            self.status(f"[ERROR] Failed to regenerate xmake.lua: {e}")
    
    def load_preferences(self):
        """Load user preferences from a simple config file"""
        self.last_build_mode = "Release"
        self.last_runtime = "SE + AE (dual)"
        self.last_clean_build = False
        self.last_project = None

        
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_path = config_dir / "clibdt_build_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    mode = config_data.get('build_mode')
                    if mode in ["Release", "Debug", "Releasedbg"]:
                        self.last_build_mode = mode
                    runtime = config_data.get('runtime')
                    if runtime in ["SE + AE (dual)", "SE only", "AE only", "VR only"]:
                        self.last_runtime = runtime
                    self.last_clean_build = config_data.get('clean_build', False)
                    self.last_project = config_data.get('project')
        except Exception:
            # If loading fails, use defaults
            pass
    
    def save_preferences(self):
        """Save user preferences to a simple config file"""
        try:
            # Use config folder in parent root
            config_dir = Path(__file__).parent.parent / "config"
            config_dir.mkdir(exist_ok=True)  # Ensure config directory exists
            config_path = config_dir / "clibdt_build_config.json"
            config_data = {
                'build_mode': self.build_mode_combo.currentText(),
                'runtime': self.runtime_combo.currentText(),
                'clean_build': self.clean_checkbox.isChecked(),
                'clibdt_version': VERSION
            }
            if hasattr(self, 'last_project') and self.last_project:
                config_data['project'] = self.last_project
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception:
            # If saving fails, just continue
            pass
    
    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)
    
    def get_build_mode(self):
        mode_map = {
            "Release": "release",
            "Debug": "debug", 
            "Releasedbg": "releasedbg"
        }
        return mode_map.get(self.build_mode_combo.currentText(), "release")
    
    def get_runtime_flags(self):
        runtime_map = {
            "SE + AE (dual)": ["--skyrim_se=y", "--skyrim_ae=y"],
            "SE only": ["--skyrim_se=y"],
            "AE only": ["--skyrim_ae=y"],
            "VR only": ["--skyrim_vr=y"]
        }
        return runtime_map.get(self.runtime_combo.currentText(), ["--skyrim_se=y", "--skyrim_ae=y"])
    
    def start_build(self):
        if not self.selected_project_path:
            QMessageBox.warning(self, "No Project Selected", "Please select a project to build.")
            return
        
        # Check for valid project using new detection method
        try:
            from modules.refresh_project import is_valid_clib_project
        except ImportError:
            # Fallback to old xmake.lua detection if module not available
            def is_valid_clib_project(project_path):
                return (project_path / "xmake.lua").exists()
        
        if not is_valid_clib_project(self.selected_project_path):
            QMessageBox.critical(self, "Invalid Project", f"No valid ClibDT project found in {self.selected_project_path}")
            return
        
        self.build_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.status("=== Starting Build ===")
        self.status(f"Project: {self.selected_project_path.name}")
        self.status(f"Build Mode: {self.build_mode_combo.currentText()}")
        self.status(f"Runtime: {self.runtime_combo.currentText()}")
        self.status(f"Clean Build: {self.clean_checkbox.isChecked()}")
        self.status("Toolchain: Auto-detected from environment variables")
        self.status("")
        
        # Start build thread (no custom toolchain path - use environment variables)
        self.build_thread = BuildThread(
            self.get_build_mode(),
            self.get_runtime_flags(),
            self.clean_checkbox.isChecked(),
            self.status,
            str(self.selected_project_path),
            None  # Always use auto-detection from environment variables
        )
        
        # Disconnect any existing connections to prevent duplicates
        try:
            self.build_thread.progress_signal.disconnect()
        except:
            pass
        try:
            self.build_thread.finished_signal.disconnect()
        except:
            pass
        
        # Connect signals
        self.build_thread.progress_signal.connect(self.status)
        self.build_thread.finished_signal.connect(self.build_finished)
        self.build_thread.start()
    
    def stop_build(self):
        if self.build_thread and self.build_thread.isRunning():
            self.build_thread.terminate()
            self.build_thread.wait()
            self.status("[INFO] Build stopped by user.")
            self.build_finished(False, "Build stopped by user.")
    
    def build_finished(self, success, message):
        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status("[SUCCESS] Build completed successfully!")
            QMessageBox.information(self, "Build Complete", "Build completed successfully!")
        else:
            self.status(f"[ERROR] {message}")
            QMessageBox.critical(self, "Build Failed", f"Build failed: {message}")
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def apply_theme(self):
        """Apply theme colors to the panel"""
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
        else:
            # Fallback theme
            theme = {
                'window_bg': '#1e1e1e',
                'bg_primary': '#2d2d2d',
                'bg_secondary': '#252525',
                'text_primary': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'text_light': '#ffffff',
                'button_bg': '#0078d4',
                'button_hover': '#106ebe',
                'button_pressed': '#005a9e',
                'input_bg': '#2d2d2d',
                'input_border': '#404040',
                'input_focus': '#0078d4',
                'separator': '#404040',
                'success_color': '#27ae60',
                'error_color': '#e74c3c',
                'warning_color': '#f39c12',
                'info_color': '#3498db'
            }
        
        # Ultra-compact styling that overrides ALL global styling
        self.setStyleSheet(f"""
            /* Nuclear option: Override ALL global styling with ultra-compact layout */
            BuildProjectPanel,
            BuildProjectPanel * {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background-color: {theme['window_bg']} !important;
                color: {theme['text_primary']} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            }}
            
            /* Typography Hierarchy - Only headers are bold */
            BuildProjectPanel QLabel {{
                background-color: transparent !important;
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                font-weight: normal !important;
            }}
            
            /* Header elements - ONLY these are bold */
            BuildProjectPanel QLabel#build_project_title {{
                font-size: 18px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-bottom: 4px !important;
                background: transparent !important;
                padding: 6px 0px !important;
            }}
            
            BuildProjectPanel QLabel#title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            BuildProjectPanel QLabel#build_project_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 11px !important;
                margin-bottom: 8px !important;
                font-weight: normal !important;
            }}
            
            BuildProjectPanel QLabel#section_title {{
                font-size: 13px !important;
                font-weight: bold !important;
                color: {theme['text_primary']} !important;
                margin-top: 8px !important;
                margin-bottom: 4px !important;
                background: transparent !important;
                padding: 4px 0px !important;
            }}
            
            BuildProjectPanel QLabel#section_title_divider {{
                background-color: {theme['separator']} !important;
                border: none !important;
                margin: 0px !important;
                padding: 0px !important;
            }}
            
            BuildProjectPanel QLabel#section_desc {{
                color: {theme['text_secondary']} !important;
                font-size: 10px !important;
                margin-bottom: 6px !important;
                font-weight: normal !important;
            }}
            
            BuildProjectPanel QLabel#metadata_label {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                font-weight: normal !important;
                background: transparent !important;
            }}
            
            /* Separator styling */
            BuildProjectPanel QLabel#section_divider {{
                background-color: {theme['separator']} !important;
                height: 2px !important;
                margin: 8px 0px !important;
            }}
            
            /* Input styling - responsive and modern */
            BuildProjectPanel QLineEdit,
            BuildProjectPanel QLineEdit:hover,
            BuildProjectPanel QLineEdit:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 120px !important;
            }}
            
            BuildProjectPanel QLineEdit:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            BuildProjectPanel QLineEdit:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* Project name combo box styling */
            BuildProjectPanel QComboBox#project_name_input {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 150px !important;
            }}
            
            BuildProjectPanel QComboBox#project_name_input:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            BuildProjectPanel QComboBox#project_name_input:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            BuildProjectPanel QComboBox#project_name_input::drop-down {{
                border: none !important;
                width: 24px !important;
            }}
            
            BuildProjectPanel QComboBox#project_name_input::down-arrow {{
                image: none !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid {theme['text_primary']} !important;
                margin-right: 6px !important;
            }}
            
            BuildProjectPanel QComboBox#project_name_input QAbstractItemView {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                selection-background-color: {theme['button_bg']} !important;
                selection-color: {theme['text_light']} !important;
                padding: 4px !important;
            }}
            
            /* Metadata input fields styling */
            BuildProjectPanel QLineEdit#project_name_input,
            BuildProjectPanel QLineEdit#version_input,
            BuildProjectPanel QLineEdit#author_input,
            BuildProjectPanel QLineEdit#description_input {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 120px !important;
            }}
            
            BuildProjectPanel QLineEdit#project_name_input:hover,
            BuildProjectPanel QLineEdit#version_input:hover,
            BuildProjectPanel QLineEdit#author_input:hover,
            BuildProjectPanel QLineEdit#description_input:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            BuildProjectPanel QLineEdit#project_name_input:focus,
            BuildProjectPanel QLineEdit#version_input:focus,
            BuildProjectPanel QLineEdit#author_input:focus,
            BuildProjectPanel QLineEdit#description_input:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            /* ComboBox styling - responsive resizing */
            BuildProjectPanel QComboBox,
            BuildProjectPanel QComboBox:hover,
            BuildProjectPanel QComboBox:focus {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 4px !important;
                padding: 6px 8px !important;
                font-size: 11px !important;
                margin: 0px !important;
                font-weight: normal !important;
                min-width: 120px !important;
            }}
            
            BuildProjectPanel QComboBox:hover {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            BuildProjectPanel QComboBox:focus {{
                border-color: {theme['input_focus']} !important;
                background-color: {theme['input_bg']} !important;
            }}
            
            BuildProjectPanel QComboBox::drop-down {{
                border: none !important;
                width: 24px !important;
            }}
            
            BuildProjectPanel QComboBox::down-arrow {{
                image: none !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid {theme['text_primary']} !important;
                margin-right: 6px !important;
            }}
            
            BuildProjectPanel QComboBox QAbstractItemView {{
                background-color: {theme['input_bg']} !important;
                color: {theme['text_primary']} !important;
                border: 2px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                selection-background-color: {theme['button_bg']} !important;
                selection-color: {theme['text_light']} !important;
                padding: 4px !important;
            }}
            
            /* CheckBox styling - transparent background */
            BuildProjectPanel QCheckBox {{
                color: {theme['text_primary']} !important;
                font-size: 11px !important;
                spacing: 8px !important;
                padding: 2px 0px !important;
                background: transparent !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            BuildProjectPanel QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                border: 2px solid {theme['input_border']} !important;
                background-color: {theme['input_bg']} !important;
                border-radius: 3px !important;
            }}
            
            BuildProjectPanel QCheckBox::indicator:checked {{
                background-color: {theme['button_bg']} !important;
                border-color: {theme['button_bg']} !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=) !important;
            }}
            
            BuildProjectPanel QCheckBox:hover::indicator:unchecked {{
                border-color: {theme['button_hover']} !important;
                background-color: {theme['bg_secondary']} !important;
            }}
            
            /* Progress Bar styling */
            BuildProjectPanel QProgressBar#build_progress_bar {{
                border: 1px solid {theme['input_border']} !important;
                border-radius: 6px !important;
                text-align: center !important;
                font-size: 11px !important;
                color: {theme['text_primary']} !important;
                background-color: {theme['input_bg']} !important;
                margin: 0px !important;
                font-weight: normal !important;
            }}
            
            BuildProjectPanel QProgressBar#build_progress_bar::chunk {{
                background-color: {theme['button_bg']} !important;
                border-radius: 4px !important;
            }}
            
            /* Button styling - unified gradient system with responsive sizing */
            BuildProjectPanel QPushButton,
            BuildProjectPanel QPushButton:hover,
            BuildProjectPanel QPushButton:pressed,
            BuildProjectPanel QPushButton:disabled {{
                border: none !important;
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 11px !important;
                font-weight: bold !important;
                min-height: 16px !important;
                margin: 2px 4px !important;
            }}
            
            BuildProjectPanel QPushButton:disabled {{
                background-color: {theme['text_secondary']} !important;
                color: {theme['text_secondary']} !important;
                opacity: 0.6 !important;
            }}
            
            /* Success action buttons */
            BuildProjectPanel QPushButton[btnType="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['success_color']}, stop:1 {theme['success_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['success_color']} !important;
                padding: 6px 12px !important;
            }}
            
            BuildProjectPanel QPushButton[btnType="success"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #82e0aa, stop:0.5 #58d68d, stop:1 #2ecc71) !important;
                border: 2px solid #a9dfbf !important;
                color: #ffffff !important;
                padding: 7px 13px !important;
            }}
            
            BuildProjectPanel QPushButton[btnType="success"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954) !important;
                border: 2px solid #1e8449 !important;
                color: #ffffff !important;
                padding: 8px 14px !important;
            }}
            
            /* Uninstall/Danger buttons */
            BuildProjectPanel QPushButton[btnType="uninstall"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                color: {theme['text_light']} !important;
                border: 1px solid {theme['error_color']} !important;
                padding: 6px 12px !important;
            }}
            
            BuildProjectPanel QPushButton[btnType="uninstall"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:0.5 #e74c3c, stop:1 #c0392b) !important;
                border: 2px solid #f1948a !important;
                color: #ffffff !important;
            }}
            
            BuildProjectPanel QPushButton[btnType="uninstall"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme['error_color']}, stop:1 {theme['error_color']}) !important;
                border: 1px solid {theme['error_color']} !important;
                opacity: 0.8 !important;
            }}
            
            /* Secondary button - Gray theme */
            BuildProjectPanel QPushButton[btnType="secondary"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268) !important;
                color: {theme['text_light']} !important;
                border: 1px solid #5a6268 !important;
            }}
            BuildProjectPanel QPushButton[btnType="secondary"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #868e96, stop:1 #6c757d) !important;
                border: 1px solid #868e96 !important;
            }}
            BuildProjectPanel QPushButton[btnType="secondary"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6268, stop:1 #495057) !important;
                border: 1px solid #495057 !important;
            }}
            

            

        """)
    


#----------Legacy CLI Functions (for backward compatibility)----------
def choose_build_mode():
    cprint("=== Choose Build Mode ===", Fore.LIGHTCYAN_EX)
    print("  1. Debug\n  2. Release\n  3. Releasedbg\n  m. Return to menu")
    mode = input("Choose a build type [Default: 2]: ").strip().lower()
    if mode == "m":
        return "__menu__"
    return { "1": "debug", "2": "release", "3": "releasedbg" }.get(mode or "2", "release")

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
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=creationflags)
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
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        proc = subprocess.Popen(["cmd", "/c", tf_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=creationflags)
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
