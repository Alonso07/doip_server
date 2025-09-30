#!/usr/bin/env python3
"""
Generate PyInstaller spec file dynamically
This script creates a PyInstaller spec file based on the current project structure
"""

import os
import sys
from pathlib import Path


def generate_spec_file(project_root, output_path):
    """Generate PyInstaller spec file for DoIP Server"""

    # Define the main entry point
    main_script = os.path.join(project_root, "src", "doip_server", "main.py")

    # Define data files to include
    config_files = [
        (os.path.join(project_root, "config"), "config"),
    ]

    # Define hidden imports (dependencies that PyInstaller might miss)
    hidden_imports = [
        "yaml",
        "doipclient",
        "psutil",
        "doip_server",
        "doip_server.doip_server",
        "doip_server.hierarchical_config_manager",
        "doip_client",
        "doip_client.doip_client",
        "doip_client.debug_client",
        "doip_client.udp_doip_client",
    ]

    # Define excludes (packages to exclude to reduce size)
    excludes = [
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "wx",
        "IPython",
        "jupyter",
        "notebook",
        "sphinx",
        "pytest",
        "pytest-cov",
        "flake8",
        "black",
        "bandit",
        "safety",
        "build",
        "twine",
    ]

    # Generate spec file content
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for DoIP Server
Generated dynamically by generate_spec.py
Creates cross-platform executables for Windows, macOS, and Linux
"""

import os
import sys
from pathlib import Path

# Get the project root directory (current working directory)
project_root = os.getcwd()

# Define the main entry point
main_script = os.path.join(project_root, 'src', 'doip_server', 'main.py')

# Define data files to include
config_files = [
    (os.path.join(project_root, 'config'), 'config'),
]

# Define hidden imports (dependencies that PyInstaller might miss)
hidden_imports = {hidden_imports}

# Define excludes (packages to exclude to reduce size)
excludes = {excludes}

# Analysis configuration
a = Analysis(
    [main_script],
    pathex=[project_root],
    binaries=[],
    datas=config_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create single executable file (onefile mode)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='doip_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
    onefile=True,  # Create single executable file
)
'''

    # Write spec file
    with open(output_path, "w") as f:
        f.write(spec_content)

    print(f"Generated PyInstaller spec file: {output_path}")


def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python generate_spec.py <project_root> <output_path>")
        sys.exit(1)

    project_root = sys.argv[1]
    output_path = sys.argv[2]

    generate_spec_file(project_root, output_path)


if __name__ == "__main__":
    main()
