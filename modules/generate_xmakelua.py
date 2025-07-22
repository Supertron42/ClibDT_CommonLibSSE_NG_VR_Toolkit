import os
from pathlib import Path

def generate_xmake_lua(output_path, project_name, version, author, description):
    """
    Generate a xmake.lua file at output_path using the provided metadata.
    """
    content = f'''-- Auto-generated xmake.lua

set_xmakever("3.0.1")
includes("lib/commonlibsse-ng")

set_project("{project_name}")
set_version("{version}")
set_license("GPL-3.0")

set_languages("c++23")
set_warnings("allextra")
set_policy("package.requires_lock", true)
set_toolset("msvc", "ninja")

add_rules("mode.debug", "mode.releasedbg", "mode.release")

option("skyrim_se")
    set_default(false)
    set_showmenu(true)
    set_description("Build for Skyrim Special Edition")
option_end()

option("skyrim_ae")
    set_default(false)
    set_showmenu(true)
    set_description("Build for Skyrim Anniversary Edition")
option_end()

option("skyrim_vr")
    set_default(false)
    set_showmenu(true)
    set_description("Build for Skyrim VR only")
option_end()

if has_config("skyrim_vr") and (has_config("skyrim_se") or has_config("skyrim_ae")) then
    raise("Cannot combine Skyrim VR with SE/AE builds. Enable only one configuration.")
end

target("{project_name}")
    add_deps("commonlibsse-ng")

    local runtime = "se_ae"
    if has_config("skyrim_vr") then
        runtime = "vr"
    elseif has_config("skyrim_ae") and not has_config("skyrim_se") then
        runtime = "ae"
    elseif has_config("skyrim_se") and not has_config("skyrim_ae") then
        runtime = "se"
    end

    add_rules("commonlibsse-ng.plugin", {{
        name        = "{project_name}",
        author      = "{author}",
        description = "{description}",
        runtime     = runtime
    }})

    add_files("src/**.cpp")
    add_headerfiles("src/**.h")

    add_includedirs(
        "src",
        "$(projectdir)",
        "$(projectdir)/ClibUtil",
        "$(projectdir)/ClibUtil/detail",
        "$(projectdir)/xbyak"
    )

    set_pcxxheader("src/pch.h")

    if has_config("skyrim_vr") then
        add_defines("ENABLE_SKYRIM_VR")
    elseif has_config("skyrim_se") and not has_config("skyrim_ae") then
        add_defines("ENABLE_SKYRIM_SE")
    elseif has_config("skyrim_ae") and not has_config("skyrim_se") then
        add_defines("ENABLE_SKYRIM_AE")
    else
        add_defines("ENABLE_SKYRIM_SE")
        add_defines("ENABLE_SKYRIM_AE")
    end
'''
    output_path = Path(output_path)
    output_path.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    print("=== xmake.lua Generator ===")
    project_name = input("Project name: ").strip() or "MyProject"
    version = input("Version [1.0.0]: ").strip() or "1.0.0"
    author = input("Author [Unknown]: ").strip() or "Unknown"
    description = input("Description [No description provided.]: ").strip() or "No description provided."
    output_path = input("Output path [xmake.lua]: ").strip() or "xmake.lua"
    generate_xmake_lua(output_path, project_name, version, author, description)
    print(f"[OK] xmake.lua generated at {output_path}") 