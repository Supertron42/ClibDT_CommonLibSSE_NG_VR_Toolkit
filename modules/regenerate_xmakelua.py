import os
import sys
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL)

def prompt_input(message, default=None):
    value = input(message + " ").strip()
    if value.lower() == "m":
        cprint("[INFO] Returning to main menu...", Fore.LIGHTBLACK_EX)
        return None
    return value or default

def run_regenerate_xmake():
    print()
    cprint("[INFO] This tool will regenerate your xmake.lua based on metadata you provide.", Fore.YELLOW)
    cprint("       Use this to refresh old projects or prepare new folders.\n", Fore.LIGHTBLACK_EX)

    #----------Use current working directory as the target path----------
    target_path = Path.cwd()
    cprint(f"[OK] Target folder: {target_path}", Fore.GREEN)

    #----------COLLECT METADATA----------
    print()
    cprint("#=== Provide Plugin Metadata ===", Fore.CYAN + Style.BRIGHT)

    default_name = target_path.name  #----------Use folder name as default----------
    plugin_name = prompt_input(f"Project name (no spaces) [Default: {default_name}]:", default_name)
    if plugin_name is None:
        return
    version     = prompt_input("Version number [Default: 1.0.0]:", "1.0.0")
    if version is None:
        return
    author      = prompt_input("Author name [Default: Unknown]:", "Unknown")
    if author is None:
        return
    description = prompt_input("Short description [Default: No description provided.]:", "No description provided.")
    if description is None:
        return

    #----------GENERATE----------
    print()
    cprint("#=== Generating xmake.lua ===", Fore.CYAN + Style.BRIGHT)

    try:
        from modules.generate_xmakelua import generate_xmake_lua
        #----------Ensure all metadata is not None----------
        if None in (plugin_name, version, author, description):
            cprint("[CANCELLED] Metadata entry was skipped. xmake.lua not generated.", Fore.LIGHTBLACK_EX)
            return
        generate_xmake_lua(target_path / "xmake.lua", plugin_name, version, author, description)
        cprint(f"[SUCCESS] xmake.lua created at: {target_path / 'xmake.lua'}", Fore.GREEN)
    except Exception as e:
        cprint(f"[ERROR] Failed to generate xmake.lua: {e}", Fore.RED)

    print()
    input("All done! Press Enter to return...")
