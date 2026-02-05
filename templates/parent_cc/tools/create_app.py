"""
Create App from Template

Creates new applications from Silver Wizard templates.

Module Size Target: <400 lines (Current: ~320 lines)
"""

import json
import logging
import shutil
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .registry import AppRegistry


logger = logging.getLogger(__name__)


TEMPLATES = {
    "pyqt_app": {
        "path": "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/templates/pyqt_app",
        "description": "PyQt6 application with MM mesh and Parent CC support",
        "files_to_customize": [
            "version.json",
            "__init__.py",
            "README.md"
        ]
    }
}


def create_app_from_template(
    app_name: str,
    template_type: str,
    pcc_folder: Path,
    features: Optional[List[str]] = None,
    registry_path: Optional[Path] = None
) -> Path:
    """
    Create new app from template.

    Args:
        app_name: Name of the app to create
        template_type: Template type (pyqt_app, etc.)
        pcc_folder: Parent CC folder path
        features: Optional list of features to include
        registry_path: Path to app registry

    Returns:
        Path to created app folder

    Example:
        create_app_from_template(
            app_name="TestApp1",
            template_type="pyqt_app",
            pcc_folder=Path("/A_Coding/Test_App_PCC"),
            features=["counter", "parent_cc_client"]
        )
    """
    logger.info(f"Creating app '{app_name}' from template '{template_type}'")

    # Validate template
    if template_type not in TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_type}. "
            f"Available: {', '.join(TEMPLATES.keys())}"
        )

    template_info = TEMPLATES[template_type]
    template_path = Path(template_info["path"])

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Create app folder
    apps_folder = pcc_folder / "apps"
    apps_folder.mkdir(exist_ok=True)

    app_folder = apps_folder / app_name

    if app_folder.exists():
        raise FileExistsError(f"App folder already exists: {app_folder}")

    # Copy template
    logger.info(f"Copying template from {template_path}")
    shutil.copytree(template_path, app_folder)

    # Customize app
    _customize_app(app_folder, app_name, features or [])

    # Create version.json
    _create_version_json(app_folder, app_name)

    # Update registry
    if registry_path:
        registry = AppRegistry(registry_path)
        registry.add_app(
            name=app_name,
            template=template_type,
            folder=f"apps/{app_name}",
            mesh_service=app_name.lower().replace(" ", "_"),
            metadata={
                "features": features or [],
                "created_by": "create_app_from_template"
            }
        )
        logger.info(f"App registered: {app_name}")

    logger.info(f"✓ App created: {app_folder}")
    return app_folder


def _customize_claude_config(app_folder: Path, app_name: str, features: List[str]):
    """
    Customize .claude/ configuration for the app's Claude instance.

    Args:
        app_folder: App folder path
        app_name: App name
        features: List of features enabled
    """
    claude_dir = app_folder / ".claude"
    if not claude_dir.exists():
        logger.warning(f"No .claude directory in template for {app_name}")
        return

    # Get PCC context
    pcc_folder = app_folder.parent.parent  # apps/AppName -> apps -> PCC
    pcc_name = pcc_folder.name

    # Customize CLAUDE.md
    claude_md_template = claude_dir / "CLAUDE.md.template"
    claude_md = claude_dir / "CLAUDE.md"

    if claude_md_template.exists():
        content = claude_md_template.read_text()

        # Replace placeholders
        content = content.replace("{APP_NAME}", app_name)
        content = content.replace("{PCC_NAME}", pcc_name)
        content = content.replace("{MESH_SERVICE}", app_name.lower().replace(" ", "_"))
        content = content.replace("{CREATED_DATE}", datetime.now().isoformat())

        # Build features description
        features_desc = _build_features_description(features)
        content = content.replace("{FEATURES_DESCRIPTION}", features_desc)

        # Write customized CLAUDE.md
        claude_md.write_text(content)

        # Remove template file
        claude_md_template.unlink()

        logger.info(f"✓ Customized .claude/CLAUDE.md for {app_name}")
    else:
        logger.warning(f"No CLAUDE.md.template found for {app_name}")

    # settings.local.json is already correct, no need to customize
    logger.info(f"✓ .claude/ configuration ready for {app_name}")


