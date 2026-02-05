#!/usr/bin/env python
"""
Parent CC Setup Script

Initialize a new Parent CC instance from this template.

Usage:
    python setup.py \
      --name Test_App_PCC \
      --location /A_Coding/Test_App_PCC \
      --github-repo https://github.com/SilverWizardAI/Test_App_PCC
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime


def setup_parent_cc(
    name: str,
    location: str,
    github_repo: str = "",
    mm_proxy_url: str = "http://localhost:6001"
):
    """
    Set up new Parent CC instance from template.

    Args:
        name: Parent CC name
        location: Folder location for Parent CC
        github_repo: Optional GitHub repository URL
        mm_proxy_url: MM mesh proxy URL
    """
    print(f"Setting up Parent CC: {name}")
    print(f"Location: {location}")

    # Get template directory (this file's directory)
    template_dir = Path(__file__).parent

    # Create destination
    dest_dir = Path(location)

    if dest_dir.exists():
        print(f"Error: Destination already exists: {dest_dir}")
        sys.exit(1)

    # Copy template
    print("Copying template...")
    shutil.copytree(template_dir, dest_dir)

    # Remove setup.py from destination (don't need it in instance)
    (dest_dir / "setup.py").unlink(missing_ok=True)

    # Customize CLAUDE.md
    print("Customizing configuration...")
    claude_md = dest_dir / ".claude" / "CLAUDE.md"
    content = claude_md.read_text()
    content = content.replace("{PCC_FOLDER_PATH}", str(dest_dir))
    content = content.replace("{PCC_NAME}", name)
    claude_md.write_text(content)

    # Customize settings.json
    settings_json = dest_dir / ".claude" / "settings.json"
    settings = json.loads(settings_json.read_text())
    settings["folder_scope"] = str(dest_dir)
    with open(settings_json, 'w') as f:
        json.dump(settings, f, indent=2)

    # Customize app_registry.json
    registry_json = dest_dir / "app_registry.json"
    registry = json.loads(registry_json.read_text())
    registry["pcc_name"] = name
    registry["pcc_folder"] = str(dest_dir)
    registry["created"] = datetime.now().isoformat()
    registry["mm_mesh"]["pcc_service_name"] = f"{name.lower()}_parent_cc"
    registry["mm_mesh"]["proxy_url"] = mm_proxy_url
    with open(registry_json, 'w') as f:
        json.dump(registry, f, indent=2)

    # Create subdirectories
    (dest_dir / "apps").mkdir(exist_ok=True)
    (dest_dir / "logs").mkdir(exist_ok=True)

    # Initialize git if requested
    if github_repo:
        print("Initializing git repository...")
        import subprocess

        subprocess.run(["git", "init"], cwd=dest_dir, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", github_repo],
            cwd=dest_dir,
            check=True
        )

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=dest_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Initial commit: {name} Parent CC"],
            cwd=dest_dir,
            check=True
        )

        print(f"✓ Git initialized with remote: {github_repo}")

    print(f"\n✓ Parent CC created: {dest_dir}")
    print(f"\nNext steps:")
    print(f"  cd {dest_dir}")
    print(f"  claude code")
    print(f"\nThe Parent CC will have full autonomy within {dest_dir}")

    return dest_dir


def main():
    parser = argparse.ArgumentParser(
        description="Set up new Parent CC instance"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Parent CC name (e.g., Test_App_PCC)"
    )
    parser.add_argument(
        "--location",
        required=True,
        help="Folder location (e.g., /A_Coding/Test_App_PCC)"
    )
    parser.add_argument(
        "--github-repo",
        default="",
        help="Optional GitHub repository URL"
    )
    parser.add_argument(
        "--mm-proxy-url",
        default="http://localhost:6001",
        help="MM mesh proxy URL (default: http://localhost:6001)"
    )

    args = parser.parse_args()

    try:
        setup_parent_cc(
            name=args.name,
            location=args.location,
            github_repo=args.github_repo,
            mm_proxy_url=args.mm_proxy_url
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
