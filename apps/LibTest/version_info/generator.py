"""
Build-time version information generator

This module generates a Python module containing version information
that can be imported at runtime. It reads from version.json and creates
_version_data.py with all build metadata.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class VersionGenerator:
    """Generates version data module from version.json"""

    def __init__(self, version_json_path: Optional[str] = None):
        """
        Initialize the version generator

        Args:
            version_json_path: Path to version.json file. If None, searches
                             in common locations.
        """
        self.version_json_path = self._find_version_json(version_json_path)
        self.version_data = self._load_version_json()

    def _find_version_json(self, provided_path: Optional[str]) -> Path:
        """
        Find version.json file

        Search order:
        1. Provided path
        2. ./version.json
        3. ../version.json
        4. Project root (if in git repo)
        """
        if provided_path:
            path = Path(provided_path)
            if path.exists():
                return path.resolve()
            raise FileNotFoundError(f"version.json not found at: {provided_path}")

        # Search common locations
        search_paths = [
            Path.cwd() / 'version.json',
            Path.cwd().parent / 'version.json',
        ]

        # Try to find git root
        try:
            current = Path.cwd()
            while current != current.parent:
                if (current / '.git').exists():
                    search_paths.insert(0, current / 'version.json')
                    break
                current = current.parent
        except:
            pass

        for path in search_paths:
            if path.exists():
                return path.resolve()

        raise FileNotFoundError(
            "version.json not found. Searched:\n" +
            "\n".join(f"  - {p}" for p in search_paths)
        )

    def _load_version_json(self) -> Dict[str, Any]:
        """Load and validate version.json"""
        try:
            with open(self.version_json_path, 'r') as f:
                data = json.load(f)

            # Validate required fields
            if 'version' not in data:
                raise ValueError("version.json must contain 'version' field")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.version_json_path}: {e}")

    def update_build_info(self, auto_increment: bool = True) -> Dict[str, Any]:
        """
        Update build number and timestamp

        Args:
            auto_increment: If True, increment build_number automatically

        Returns:
            Updated version data dictionary
        """
        now = datetime.now(timezone.utc)

        # Update build timestamp
        self.version_data['build_date'] = now.strftime('%Y-%m-%d')
        self.version_data['build_time'] = now.strftime('%H:%M:%S UTC')
        self.version_data['build_timestamp'] = now.strftime('%Y-%m-%d %H:%M:%S')
        self.version_data['build_timestamp_iso'] = now.isoformat()
        self.version_data['build_timestamp_unix'] = int(now.timestamp())

        # Update or initialize build number
        if auto_increment:
            current_build = self.version_data.get('build_number', 0)
            if isinstance(current_build, int):
                self.version_data['build_number'] = current_build + 1
            else:
                # Use timestamp-based build number (PIW style)
                self.version_data['build_number'] = int(now.timestamp()) - 1700000000

        # Save updated version.json
        with open(self.version_json_path, 'w') as f:
            json.dump(self.version_data, f, indent=2)

        return self.version_data

    def generate_version_module(
        self,
        output_path: Optional[str] = None,
        update_build: bool = True,
        auto_increment: bool = True,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate _version_data.py module

        Args:
            output_path: Where to write _version_data.py. If None, writes to
                        same directory as this module.
            update_build: If True, updates build number and timestamp
            auto_increment: If True, auto-increments build number
            extra_data: Additional key-value pairs to include in module

        Returns:
            Path to generated module
        """
        if update_build:
            self.update_build_info(auto_increment=auto_increment)

        # Determine output path
        if output_path:
            out_path = Path(output_path)
        else:
            out_path = Path(__file__).parent / '_version_data.py'

        # Merge extra data
        data = self.version_data.copy()
        if extra_data:
            data.update(extra_data)

        # Generate Python module content
        content = self._generate_module_content(data)

        # Write module
        with open(out_path, 'w') as f:
            f.write(content)

        print(f"✓ Generated version module: {out_path}")
        print(f"  Version: {data['version']}")
        print(f"  Build: {data.get('build_number', 'N/A')}")
        print(f"  Timestamp: {data.get('build_timestamp', 'N/A')}")

        return out_path.resolve()

    def _generate_module_content(self, data: Dict[str, Any]) -> str:
        """Generate Python module source code"""
        lines = [
            '"""',
            'Auto-generated version information module',
            '',
            'WARNING: This file is auto-generated during build.',
            'Do not edit manually - changes will be overwritten.',
            '',
            f'Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}',
            f'Source: {self.version_json_path}',
            '"""',
            '',
        ]

        # Add each field as a constant
        for key, value in sorted(data.items()):
            const_name = key.upper()

            if isinstance(value, str):
                lines.append(f'{const_name} = "{value}"')
            elif isinstance(value, (int, float)):
                lines.append(f'{const_name} = {value}')
            elif isinstance(value, bool):
                lines.append(f'{const_name} = {value}')
            elif isinstance(value, (dict, list)):
                import json
                lines.append(f'{const_name} = {json.dumps(value)}')
            else:
                lines.append(f'{const_name} = {repr(value)}')

        lines.append('')
        lines.append('# Dictionary representation')
        lines.append('VERSION_INFO = {')
        for key, value in sorted(data.items()):
            lines.append(f'    "{key}": {key.upper()},')
        lines.append('}')
        lines.append('')

        return '\n'.join(lines)


def generate_version_module(
    version_json_path: Optional[str] = None,
    output_path: Optional[str] = None,
    update_build: bool = True,
    auto_increment: bool = True,
    extra_data: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Convenience function to generate version module

    Args:
        version_json_path: Path to version.json file
        output_path: Where to write _version_data.py
        update_build: If True, updates build number and timestamp
        auto_increment: If True, auto-increments build number
        extra_data: Additional key-value pairs to include

    Returns:
        Path to generated module

    Example:
        # In your build script:
        from version_info.generator import generate_version_module

        generate_version_module(
            version_json_path='./version.json',
            extra_data={'theme_default': 'Dark'}
        )
    """
    generator = VersionGenerator(version_json_path)
    return generator.generate_version_module(
        output_path=output_path,
        update_build=update_build,
        auto_increment=auto_increment,
        extra_data=extra_data
    )


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate version information module'
    )
    parser.add_argument(
        'version_json',
        nargs='?',
        help='Path to version.json file (auto-detected if not provided)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output path for _version_data.py'
    )
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Do not update build number/timestamp'
    )
    parser.add_argument(
        '--no-increment',
        action='store_true',
        help='Do not auto-increment build number'
    )

    args = parser.parse_args()

    try:
        generate_version_module(
            version_json_path=args.version_json,
            output_path=args.output,
            update_build=not args.no_update,
            auto_increment=not args.no_increment
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