def _build_features_description(features: List[str]) -> str:
    """
    Build human-readable description of enabled features.

    Args:
        features: List of feature names

    Returns:
        Formatted feature description
    """
    if not features:
        return "- Standard PyQt6 application (no additional features)"

    descriptions = []

    feature_map = {
        "counter": "- **Counter**: Simple increment/decrement counter with UI",
        "logger": "- **Logger**: Event logging and log display functionality",
        "parent_cc_client": "- **Parent CC Client**: Request assistance from Parent CC",
        "mm_mesh": "- **MM Mesh**: Register and communicate with other apps",
        "settings": "- **Settings**: User preferences and configuration management",
        "database": "- **Database**: SQLite database integration",
    }

    for feature in features:
        if feature in feature_map:
            descriptions.append(feature_map[feature])
        else:
            descriptions.append(f"- **{feature.title()}**: Custom feature")

    return "\n".join(descriptions)


def _customize_app(app_folder: Path, app_name: str, features: List[str]):
    """
    Customize app files with app-specific information.

    Args:
        app_folder: App folder path
        app_name: App name
        features: List of features to include
    """
    logger.info(f"Customizing app: {app_name}")

    # Update __init__.py with app name
    init_file = app_folder / "__init__.py"
    if init_file.exists():
        content = init_file.read_text()
        content = content.replace("{APP_NAME}", app_name)
        init_file.write_text(content)

    # Update README.md
    readme_file = app_folder / "README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        content = content.replace("PyQt6 Application Template", app_name)
        content = content.replace("My App", app_name)
        readme_file.write_text(content)

    # Create main.py if features include specific app types
    if "counter" in features:
        _create_counter_app(app_folder, app_name)
    elif "logger" in features:
        _create_logger_app(app_folder, app_name)


def _create_version_json(app_folder: Path, app_name: str):
    """
    Create version.json for app.

    Args:
        app_folder: App folder path
        app_name: App name
    """
    version_json = app_folder / "version.json"

    # Copy from template if it exists
    template_version = app_folder / "version.json.template"
    if template_version.exists():
        shutil.copy(template_version, version_json)
    else:
        # Create new version.json
        version_data = {
            "version": "0.1.0",
            "build_number": 1,
            "build_date": "",
            "build_time": "",
            "build_timestamp": ""
        }
        with open(version_json, 'w') as f:
            json.dump(version_data, f, indent=2)

    logger.info(f"Created version.json for {app_name}")


def _create_counter_app(app_folder: Path, app_name: str):
    """Create a simple counter app."""
    main_py = app_folder / "main.py"

    code = f'''"""
{app_name} - Simple Counter App

Demonstrates Parent CC protocol integration.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLabel
)

from base_application import BaseApplication, create_application
from parent_cc_protocol import ParentCCProtocol, RequestPriority
from version_info._version_data import VERSION


class {app_name.replace(" ", "")}(BaseApplication):
    """Simple counter app that requests help from Parent CC."""

    def __init__(self, app_name: str = "{app_name}", app_version: str = "0.1.0", **kwargs):
        super().__init__(app_name=app_name, app_version=app_version, **kwargs)
        self.count = 0

        # Initialize Parent CC protocol
        self.protocol = ParentCCProtocol(
            app_name=app_name,
            mesh_integration=self.mesh
        )

        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        # Central widget
        layout = QVBoxLayout(self.central_widget)

        # Counter label
        self.counter_label = QLabel(f"Count: {{self.count}}")
        self.counter_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.counter_label)

        # Increment button
        inc_button = QPushButton("Click Me!")
        inc_button.clicked.connect(self.increment)
        layout.addWidget(inc_button)

        # Reset button
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_counter)
        layout.addWidget(reset_button)

        layout.addStretch()

    def increment(self):
        """Increment counter and check with Parent CC if needed."""
        self.count += 1
        self.counter_label.setText(f"Count: {{self.count}}")

        # Ask Parent CC when count exceeds threshold
        if self.count > 100:
            response = self.protocol.request_help(
                context={{"count": self.count, "threshold": 100}},
                question="Count exceeded 100. Should I reset?",
                priority=RequestPriority.NORMAL
            )

            if response.approved and "reset" in response.suggested_action.lower():
                self.reset_counter()
                self.statusBar().showMessage(
                    f"Parent CC advised: {{response.guidance}}", 5000
                )

    def reset_counter(self):
        """Reset counter to zero."""
        self.count = 0
        self.counter_label.setText(f"Count: {{self.count}}")


if __name__ == "__main__":
    sys.exit(create_application({app_name.replace(" ", "")}, "{app_name}", VERSION))
'''

    with open(main_py, 'w') as f:
        f.write(code)

    logger.info(f"Created counter app: {main_py}")


