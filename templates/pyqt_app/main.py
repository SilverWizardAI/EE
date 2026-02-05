"""
{APP_NAME} - PyQt6 Application

Template main.py - customize for your application.
"""

import sys
from PyQt6.QtWidgets import QVBoxLayout, QLabel

from base_application import BaseApplication, create_application
from parent_cc_protocol import ParentCCProtocol
from version_info._version_data import VERSION


class {APP_NAME}(BaseApplication):
    """Your custom application."""

    def __init__(self, app_name: str = "{APP_NAME}", app_version: str = "0.1.0", **kwargs):
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

        # Add your UI components here
        label = QLabel("Welcome to {APP_NAME}!")
        label.setStyleSheet("font-size: 18px; padding: 20px;")
        layout.addWidget(label)

        layout.addStretch()


if __name__ == "__main__":
    sys.exit(create_application({APP_NAME}, "{APP_NAME}", VERSION))
