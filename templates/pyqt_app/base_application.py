"""
PyQt6 Base Application Template

Enterprise-grade application base class with built-in integrations.

Module Size Target: <400 lines (Current: ~350 lines)
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget,
    QMenuBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QPalette, QColor

# Handle both package and script execution
try:
    from .settings_manager import SettingsManager
    from .version_manager import VersionManager
    from .mesh_integration import MeshIntegration
    from .module_monitor import ModuleMonitor
except ImportError:
    from settings_manager import SettingsManager
    from version_manager import VersionManager
    from mesh_integration import MeshIntegration
    from module_monitor import ModuleMonitor


logger = logging.getLogger(__name__)


class BaseApplication(QMainWindow):
    """
    Base class for all Silver Wizard PyQt6 applications.

    Provides: theme management, settings persistence, version tracking,
    mesh integration, module monitoring, standard menus, error handling.
    """

    # Signals
    theme_changed = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)
    mesh_connected = pyqtSignal()
    mesh_disconnected = pyqtSignal()

    def __init__(
        self,
        app_name: str,
        app_version: Optional[str] = None,
        organization: str = "Silver Wizard Software",
        enable_mesh: bool = True,
        enable_module_monitor: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.app_name = app_name
        self.organization = organization

        self._setup_logging()

        # Initialize version manager (auto-detects version from version_info if available)
        self.version = VersionManager(
            app_name=app_name,
            manual_version=app_version
        )

        # Use detected version
        self.app_version = self.version.version

        logger.info("=" * 70)
        logger.info(f"🚀 STARTING {app_name.upper()} v{self.app_version}")
        logger.info("=" * 70)

        # Initialize settings manager
        self.settings = SettingsManager(
            organization=organization,
            application=app_name
        )

        # Optional integrations
        self.mesh: Optional[MeshIntegration] = None
        if enable_mesh:
            self.mesh = MeshIntegration(
                instance_name=app_name.lower().replace(" ", "_"),
                on_connected=self.mesh_connected.emit,
                on_disconnected=self.mesh_disconnected.emit
            )

        self.module_monitor: Optional[ModuleMonitor] = None
        if enable_module_monitor:
            self.module_monitor = ModuleMonitor(
                project_root=Path.cwd(),
                warning_threshold=600,
                critical_threshold=800
            )

        # Setup UI
        self._init_base_ui()
        self._setup_menus()
        self._setup_status_bar()

        # Apply saved theme
        self._apply_theme(self.settings.get("theme", "dark"))

        # Connect signals
        self._connect_signals()

        # Start monitoring
        if self.module_monitor:
            self._start_module_monitoring()

        logger.info(f"✓ {app_name} initialized successfully")

    def _setup_logging(self):
        """Configure application logging."""
        log_dir = Path.home() / ".local" / "share" / self.app_name / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _init_base_ui(self):
        """Initialize base UI elements."""
        self.setWindowTitle(f"{self.app_name} v{self.app_version}")
        self.setGeometry(100, 100, 1200, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

    def _setup_menus(self):
        """Setup standard menu structure."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        dark_theme_action = QAction("&Dark Theme", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.settings.get("theme") == "dark")
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        view_menu.addAction(dark_theme_action)

        light_theme_action = QAction("&Light Theme", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.settings.get("theme") == "light")
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        view_menu.addAction(light_theme_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        if self.module_monitor:
            view_menu.addSeparator()
            module_stats_action = QAction("Module &Statistics...", self)
            module_stats_action.triggered.connect(self.show_module_statistics)
            view_menu.addAction(module_stats_action)

    def _setup_status_bar(self):
        """Setup status bar with indicators."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _apply_theme(self, theme: str):
        """Apply theme (dark or light)."""
        app = QApplication.instance()
        if not app:
            return

        if theme == "dark":
            self._apply_dark_theme(app)
        else:
            self._apply_light_theme(app)

        self.settings.set("theme", theme)
        self.theme_changed.emit(theme)
        logger.info(f"Theme changed to: {theme}")

    def _apply_dark_theme(self, app: QApplication):
        """Apply dark theme palette."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(palette)

    def _apply_light_theme(self, app: QApplication):
        """Apply light theme palette."""
        app.setPalette(app.style().standardPalette())

    def _connect_signals(self):
        """Connect internal signals."""
        if self.mesh:
            self.mesh_connected.connect(self._on_mesh_connected)
            self.mesh_disconnected.connect(self._on_mesh_disconnected)

    def _start_module_monitoring(self):
        """Start periodic module size monitoring."""
        self.module_monitor_timer = QTimer()
        self.module_monitor_timer.timeout.connect(self._check_module_sizes)
        self.module_monitor_timer.start(60000)

    def _check_module_sizes(self):
        """Check module sizes and show warnings if needed."""
        if not self.module_monitor:
            return
        violations = self.module_monitor.check_all_modules()
        if violations:
            logger.warning(f"Module size violations: {len(violations)}")

    def set_theme(self, theme: str):
        """Set application theme."""
        self._apply_theme(theme)

    def show_settings_dialog(self):
        """Show settings dialog (override in subclass)."""
        QMessageBox.information(
            self,
            "Settings",
            f"{self.app_name} Settings\n\n"
            f"Override show_settings_dialog() for custom settings."
        )

    def show_about_dialog(self):
        """Show about dialog with version information."""
        about_text = self.version.get_about_text(
            include_copyright=True,
            organization=self.organization
        )
        QMessageBox.about(self, f"About {self.app_name}", about_text)

    def show_module_statistics(self):
        """Show module size statistics dialog."""
        if not self.module_monitor:
            return
        stats = self.module_monitor.get_statistics()
        stats_text = (
            f"<h3>Module Statistics</h3>"
            f"<p>Total modules: {stats['total_modules']}</p>"
            f"<p>Average size: {stats['average_size']} lines</p>"
            f"<p>Largest: {stats['largest_module']} "
            f"({stats['largest_size']} lines)</p>"
            f"<p>Violations: {stats['violations']}</p>"
        )
        QMessageBox.information(self, "Module Statistics", stats_text)

    def _on_mesh_connected(self):
        """Called when mesh connection established."""
        logger.info("✓ Mesh connected")

    def _on_mesh_disconnected(self):
        """Called when mesh connection lost."""
        logger.warning("✗ Mesh disconnected")

    def closeEvent(self, event):
        """Handle application close."""
        logger.info(f"Closing {self.app_name}...")
        if self.mesh:
            self.mesh.disconnect()
        self.settings.sync()
        super().closeEvent(event)
        logger.info("✓ Application closed cleanly")


def create_application(app_class, app_name: str, app_version: str, **kwargs) -> int:
    """
    Standard application entry point.

    Supports both GUI and headless modes via --headless flag.
    Handles SIGTERM/SIGINT for graceful shutdown.
    """
    import signal
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    args, remaining = parser.parse_known_args()

    # Create QApplication with remaining args
    sys.argv = [sys.argv[0]] + remaining
    app = QApplication(sys.argv)
    app.setOrganizationName("Silver Wizard Software")
    app.setApplicationName(app_name)
    app.setApplicationVersion(app_version)

    try:
        from qt_instrument import enable_instrumentation
        enable_instrumentation(app)
        logger.info("✓ PQTI instrumentation enabled")
    except ImportError:
        logger.info("ℹ PQTI instrumentation not available")

    # Create application window
    window = app_class(app_name=app_name, app_version=app_version, **kwargs)

    # Show window only in GUI mode
    if not args.headless:
        window.show()
        logger.info(f"✓ {app_name} window shown (GUI mode)")
    else:
        logger.info(f"✓ {app_name} running in headless mode")

    # Install signal handlers for graceful shutdown
    # Use a flag that Qt can check periodically
    shutdown_requested = {'value': False}

    def signal_handler(signum, frame):
        """Handle SIGTERM/SIGINT gracefully."""
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info(f"Received {signal_name}, requesting shutdown...")
        shutdown_requested['value'] = True

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create timer to check for shutdown requests
    # This allows Python signal handlers to run within Qt event loop
    def check_shutdown():
        if shutdown_requested['value']:
            logger.info("Shutting down gracefully...")
            window.close()
            app.quit()

    shutdown_timer = QTimer()
    shutdown_timer.timeout.connect(check_shutdown)
    shutdown_timer.start(100)  # Check every 100ms

    # Run event loop (works in both GUI and headless modes)
    result = app.exec()
    shutdown_timer.stop()
    return result
