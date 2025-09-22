# Publishing Scripts Troubleshooting Guide

## Problem: Scripts only work in Cursor terminal

The `publish*.sh` scripts should work in any terminal, but there are several common issues that can cause them to fail in other terminals.

## Root Causes

### 1. **Working Directory Issues**
- **Problem**: Scripts expect to be run from the project root directory
- **Solution**: Always run scripts from the project root, or use the new `run_publish.sh` launcher

### 2. **PATH Environment Differences**
- **Problem**: Different terminals may have different PATH configurations
- **Solution**: The `run_publish.sh` script automatically adds common Poetry paths

### 3. **Shell Configuration Differences**
- **Problem**: Different terminals load different shell configs (`.zshrc`, `.bashrc`, etc.)
- **Solution**: Use the universal launcher which sets up the environment explicitly

## Solutions

### Option 1: Use the Universal Launcher (Recommended)
```bash
# This works from any directory and any terminal
./run_publish.sh
```

### Option 2: Fix PATH Issues
Add Poetry to your shell configuration:

**For Zsh** (add to `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**For Bash** (add to `~/.bashrc` or `~/.bash_profile`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Option 3: Use Absolute Paths
```bash
# Instead of: ./publish.sh
# Use: /full/path/to/doip_server/publish.sh
```

## Testing Your Setup

### Test 1: Check Poetry Installation
```bash
which poetry
# Should return: ~/.local/bin/poetry (or similar path)
```

### Test 2: Check Working Directory
```bash
pwd
# Should be: /path/to/doip_server
ls pyproject.toml
# Should show: pyproject.toml
```

### Test 3: Test Universal Launcher
```bash
# From any directory
/path/to/doip_server/run_publish.sh
```

## Common Error Messages and Solutions

### "pyproject.toml not found"
- **Cause**: Not in the project root directory
- **Solution**: `cd` to the project directory or use `run_publish.sh`

### "Poetry is not installed"
- **Cause**: Poetry not in PATH
- **Solution**: Install Poetry or add it to PATH

### "command not found: poetry"
- **Cause**: PATH doesn't include Poetry location
- **Solution**: Use `run_publish.sh` or fix PATH

## Environment Variables

The scripts check these locations for Poetry:
- `$HOME/.local/bin/poetry`
- `/opt/homebrew/bin/poetry`
- `/usr/local/bin/poetry`
- Any location in `$PATH`

## Debug Information

To debug issues, run:
```bash
echo "PATH: $PATH"
echo "SHELL: $SHELL"
echo "PWD: $(pwd)"
which poetry
poetry --version
```
