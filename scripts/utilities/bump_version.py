#!/usr/bin/env python3
"""
Version bumping script for doip-server package
Usage: python bump_version.py [major|minor|patch]
"""

import sys
import re
import subprocess
from pathlib import Path


def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    return match.group(1)


def bump_version(version, bump_type):
    """Bump version based on type"""
    parts = version.split(".")
    if len(parts) != 3:
        print(f"Error: Invalid version format: {version}")
        sys.exit(1)

    major, minor, patch = map(int, parts)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Error: Invalid bump type: {bump_type}")
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def update_pyproject_toml(new_version):
    """Update version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Replace version line
    new_content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)

    pyproject_path.write_text(new_content)
    print(f"Updated pyproject.toml: {new_version}")


def main():
    """Main function to handle version bumping."""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1]
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)

    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")

    # Confirm with user
    confirm = input(f"Bump version to {new_version}? (y/N): ")
    if confirm.lower() not in ["y", "yes"]:
        print("Version bump cancelled")
        sys.exit(0)

    # Update pyproject.toml
    update_pyproject_toml(new_version)

    # Run tests
    print("Running tests...")
    result = subprocess.run(
        ["poetry", "run", "pytest", "tests/", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("Error: Tests failed. Please fix tests before bumping version.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

    print("✅ All tests passed!")
    print(f"✅ Version bumped to {new_version}")
    print("\nNext steps:")
    print(
        f"1. Commit changes: git add pyproject.toml && "
        f"git commit -m 'Bump version to {new_version}'"
    )
    print(f"2. Create tag: git tag v{new_version}")
    print("3. Push changes: git push origin main --tags")
    print("4. Publish: ./publish_to_pypi.sh")


if __name__ == "__main__":
    main()
