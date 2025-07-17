import os
import subprocess
from colorama import init, Fore, Style
from pathlib import Path

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def run_git_commit():
    dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
    if not dev_root:
        cprint("[ERROR] XSE_CLIBDT_DEVROOT is not set. Cannot continue.", Fore.RED)
        input("Press Enter to return...")
        return

    #----------Automatic Git init----------
    cprint("  🔧 Initializing Git repository...", Fore.CYAN)
    subprocess.run(["git", "init"], capture_output=True, text=True)

    #----------Stage all changes----------
    cprint("  📝 Staging files...", Fore.CYAN)
    subprocess.run(["git", "add", "."], capture_output=True, text=True)

    #----------Check for staged changes----------
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:
        cprint("  💾 Ready to commit your changes.", Fore.CYAN)
        commit_msg = input("Enter a commit message [Default: Commit]: ").strip()
        if not commit_msg:
            commit_msg = "Commit"
        cprint(f"  💾 Creating commit: {commit_msg}", Fore.CYAN)
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        cprint("[OK] Changes committed successfully.", Fore.GREEN)
    else:
        cprint("[OK] No changes to commit. Working tree is clean.", Fore.GREEN)

    #----------Optionally launch GitHub Desktop----------
    def find_github_desktop():
        """Find GitHub Desktop installation in default or tools location"""
        # Check environment variable first
        gh_env_path = os.getenv("XSE_GITHUB_DESKTOP_PATH")
        if gh_env_path and Path(gh_env_path).exists():
            return gh_env_path
        
        #----------Check default installation path----------
        default_path = Path(os.getenv("LocalAppData", "")) / "GitHubDesktop" / "GitHubDesktop.exe"
        if default_path.exists():
            return str(default_path)
        
        #----------Check tools/GitHubDesktop path----------
        dev_root = os.getenv("XSE_CLIBDT_DEVROOT")
        if dev_root:
            tools_path = Path(dev_root) / "tools" / "GitHubDesktop" / "GitHubDesktop.exe"
            if tools_path.exists():
                return str(tools_path)
        
        return None

    gh_path = find_github_desktop()
    if gh_path:
        gh_exe = Path(gh_path)
        if gh_exe.exists():
            cprint("[OPTIONAL] Open GitHub Desktop to review or push?", Fore.CYAN)
            open_gh = input("Open GitHub Desktop now? (Y/N): ").strip().lower()
            if open_gh == "m":
                return
            if open_gh == "y" or open_gh == "":
                cprint("  🚀 Launching GitHub Desktop...", Fore.CYAN)
                subprocess.Popen([str(gh_exe)])
            else:
                cprint("[INFO] Skipped opening GitHub Desktop.", Fore.LIGHTBLACK_EX)
        else:
            cprint("[WARNING] GitHub Desktop path found, but GitHubDesktop.exe was not found:", Fore.RED)
            print(f"  {gh_path}")
    else:
        cprint("[INFO] GitHub Desktop not found in any location. Skipping.", Fore.YELLOW)

    print()
    cprint("[OK] Git commit helper finished.", Fore.GREEN)
    input("Press Enter to return...")

if __name__ == "__main__":
    run_git_commit()
