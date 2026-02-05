"""
TestApp1 - Simple Counter App

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


class TestApp1(BaseApplication):
    """Simple counter app that requests help from Parent CC."""

    def __init__(self, app_name: str = "TestApp1", app_version: str = "0.1.0", **kwargs):
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
        self.counter_label = QLabel(f"Count: {self.count}")
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
        self.counter_label.setText(f"Count: {self.count}")

        # Ask Parent CC when count exceeds threshold
        if self.count > 100:
            response = self.protocol.request_help(
                context={"count": self.count, "threshold": 100},
                question="Count exceeded 100. Should I reset?",
                priority=RequestPriority.NORMAL
            )

            if response.approved and "reset" in response.suggested_action.lower():
                self.reset_counter()
                self.statusBar().showMessage(
                    f"Parent CC advised: {response.guidance}", 5000
                )

    def reset_counter(self):
        """Reset counter to zero."""
        self.count = 0
        self.counter_label.setText(f"Count: {self.count}")


if __name__ == "__main__":
    sys.exit(create_application(TestApp1, "TestApp1", VERSION))
