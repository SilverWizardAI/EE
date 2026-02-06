"""
SW2 App Builder - Visual Application Creator

Build PyQt6 applications with library components, custom tabs, and branding.
"""

import sys
from pathlib import Path
from typing import List, Dict
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QGroupBox, QScrollArea, QWidget, QFileDialog,
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont

from sw_core.base_application import BaseApplication, create_application
from sw_core.parent_cc_protocol import ParentCCProtocol
from sw_core.version_info import get_version

from app_builder_engine import AppBuilderEngine


class SW2_App_Builder(BaseApplication):
    """Visual app builder for Silver Wizard applications."""

    def __init__(self, app_name: str = "SW2_App_Builder", app_version: str = "0.1.0", **kwargs):
        super().__init__(app_name=app_name, app_version=app_version, **kwargs)

        # Set application icon
        icon_path = Path(__file__).parent / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Initialize Parent CC protocol
        self.protocol = ParentCCProtocol(
            app_name=app_name,
            mesh_integration=self.mesh
        )

        # Initialize builder engine
        self.engine = AppBuilderEngine()

        # Tab list
        self.tabs = ["Home", "Settings"]

        # Use light theme for better input visibility
        self.set_theme("light")

        self.init_ui()
        self.resize(900, 800)

    def init_ui(self):
        """Initialize comprehensive app builder UI."""
        # Main scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🏗️ SW2 App Builder")
        header.setStyleSheet("font-size: 28px; font-weight: bold; padding: 15px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Build Silver Wizard applications with custom components and features")
        subtitle.setStyleSheet("font-size: 13px; color: #666; padding-bottom: 10px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Sections
        layout.addWidget(self.create_app_config_section())
        layout.addWidget(self.create_component_selection_section())
        layout.addWidget(self.create_tab_configuration_section())
        layout.addWidget(self.create_location_section())
        layout.addWidget(self.create_logo_section())
        layout.addWidget(self.create_build_section())

        scroll.setWidget(container)

        # Set scroll area as central widget content
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_app_config_section(self):
        """App name and version configuration."""
        group = QGroupBox("📱 Application Configuration")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        # App name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("App Name:"))
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("e.g., MyAwesomeApp")
        self.app_name_input.setStyleSheet("QLineEdit { padding: 5px; }")
        self.app_name_input.textChanged.connect(self.update_logo_preview)
        name_layout.addWidget(self.app_name_input)
        layout.addLayout(name_layout)

        # Version
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self.version_input = QLineEdit()
        self.version_input.setText("0.1.0")
        self.version_input.setPlaceholderText("e.g., 0.1.0")
        self.version_input.setStyleSheet("QLineEdit { padding: 5px; }")
        version_layout.addWidget(self.version_input)
        layout.addLayout(version_layout)

        group.setLayout(layout)
        return group

    def create_component_selection_section(self):
        """Library component checkboxes."""
        group = QGroupBox("📚 Library Components (select after Basic App config)")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        info = QLabel("Select which Silver Wizard library features to include:")
        info.setStyleSheet("font-size: 12px; color: #666; padding-bottom: 5px;")
        layout.addWidget(info)

        # Component checkboxes
        self.component_checks = {}

        components = [
            ("mesh", "Mesh Integration", "Connect to MM mesh for service discovery"),
            ("parent_cc", "Parent CC Protocol", "Spawn Claude workers for assistance"),
            ("module_monitor", "Module Monitor", "Track code quality and module sizes"),
            ("settings", "Settings & Themes", "User preferences and theme switching"),
        ]

        for key, name, desc in components:
            cb = QCheckBox(f"{name}")
            cb.setChecked(True)  # Default to all enabled
            cb.setToolTip(desc)
            cb.setStyleSheet("font-weight: normal;")
            layout.addWidget(cb)

            desc_label = QLabel(f"  → {desc}")
            desc_label.setStyleSheet("font-size: 11px; color: #666; padding-left: 25px;")
            layout.addWidget(desc_label)

            self.component_checks[key] = cb

        group.setLayout(layout)
        return group

    def create_tab_configuration_section(self):
        """Tab configuration with add/remove."""
        group = QGroupBox("📑 Tab Configuration")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        info = QLabel("Configure application tabs (or leave empty for single-window app):")
        info.setStyleSheet("font-size: 12px; color: #666; padding-bottom: 5px;")
        layout.addWidget(info)

        # Smart placement info
        smart_info = QLabel("💡 Components auto-place in matching tabs (e.g., Settings → Settings tab)")
        smart_info.setStyleSheet("font-size: 11px; color: #0066cc; font-style: italic; padding: 3px 0px 8px 0px;")
        layout.addWidget(smart_info)

        # Tab list
        self.tab_list = QListWidget()
        self.tab_list.setMaximumHeight(120)
        for tab in self.tabs:
            self.tab_list.addItem(tab)
        layout.addWidget(self.tab_list)

        # Add/Remove buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Tab")
        add_btn.clicked.connect(self.add_tab)
        button_layout.addWidget(add_btn)

        remove_btn = QPushButton("➖ Remove Selected")
        remove_btn.clicked.connect(self.remove_tab)
        button_layout.addWidget(remove_btn)

        clear_btn = QPushButton("🗑️ Clear All (Single Window)")
        clear_btn.clicked.connect(self.clear_tabs)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def create_location_section(self):
        """Folder selection and git/claude options."""
        group = QGroupBox("📁 Location & Structure")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("App Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setText(str(Path.home() / "Desktop"))
        self.folder_input.setStyleSheet("QLineEdit { padding: 5px; }")
        folder_layout.addWidget(self.folder_input)

        browse_btn = QPushButton("📂 Browse")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)

        layout.addLayout(folder_layout)

        # Git option
        self.git_check = QCheckBox("Initialize Git repository with .gitignore")
        self.git_check.setChecked(True)
        self.git_check.setStyleSheet("font-weight: normal;")
        layout.addWidget(self.git_check)

        # Claude structure option
        self.claude_check = QCheckBox("Create Claude Code structure (.claude/ with CLAUDE.md)")
        self.claude_check.setChecked(True)
        self.claude_check.setStyleSheet("font-weight: normal;")
        layout.addWidget(self.claude_check)

        group.setLayout(layout)
        return group

    def create_logo_section(self):
        """Logo text customization."""
        group = QGroupBox("🎨 Application Logo")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        info = QLabel("Customize the app icon text (1-3 characters recommended):")
        info.setStyleSheet("font-size: 12px; color: #666; padding-bottom: 5px;")
        layout.addWidget(info)

        # Logo text input
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(QLabel("Icon Text:"))
        self.logo_input = QLineEdit()
        self.logo_input.setPlaceholderText("Auto-generated from app name")
        self.logo_input.setMaxLength(3)
        self.logo_input.setStyleSheet("QLineEdit { padding: 5px; font-size: 14px; }")
        self.logo_input.textChanged.connect(self.update_logo_preview)
        logo_layout.addWidget(self.logo_input)
        layout.addLayout(logo_layout)

        # Preview label
        self.logo_preview = QLabel("Preview: [Will be Electric Coral orange]")
        self.logo_preview.setStyleSheet(
            "background-color: #FF6B35; color: #EDE8DC; "
            "font-size: 32px; font-weight: bold; padding: 20px; "
            "border-radius: 10px; border: 3px solid #E55A2B;"
        )
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setMaximumHeight(100)
        layout.addWidget(self.logo_preview)

        group.setLayout(layout)
        return group

    def create_build_section(self):
        """Build button and progress log."""
        group = QGroupBox("🚀 Build & Launch")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()

        # Build button
        self.build_btn = QPushButton("🏗️ Build Application")
        self.build_btn.setStyleSheet(
            "QPushButton { background-color: #FF6B35; color: white; "
            "font-size: 16px; font-weight: bold; padding: 12px; "
            "border-radius: 5px; }"
            "QPushButton:hover { background-color: #E55A2B; }"
        )
        self.build_btn.clicked.connect(self.build_application)
        layout.addWidget(self.build_btn)

        # Progress log
        log_label = QLabel("Build Log:")
        log_label.setStyleSheet("font-weight: bold; padding-top: 10px;")
        layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self.log_display)

        # Launch button (initially hidden)
        self.launch_btn = QPushButton("▶️ Launch Application")
        self.launch_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.launch_btn.clicked.connect(self.launch_application)
        self.launch_btn.setVisible(False)
        layout.addWidget(self.launch_btn)

        group.setLayout(layout)
        return group

    # Event handlers

    def update_logo_preview(self):
        """Update logo preview based on text input."""
        text = self.logo_input.text()
        if not text and self.app_name_input.text():
            # Auto-generate from app name
            name = self.app_name_input.text()
            text = ''.join([c for c in name if c.isupper()])[:2]
            if not text:
                text = name[:2].upper()

        self.logo_preview.setText(text.upper() if text else "??")

    def add_tab(self):
        """Add new tab to configuration."""
        from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "Add Tab", "Enter tab name:")
        if ok and text:
            self.tab_list.addItem(text)
            self.log(f"Added tab: {text}")

    def remove_tab(self):
        """Remove selected tab."""
        current = self.tab_list.currentItem()
        if current:
            self.tab_list.takeItem(self.tab_list.row(current))
            self.log(f"Removed tab: {current.text()}")

    def clear_tabs(self):
        """Clear all tabs for single-window app."""
        self.tab_list.clear()
        self.log("Cleared all tabs - will create single-window app")

    def browse_folder(self):
        """Open folder browser."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select App Folder",
            str(Path.home())
        )
        if folder:
            self.folder_input.setText(folder)

    def build_application(self):
        """Build the application from configuration."""
        # Validate inputs
        app_name = self.app_name_input.text().strip()
        if not app_name:
            QMessageBox.warning(self, "Validation Error", "Please enter an app name.")
            return

        version = self.version_input.text().strip()
        if not version:
            version = "0.1.0"

        folder = Path(self.folder_input.text())
        if not folder.exists():
            reply = QMessageBox.question(
                self,
                "Create Folder?",
                f"Folder doesn't exist:\n{folder}\n\nCreate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                folder.mkdir(parents=True, exist_ok=True)
            else:
                return

        # Gather configuration
        config = {
            'app_name': app_name,
            'version': version,
            'folder': folder,
            'components': {
                key: cb.isChecked()
                for key, cb in self.component_checks.items()
            },
            'tabs': [
                self.tab_list.item(i).text()
                for i in range(self.tab_list.count())
            ],
            'git': self.git_check.isChecked(),
            'claude': self.claude_check.isChecked(),
            'logo_text': self.logo_input.text() or self.logo_preview.text()
        }

        # Disable build button
        self.build_btn.setEnabled(False)
        self.log_display.clear()
        self.log("🏗️ Starting application build...")
        self.log(f"App: {app_name} v{version}")
        self.log(f"Location: {folder}")

        # Build app (using engine)
        try:
            app_path = self.engine.build_app(config, self.log)
            self.log("")
            self.log("✅ Application built successfully!")
            self.log(f"📁 Location: {app_path}")

            # Store app path and show launch button
            self.built_app_path = app_path
            self.launch_btn.setVisible(True)

            QMessageBox.information(
                self,
                "Success!",
                f"Application built successfully!\n\nLocation: {app_path}"
            )
        except Exception as e:
            self.log(f"❌ Error: {e}")
            QMessageBox.critical(self, "Build Error", f"Failed to build application:\n\n{e}")
        finally:
            self.build_btn.setEnabled(True)

    def launch_application(self):
        """Launch the built application."""
        if not hasattr(self, 'built_app_path'):
            QMessageBox.warning(self, "No App", "No application has been built yet.")
            return

        self.log("")
        self.log("🚀 Launching application...")

        try:
            import subprocess
            import os
            app_path = self.built_app_path
            main_py = app_path / "main.py"

            if not main_py.exists():
                raise FileNotFoundError(f"main.py not found at {main_py}")

            # Set up environment with PYTHONPATH for shared libraries
            env = os.environ.copy()
            shared_path = str(self.engine.ee_root / "shared")
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{shared_path}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = shared_path

            # Create log file for app output
            log_file = app_path / f"{app_path.name.lower()}.log"
            self.log(f"📝 Logging to: {log_file}")

            # Launch in background with proper environment
            with open(log_file, 'w') as f:
                proc = subprocess.Popen(
                    ["python3", "main.py"],
                    cwd=app_path,
                    env=env,
                    stdout=f,
                    stderr=subprocess.STDOUT
                )

            self.log(f"✅ Application launched! PID: {proc.pid}")
            self.log(f"📋 Check {log_file} for app logs")
            QMessageBox.information(
                self,
                "Launched!",
                f"Application launched successfully!\n\n"
                f"PID: {proc.pid}\n"
                f"Log: {log_file}\n\n"
                f"Check your dock/taskbar."
            )
        except Exception as e:
            self.log(f"❌ Launch error: {e}")
            QMessageBox.critical(self, "Launch Error", f"Failed to launch:\n\n{e}")

    def log(self, message: str):
        """Add message to build log."""
        self.log_display.append(message)
        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)


if __name__ == "__main__":
    sys.exit(create_application(SW2_App_Builder, "SW2_App_Builder", get_version()))
