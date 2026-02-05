"""
Module Size Monitor

Tracks Python module sizes and alerts on violations.

Module Size Guidelines:
- Target: <400 lines (Ideal)
- Acceptable: 400-600 lines (OK, monitor growth)
- Warning: 600-800 lines (At the limit)
- Critical: >800 lines (MUST refactor)

Module Size Target: <400 lines (Current: ~220 lines)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


logger = logging.getLogger(__name__)


class ModuleSizeViolation:
    """Represents a module size violation."""

    def __init__(self, file_path: Path, line_count: int, threshold: int, severity: str):
        self.file_path = file_path
        self.line_count = line_count
        self.threshold = threshold
        self.severity = severity  # "warning" or "critical"

    def __repr__(self):
        return (
            f"ModuleSizeViolation({self.file_path.name}, "
            f"{self.line_count} lines, {self.severity})"
        )


class ModuleMonitor:
    """
    Monitors Python module sizes and reports violations.

    Thresholds:
    - warning_threshold: Module approaching limit (default 600)
    - critical_threshold: Module exceeds limit (default 800)

    Usage:
        monitor = ModuleMonitor(Path.cwd())
        violations = monitor.check_all_modules()
        if violations:
            for v in violations:
                print(f"{v.file_path}: {v.line_count} lines ({v.severity})")
    """

    def __init__(
        self,
        project_root: Path,
        warning_threshold: int = 600,
        critical_threshold: int = 800,
        exclude_patterns: List[str] = None
    ):
        """
        Initialize module monitor.

        Args:
            project_root: Root directory to monitor
            warning_threshold: Lines before warning
            critical_threshold: Lines before critical alert
            exclude_patterns: Patterns to exclude (e.g., [".venv", "tests"])
        """
        self.project_root = project_root
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.exclude_patterns = exclude_patterns or [
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "build",
            "dist",
        ]

        logger.info(f"Module monitor initialized: {project_root}")
        logger.info(f"Thresholds: warning={warning_threshold}, critical={critical_threshold}")

    def count_lines(self, file_path: Path) -> int:
        """
        Count lines in a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Number of lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.error(f"Error counting lines in {file_path}: {e}")
            return 0

    def should_exclude(self, file_path: Path) -> bool:
        """
        Check if file should be excluded.

        Args:
            file_path: Path to check

        Returns:
            True if should exclude
        """
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.exclude_patterns)

    def find_python_files(self) -> List[Path]:
        """
        Find all Python files in project.

        Returns:
            List of Python file paths
        """
        files = []
        for py_file in self.project_root.rglob("*.py"):
            if not self.should_exclude(py_file):
                files.append(py_file)
        return files

    def check_module(self, file_path: Path) -> Tuple[int, Optional[ModuleSizeViolation]]:
        """
        Check a single module.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (line_count, violation or None)
        """
        line_count = self.count_lines(file_path)

        if line_count >= self.critical_threshold:
            violation = ModuleSizeViolation(
                file_path, line_count, self.critical_threshold, "critical"
            )
            return line_count, violation

        if line_count >= self.warning_threshold:
            violation = ModuleSizeViolation(
                file_path, line_count, self.warning_threshold, "warning"
            )
            return line_count, violation

        return line_count, None

    def check_all_modules(self) -> List[ModuleSizeViolation]:
        """
        Check all Python modules.

        Returns:
            List of violations (empty if all OK)
        """
        violations = []
        files = self.find_python_files()

        logger.debug(f"Checking {len(files)} Python files...")

        for file_path in files:
            _, violation = self.check_module(file_path)
            if violation:
                violations.append(violation)

        if violations:
            logger.warning(f"Found {len(violations)} module size violations")
        else:
            logger.debug("No module size violations found")

        return violations

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get module size statistics.

        Returns:
            Dictionary with statistics
        """
        files = self.find_python_files()
        line_counts = []
        violations = []

        for file_path in files:
            line_count, violation = self.check_module(file_path)
            line_counts.append((file_path, line_count))
            if violation:
                violations.append(violation)

        # Sort by size
        line_counts.sort(key=lambda x: x[1], reverse=True)

        stats = {
            "total_modules": len(files),
            "average_size": sum(lc for _, lc in line_counts) // len(line_counts) if line_counts else 0,
            "largest_module": str(line_counts[0][0].name) if line_counts else "N/A",
            "largest_size": line_counts[0][1] if line_counts else 0,
            "violations": len(violations),
            "critical_violations": sum(1 for v in violations if v.severity == "critical"),
            "warning_violations": sum(1 for v in violations if v.severity == "warning"),
        }

        return stats

    def generate_report(self) -> str:
        """
        Generate a text report of module sizes.

        Returns:
            Multi-line report string
        """
        violations = self.check_all_modules()
        stats = self.get_statistics()

        lines = [
            "=" * 70,
            "MODULE SIZE REPORT",
            "=" * 70,
            f"Project: {self.project_root}",
            f"Total modules: {stats['total_modules']}",
            f"Average size: {stats['average_size']} lines",
            f"Largest module: {stats['largest_module']} ({stats['largest_size']} lines)",
            "",
            f"Violations: {stats['violations']}",
            f"  Critical (>{self.critical_threshold}): {stats['critical_violations']}",
            f"  Warning ({self.warning_threshold}-{self.critical_threshold}): {stats['warning_violations']}",
        ]

        if violations:
            lines.append("")
            lines.append("VIOLATIONS:")
            lines.append("-" * 70)
            for v in sorted(violations, key=lambda x: x.line_count, reverse=True):
                severity_mark = "❌" if v.severity == "critical" else "⚠️"
                lines.append(f"{severity_mark} {v.file_path.name}: {v.line_count} lines ({v.severity})")

        lines.append("=" * 70)

        return "\n".join(lines)