def _create_logger_app(app_folder: Path, app_name: str):
    """Create a simple logger app."""
    main_py = app_folder / "main.py"

    code = f'''"""
{app_name} - Simple Logger App

Demonstrates Parent CC protocol and peer communication.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLineEdit
)

from base_application import BaseApplication, create_application
from parent_cc_protocol import ParentCCProtocol
from version_info._version_data import VERSION


class {app_name.replace(" ", "")}(BaseApplication):
    """Simple logger app that communicates with other apps."""

    def __init__(self, app_name: str = "{app_name}", app_version: str = "0.1.0", **kwargs):
        super().__init__(app_name=app_name, app_version=app_version, **kwargs)

        # Initialize Parent CC protocol
        self.protocol = ParentCCProtocol(
            app_name=app_name,
            mesh_integration=self.mesh
        )

        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self.central_widget)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message to log...")
        layout.addWidget(self.message_input)

        # Log button
        log_button = QPushButton("Log Message")
        log_button.clicked.connect(self.log_message)
        layout.addWidget(log_button)

        # Query button (query other apps via mesh)
        query_button = QPushButton("Query TestApp1 Count")
        query_button.clicked.connect(self.query_counter)
        layout.addWidget(query_button)

    def log_message(self):
        """Log a message and request analysis from Parent CC."""
        message = self.message_input.text()
        if not message:
            return

        self.log_display.append(f"[{{datetime.now().strftime('%H:%M:%S')}}] {{message}}")
        self.message_input.clear()

        # Request analysis from Parent CC
        response = self.protocol.request_analysis(
            data={{"message": message, "timestamp": datetime.now().isoformat()}},
            analysis_type="message_content"
        )

        if response.guidance:
            self.log_display.append(f"  → Parent CC: {{response.guidance}}")

    def query_counter(self):
        """Query TestApp1's counter via MM mesh."""
        if not self.mesh:
            self.log_display.append("Error: MM mesh not connected")
            return

        try:
            result = self.mesh.call_service(
                service_name="testapp1",
                tool_name="get_count"
            )

            if result:
                self.log_display.append(f"TestApp1 count: {{result.get('count', 'unknown')}}")
        except Exception as e:
            self.log_display.append(f"Error querying TestApp1: {{e}}")


if __name__ == "__main__":
    from datetime import datetime
    sys.exit(create_application({app_name.replace(" ", "")}, "{app_name}", VERSION))
'''

    with open(main_py, 'w') as f:
        f.write(code)

    logger.info(f"Created logger app: {main_py}")


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Create app from template")
    parser.add_argument("--name", required=True, help="App name")
    parser.add_argument(
        "--template",
        default="pyqt_app",
        choices=list(TEMPLATES.keys()),
        help="Template type"
    )
    parser.add_argument(
        "--pcc-folder",
        required=True,
        help="Parent CC folder path"
    )
    parser.add_argument(
        "--features",
        nargs="+",
        help="Features to include (counter, logger, etc.)"
    )
    parser.add_argument(
        "--registry",
        help="Path to app registry"
    )

    args = parser.parse_args()

    try:
        pcc_folder = Path(args.pcc_folder)
        registry_path = Path(args.registry) if args.registry else None

        app_folder = create_app_from_template(
            app_name=args.name,
            template_type=args.template,
            pcc_folder=pcc_folder,
            features=args.features,
            registry_path=registry_path
        )

        print(f"✓ App created: {app_folder}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
