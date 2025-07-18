# 🛠️ ClibDT - CommonLibSSE-NG Developers Toolkit

A complete Windows-based developer toolkit for creating, building, and managing **Skyrim SKSE plugin projects** using [CommonLibSSE-NG] with [xmake].
All requirements are either done for you, or installed step-by-step with clear instructions.

This tool is intended to be a complete environment creation, and project building tool so you can just focus on coding.

If you are interested in making your own SKSE Skyrim mods, you're in the right place.

---

## 📦 What This Tool Does

- Installs everything you need to start modding Skyrim with SKSE plugins
- Helps you create projects with proper structure and `xmake.lua`
- Builds your plugin (SE/AE/VR) with runtime-safe settings
- Manages Git version control
- Automatically sets system environment variables
- And more...

---

## 📩 Download Executable

- Install from `https://www.nexusmods.com/skyrimspecialedition/mods/154240`

---

## 📩 How To Run with Python
Do this if you don't want to use the Windows executable. 

- Install Python
- run `install packages.bat`
- run ClibDT.py

---

## 🧰 Requirements

- Windows 10 or later

---

## 🚀 Getting Started

1. Run `ClibDT.exe`
2. Follow the menu-driven setup
3. Create your project and build your plugin

---

## 📖 Menu Options Explained

### **1. Set Environment Variables (required)**
Guides you through setting up the key folders and paths used by the toolkit:
- Where your dev projects live
- Where your Skyrim game folder (or SKSE) lives
- Where you want to create your mod to

**You must do this first!**

---

### **2. Install VS (or Build Tools), Git, Xmake, GitHub Desktop, Ninja**
Downloads and installs all the developer tools you need:
- Visual Studio 2022 Community or Build Tools (for compiling)
- Git for Windows (version control)
- Xmake (build system)
- GitHub Desktop (optional, for GUI git)

You can skip any tool you already have previously installed.

---

### **3. Create a New Project**
Creates a ready-to-build SKSE plugin project:
- Prompts for project name, author, version
- Sets up folders and a starter `xmake.lua`
- Supports SE, AE, and VR builds

---

### **4. Update Project Dependencies**
Keeps your project up to date:
- Updates Xmake package index
- Optionally upgrades all required packages

Use this after editing `xmake.lua` or to upgrade libraries.

---

### **5. Build Project (Debug or Release)**
Compiles your plugin using Xmake:
- Choose Debug or Release mode
- Detects runtime settings (SE, AE, VR)
- Shows build progress and output

---

### **6. Regenerate xmake.lua**
Regenerates your project’s `xmake.lua`:
- Updates name, version, author, description
- Ensures correct runtime logic and macros

Use if you want to reset or update your build script.

---

### **7. Git Stage & Commit Project**
Helps you manage version control:
- Initializes a Git repository (if needed)
- Stages all changes
- Prompts for a commit message
- Optionally launches GitHub Desktop

---

### **8. Detach Git (Remove History)**
Removes the `.git` folder from your project:
- Permanently deletes all Git commit history and tracking
- Useful if you cloned a template and want to start fresh

---

### **9. Smart Backup Dev Folder**
Creates a safe backup of your entire dev root:
- Backs up all projects and settings
- Useful before major changes or upgrades

---

### **10. Refresh Existing Project**
Refreshes your project folder:
- Cleans up temporary files and folders
- Ensures your project structure is up to date
- Useful if you’ve made manual changes or want to reset the workspace

---

### **11. Clear Environment Variables**
Removes all ClibDT-related environment variables for this session:
- Lets you reset or reconfigure your environment safely
- Only affects the current session (does not change system-wide settings)
- Prompts for confirmation and lists all variables to be removed

---

### **0. Exit**
Closes the program.

---

## 🔗 Extra Features

- Press `P` at any time to open the NexusMods page:
  [Supertron Nexus Page](https://www.nexusmods.com/skyrimspecialedition/mods/154240)
- Auto-checks for updates (if online)

---

## 📁 Project Layout Example

```
MyPlugin/
├── xmake.lua
├── src/
│   ├── main.cpp
│   └── pch.h
├── ClibUtil/
├── xbyak/
└── .git/
```

---

## 🛠 Build Tips

- To build your plugin, just select option 5 from the menu.
- Use SE, AE, or VR build targets — mix/match is supported safely..

---

## 🧃 Support

Found a bug or have a suggestion? 
Open an issue on GitHub or comment/message me via [NexusMods](https://www.nexusmods.com/skyrimspecialedition/mods/154240).

---

## 📜 License

ClibDT Source License v1.0 © 2025 Supertron  
All bundled components retain their own licenses (e.g., CommonLibSSE-NG, Xmake)

---

## 📝 Credits & Third-Party Licenses

This toolkit bundles or assists with the installation of several third-party tools. All trademarks and copyrights are the property of their respective owners.

- **7-Zip**
  - [https://www.7-zip.org/](https://www.7-zip.org/)
  - Igor Pavlov
  - Licensed under the GNU LGPL v2.1
  - See LICENSE.txt in the 7-Zip distribution or [7-Zip License](https://www.7-zip.org/license.txt)

- **Xmake**
  - [https://xmake.io/](https://xmake.io/)
  - ruki (xmake authors)
  - Licensed under the Apache License 2.0

- **Git for Windows**
  - [https://gitforwindows.org/](https://gitforwindows.org/)
  - The Git Development Community
  - Licensed under GPL v2

- **GitHub Desktop**
  - [https://desktop.github.com/](https://desktop.github.com/)
  - GitHub, Inc.
  - Licensed under MIT License

- **Ninja Build System**
  - [https://ninja-build.org/](https://ninja-build.org/)
  - Evan Martin
  - Licensed under Apache License 2.0

- **CommonLibSSE-NG**
  - [https://github.com/alandtse/CommonLibVR)
  - Ryan McKenzie and contributors
  - Licensed under MIT License

If you use this toolkit, please respect the licenses of all bundled and third-party tools. See their respective websites and license files for more information.

---
