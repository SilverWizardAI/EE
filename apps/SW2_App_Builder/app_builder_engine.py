"""
App Builder Engine - Core logic for building Silver Wizard applications
"""

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Callable, Optional
from PIL import Image, ImageDraw, ImageFont


class AppBuilderEngine:
    """Core engine for building PyQt6 applications from templates."""

    # Component-to-tab semantic mappings for intelligent placement
    COMPONENT_TAB_MAPPINGS = {
        'settings': ['settings', 'preferences', 'prefs', 'config', 'configuration', 'options'],
        'module_monitor': ['developer', 'dev', 'tools', 'debug', 'advanced', 'settings'],
        'mesh': ['system', 'status', 'network', 'about', 'info', 'information'],
        'parent_cc': ['help', 'tools', 'assistant', 'ai', 'claude', 'support']
    }

    def __init__(self):
        # Find EE root (two levels up from this file)
        self.ee_root = Path(__file__).parent.parent.parent
        self.template_dir = self.ee_root / "templates" / "pyqt_app"

    @staticmethod
    def sanitize_identifier(name: str) -> str:
        """
        Convert app/tab name to valid Python identifier.

        Example: "Test App" -> "TestApp"
                 "Hello World" -> "HelloWorld"
        """
        # Remove spaces and special chars, capitalize words
        import re
        # Replace spaces and non-alphanumeric with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # If starts with number, prefix with underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized or 'App'

    def _match_component_to_tab(self, component_key: str, tab_name: str) -> bool:
        """
        Check if a component semantically matches a tab name.

        Args:
            component_key: Component key (e.g., 'settings', 'mesh')
            tab_name: User-defined tab name (e.g., 'Settings', 'About', 'Developer Tools')

        Returns:
            True if component should be placed in this tab
        """
        if component_key not in self.COMPONENT_TAB_MAPPINGS:
            return False

        # Normalize tab name for comparison
        normalized_tab = tab_name.lower().strip()

        # Check if tab name matches any of the component's keywords
        keywords = self.COMPONENT_TAB_MAPPINGS[component_key]

        # First try exact match
        if normalized_tab in keywords:
            return True

        # Then try if tab name contains any keyword (for multi-word tabs like "Developer Tools")
        for keyword in keywords:
            if keyword in normalized_tab:
                return True

        return False

    def _assign_components_to_tabs(self, components: Dict, tabs: List[str]) -> Dict[str, List[str]]:
        """
        Assign components to tabs based on semantic matching.

        Args:
            components: Dict of component_key -> enabled (bool)
            tabs: List of user-defined tab names

        Returns:
            Dict mapping tab_name (lowercase) -> [list of component keys]
            Special key '_features' contains unmatched components
        """
        assignments = {tab.lower(): [] for tab in tabs}
        assignments['_features'] = []  # Fallback for unmatched components

        # Process each enabled component
        for component_key, enabled in components.items():
            if not enabled:
                continue

            # Try to match component to a custom tab
            matched = False
            for tab_name in tabs:
                if self._match_component_to_tab(component_key, tab_name):
                    assignments[tab_name.lower()].append(component_key)
                    matched = True
                    break  # Use first match

            # If no match, add to fallback Features tab
            if not matched:
                assignments['_features'].append(component_key)

        return assignments

    def build_app(self, config: Dict, log_func: Callable[[str], None]) -> Path:
        """
        Build complete application from configuration.

        Args:
            config: Configuration dictionary with all app settings
            log_func: Function to call for logging messages

        Returns:
            Path to created application
        """
        app_name = config['app_name']
        folder = config['folder']
        app_path = folder / app_name

        # Check if app already exists
        if app_path.exists():
            raise FileExistsError(f"App folder already exists: {app_path}")

        log_func(f"📁 Creating app folder: {app_name}")
        app_path.mkdir(parents=True, exist_ok=True)

        # Copy template files
        log_func("📋 Copying template files...")
        self._copy_template_files(app_path, app_name, config, log_func)

        # Generate main.py with components and tabs
        log_func("🔧 Generating main.py...")

        # Log component placement strategy
        if config['tabs'] and any(config['components'].values()):
            log_func("  ℹ️  Components will be intelligently placed in matching tabs")

        self._generate_main_py(app_path, config, log_func)

        # Create custom logo
        log_func(f"🎨 Creating logo: {config['logo_text']}")
        self._create_logo(app_path, config['logo_text'], log_func)

        # Initialize git
        if config['git']:
            log_func("📦 Initializing Git repository...")
            self._init_git(app_path, log_func)

        # Create Claude structure
        if config['claude']:
            log_func("🤖 Creating Claude Code structure...")
            self._create_claude_structure(app_path, config, log_func)

        log_func("✨ App structure complete!")
        return app_path

    def _copy_template_files(self, app_path: Path, app_name: str, config: Dict, log_func: Callable):
        """Copy essential template files."""
        files_to_copy = [
            "__init__.py",
            "version.json",
            "version_manager.py",
            "pytest.ini",
            "run_tests.py",
            "README.md"
        ]

        for file in files_to_copy:
            src = self.template_dir / file
            if src.exists():
                dst = app_path / file
                shutil.copy2(src, dst)

                # Customize README
                if file == "README.md":
                    content = dst.read_text()
                    content = content.replace("{APP_NAME}", app_name)
                    dst.write_text(content)

    def _generate_main_py(self, app_path: Path, config: Dict, log_func: Callable):
        """Generate main.py with selected components and tabs."""
        app_name = config['app_name']
        app_class = self.sanitize_identifier(app_name)
        version = config['version']
        components = config['components']
        tabs = config['tabs']

        # Build imports
        imports = [
            "import sys",
            "from pathlib import Path",
            "from PyQt6.QtWidgets import (",
            "    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,",
            "    QTextEdit, QGroupBox, QMessageBox,",
        ]

        if tabs:
            imports.append("    QTabWidget, QWidget,")

        imports.extend([
            ")",
            "from PyQt6.QtGui import QIcon",
            "from PyQt6.QtCore import Qt",
            "",
            "from sw_core.base_application import BaseApplication, create_application",
        ])

        if components.get('parent_cc'):
            imports.append("from sw_core.parent_cc_protocol import ParentCCProtocol, RequestPriority")

        imports.extend([
            "from sw_core.version_info import get_version",
            "",
        ])

        # Build class with feature flags
        enable_flags = []
        if not components.get('mesh'):
            enable_flags.append("enable_mesh=False")
        if not components.get('module_monitor'):
            enable_flags.append("enable_module_monitor=False")

        flags_str = ", " + ", ".join(enable_flags) if enable_flags else ""

        class_def = [
            f'class {app_class}(BaseApplication):',
            f'    """{app_name} - Silver Wizard Application with library features."""',
            "",
            f'    def __init__(self, app_name: str = "{app_name}", app_version: str = "{version}", **kwargs):',
            f"        super().__init__(app_name=app_name, app_version=app_version{flags_str}, **kwargs)",
            "",
            "        # Set application icon",
            '        icon_path = Path(__file__).parent / "app_icon.png"',
            "        if icon_path.exists():",
            "            self.setWindowIcon(QIcon(str(icon_path)))",
            "",
        ]

        # Add component initialization
        if components.get('parent_cc'):
            class_def.extend([
                "        # Initialize Parent CC protocol",
                "        self.protocol = ParentCCProtocol(",
                "            app_name=app_name,",
                "            mesh_integration=self.mesh",
                "        )",
                "",
            ])

        class_def.extend([
            "        self.init_ui()",
            "",
        ])

        # Build init_ui with feature demos
        init_ui = self._build_ui_with_features(app_name, app_class, components, tabs)

        # Build feature methods
        feature_methods = self._build_feature_methods(components)

        # Build main block
        main_block = [
            "",
            "",
            'if __name__ == "__main__":',
            f'    sys.exit(create_application({app_class}, "{app_name}", get_version()))',
            "",
        ]

        # Combine all parts
        full_code = "\n".join([
            '"""',
            f'{app_name} - Silver Wizard Application',
            "",
            f"Version: {version}",
            "Built with SW2 App Builder - Demonstrating Silver Wizard library features",
            '"""',
            "",
            *imports,
            "",
            *class_def,
            *init_ui,
            *feature_methods,
            *main_block
        ])

        # Write main.py
        main_py = app_path / "main.py"
        main_py.write_text(full_code)

    def _build_ui_with_features(self, app_name: str, app_class: str, components: Dict, tabs: List[str]) -> List[str]:
        """Build init_ui method with intelligent component placement."""
        init_ui = [
            "    def init_ui(self):",
            f'        """Initialize {app_name} user interface."""',
            "        layout = QVBoxLayout(self.central_widget)",
            "        layout.setSpacing(10)",
            "        layout.setContentsMargins(15, 15, 15, 15)",
            "",
        ]

        if tabs:
            # Tabbed interface with intelligent component placement
            init_ui.extend([
                "        # Create tab widget",
                "        tab_widget = QTabWidget()",
                "        layout.addWidget(tab_widget)",
                "",
            ])

            # Get component-to-tab assignments
            assignments = self._assign_components_to_tabs(components, tabs)

            # Build each custom tab with its assigned components
            for tab_name in tabs:
                tab_var = self.sanitize_identifier(tab_name).lower()
                tab_components = assignments.get(tab_name.lower(), [])

                init_ui.extend([
                    f"        # {tab_name} tab",
                    f"        {tab_var}_widget = QWidget()",
                    f"        {tab_var}_layout = QVBoxLayout({tab_var}_widget)",
                    "",
                ])

                # Add components assigned to this tab
                if tab_components:
                    for component_key in tab_components:
                        if component_key == 'mesh':
                            init_ui.extend(self._build_mesh_demo_ui(target_layout=f"{tab_var}_layout"))
                        elif component_key == 'module_monitor':
                            init_ui.extend(self._build_module_monitor_demo_ui(target_layout=f"{tab_var}_layout"))
                        elif component_key == 'settings':
                            init_ui.extend(self._build_settings_demo_ui(target_layout=f"{tab_var}_layout"))
                        elif component_key == 'parent_cc':
                            init_ui.extend(self._build_parent_cc_demo_ui(target_layout=f"{tab_var}_layout"))

                # Add placeholder content section
                init_ui.extend([
                    f'        # Add your custom {tab_name.lower()} content below',
                    f'        # {tab_var}_layout.addWidget(QLabel("Your content here"))',
                    "",
                ])

                init_ui.extend([
                    f"        {tab_var}_layout.addStretch()",
                    f'        tab_widget.addTab({tab_var}_widget, "{tab_name}")',
                    "",
                ])

            # Add Features tab only if there are unmatched components
            unmatched = assignments.get('_features', [])
            if unmatched:
                init_ui.extend([
                    "        # Features tab (unmatched components)",
                    "        features_widget = QWidget()",
                    "        features_layout = QVBoxLayout(features_widget)",
                    "",
                ])

                for component_key in unmatched:
                    if component_key == 'mesh':
                        init_ui.extend(self._build_mesh_demo_ui(target_layout="features_layout"))
                    elif component_key == 'module_monitor':
                        init_ui.extend(self._build_module_monitor_demo_ui(target_layout="features_layout"))
                    elif component_key == 'settings':
                        init_ui.extend(self._build_settings_demo_ui(target_layout="features_layout"))
                    elif component_key == 'parent_cc':
                        init_ui.extend(self._build_parent_cc_demo_ui(target_layout="features_layout"))

                init_ui.extend([
                    "        features_layout.addStretch()",
                    '        tab_widget.addTab(features_widget, "🔧 Features")',
                    "",
                ])

        else:
            # Single window with feature demos
            init_ui.extend([
                f'        # Header',
                f'        header = QLabel("🚀 {app_name}")',
                '        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 15px;")',
                "        header.setAlignment(Qt.AlignmentFlag.AlignCenter)",
                "        layout.addWidget(header)",
                "",
            ])

            # Add all enabled components to main layout
            if components.get('mesh'):
                init_ui.extend(self._build_mesh_demo_ui(target_layout="layout"))
            if components.get('module_monitor'):
                init_ui.extend(self._build_module_monitor_demo_ui(target_layout="layout"))
            if components.get('settings'):
                init_ui.extend(self._build_settings_demo_ui(target_layout="layout"))
            if components.get('parent_cc'):
                init_ui.extend(self._build_parent_cc_demo_ui(target_layout="layout"))

            if not any(components.values()):
                init_ui.extend([
                    '        info = QLabel("Start building your application...")',
                    '        info.setStyleSheet("font-size: 14px; padding: 20px;")',
                    "        info.setAlignment(Qt.AlignmentFlag.AlignCenter)",
                    "        layout.addWidget(info)",
                    "",
                ])

            init_ui.append("        layout.addStretch()")

        return init_ui

    def _build_mesh_demo_ui(self, target_layout: str = "features_layout") -> List[str]:
        """Build mesh integration demo UI."""
        return [
            "        # Mesh Integration Demo",
            '        mesh_group = QGroupBox("🌐 Mesh Integration")',
            "        mesh_group_layout = QVBoxLayout()",
            "",
            "        if self.mesh:",
            '            self.mesh_status = QLabel("Status: Checking...")',
            "            mesh_group_layout.addWidget(self.mesh_status)",
            "",
            "            mesh_buttons = QHBoxLayout()",
            '            check_btn = QPushButton("Check Status")',
            "            check_btn.clicked.connect(self.check_mesh_status)",
            "            mesh_buttons.addWidget(check_btn)",
            "",
            '            list_btn = QPushButton("List Services")',
            "            list_btn.clicked.connect(self.list_mesh_services)",
            "            mesh_buttons.addWidget(list_btn)",
            "            mesh_group_layout.addLayout(mesh_buttons)",
            "",
            "            self.mesh_output = QTextEdit()",
            "            self.mesh_output.setReadOnly(True)",
            "            self.mesh_output.setMaximumHeight(100)",
            "            mesh_group_layout.addWidget(self.mesh_output)",
            "            self.check_mesh_status()  # Check on startup",
            "        else:",
            '            mesh_group_layout.addWidget(QLabel("Mesh integration not enabled"))',
            "",
            "        mesh_group.setLayout(mesh_group_layout)",
            f"        {target_layout}.addWidget(mesh_group)",
            "",
        ]

    def _build_module_monitor_demo_ui(self, target_layout: str = "features_layout") -> List[str]:
        """Build module monitor demo UI."""
        return [
            "        # Module Monitor Demo",
            '        monitor_group = QGroupBox("📊 Module Monitor")',
            "        monitor_group_layout = QVBoxLayout()",
            "",
            "        if self.module_monitor:",
            '            self.monitor_status = QLabel("Click button to check module sizes")',
            "            monitor_group_layout.addWidget(self.monitor_status)",
            "",
            '            check_modules_btn = QPushButton("Check Module Sizes")',
            "            check_modules_btn.clicked.connect(self.check_modules)",
            "            monitor_group_layout.addWidget(check_modules_btn)",
            "",
            "            self.module_output = QTextEdit()",
            "            self.module_output.setReadOnly(True)",
            "            self.module_output.setMaximumHeight(100)",
            "            monitor_group_layout.addWidget(self.module_output)",
            "        else:",
            '            monitor_group_layout.addWidget(QLabel("Module monitoring not enabled"))',
            "",
            "        monitor_group.setLayout(monitor_group_layout)",
            f"        {target_layout}.addWidget(monitor_group)",
            "",
        ]

    def _build_settings_demo_ui(self, target_layout: str = "features_layout") -> List[str]:
        """Build settings/theme demo UI."""
        return [
            "        # Theme Settings Demo",
            '        settings_group = QGroupBox("🎨 Theme Settings")',
            "        settings_group_layout = QVBoxLayout()",
            "",
            '        current_theme = self.settings.get("theme", "dark")',
            '        self.theme_status = QLabel(f"Current theme: {current_theme}")',
            "        settings_group_layout.addWidget(self.theme_status)",
            "",
            "        theme_buttons = QHBoxLayout()",
            '        dark_btn = QPushButton("🌙 Dark Theme")',
            '        dark_btn.clicked.connect(lambda: self.switch_theme("dark"))',
            "        theme_buttons.addWidget(dark_btn)",
            "",
            '        light_btn = QPushButton("☀️ Light Theme")',
            '        light_btn.clicked.connect(lambda: self.switch_theme("light"))',
            "        theme_buttons.addWidget(light_btn)",
            "        settings_group_layout.addLayout(theme_buttons)",
            "",
            "        settings_group.setLayout(settings_group_layout)",
            f"        {target_layout}.addWidget(settings_group)",
            "",
        ]

    def _build_parent_cc_demo_ui(self, target_layout: str = "features_layout") -> List[str]:
        """Build Parent CC protocol demo UI."""
        return [
            "        # Parent CC Protocol Demo",
            '        pcc_group = QGroupBox("🤖 Parent CC Protocol")',
            "        pcc_group_layout = QVBoxLayout()",
            "",
            '        pcc_group_layout.addWidget(QLabel("Request help from Parent Claude instance:"))',
            "",
            '        help_btn = QPushButton("Request Assistance")',
            "        help_btn.clicked.connect(self.request_parent_help)",
            "        pcc_group_layout.addWidget(help_btn)",
            "",
            "        self.pcc_output = QTextEdit()",
            "        self.pcc_output.setReadOnly(True)",
            "        self.pcc_output.setMaximumHeight(100)",
            "        pcc_group_layout.addWidget(self.pcc_output)",
            "",
            "        pcc_group.setLayout(pcc_group_layout)",
            f"        {target_layout}.addWidget(pcc_group)",
            "",
        ]

    def _build_feature_methods(self, components: Dict) -> List[str]:
        """Build methods for feature demonstrations."""
        methods = []

        if components.get('mesh'):
            methods.extend([
                "    def check_mesh_status(self):",
                '        """Check mesh connection status."""',
                "        if self.mesh and self.mesh.is_available():",
                '            self.mesh_status.setText("✅ Status: Connected to MM mesh")',
                "            self.mesh_output.append(f\"Connected as: {self.mesh.instance_name}\")",
                "        else:",
                '            self.mesh_status.setText("❌ Status: Not connected")',
                '            self.mesh_output.append("Not connected to mesh proxy")',
                "",
                "    def list_mesh_services(self):",
                '        """List available mesh services."""',
                "        if not self.mesh or not self.mesh.is_available():",
                '            self.mesh_output.append("❌ Not connected to mesh")',
                "            return",
                "",
                "        try:",
                "            services = self.mesh.list_services()",
                "            self.mesh_output.clear()",
                "            self.mesh_output.append(f\"Found {len(services)} services:\")",
                "            for service in services[:10]:  # Show first 10",
                "                self.mesh_output.append(f\"  • {service}\")",
                "        except Exception as e:",
                "            self.mesh_output.append(f\"Error: {e}\")",
                "",
            ])

        if components.get('module_monitor'):
            methods.extend([
                "    def check_modules(self):",
                '        """Check module sizes and violations."""',
                "        if not self.module_monitor:",
                "            return",
                "",
                "        self.module_output.clear()",
                "        report = self.module_monitor.generate_report()",
                "",
                "        self.module_output.append(f\"Total modules: {report['total_modules']}\")",
                "        self.module_output.append(f\"Warnings: {report['warning_count']}\")",
                "        self.module_output.append(f\"Critical: {report['critical_count']}\")",
                "",
                "        if report['violations']:",
                "            self.module_output.append(\"\\nViolations:\")",
                "            for v in report['violations'][:5]:  # Show first 5",
                "                self.module_output.append(f\"  ⚠️ {v['file']}: {v['lines']} lines\")",
                "        else:",
                "            self.module_output.append(\"\\n✅ All modules within limits!\")",
                "",
            ])

        if components.get('settings'):
            methods.extend([
                "    def switch_theme(self, theme: str):",
                '        """Switch application theme."""',
                "        self.set_theme(theme)",
                "        self.settings.set('theme', theme)",
                "        self.theme_status.setText(f\"Current theme: {theme}\")",
                "        self.statusBar().showMessage(f\"Switched to {theme} theme\", 3000)",
                "",
            ])

        if components.get('parent_cc'):
            methods.extend([
                "    def request_parent_help(self):",
                '        """Request assistance from Parent CC."""',
                "        self.pcc_output.clear()",
                "        self.pcc_output.append(\"Sending request to Parent CC...\")",
                "",
                "        try:",
                "            response = self.protocol.request_help(",
                "                context={'feature': 'demo', 'timestamp': 'now'},",
                '                question="This is a test request from the generated app. Can you confirm the Parent CC protocol is working?",',
                "                priority=RequestPriority.NORMAL",
                "            )",
                "",
                "            if response.approved:",
                "                self.pcc_output.append(f\"\\n✅ Response: {response.guidance}\")",
                "                self.pcc_output.append(f\"Suggested: {response.suggested_action}\")",
                "            else:",
                "                self.pcc_output.append(\"\\n❌ Request not approved\")",
                "        except Exception as e:",
                "            self.pcc_output.append(f\"\\n❌ Error: {e}\")",
                "",
            ])

        return methods

    def _create_logo(self, app_path: Path, logo_text: str, log_func: Callable):
        """Create custom logo with specified text."""
        if not logo_text or logo_text == "??":
            log_func("  ⚠️  No logo text provided, using default 'T'")
            logo_text = "T"

        # Create icon using same logic as template create_icon.py
        sizes = [512, 256, 128, 64, 32, 16]

        # Create icons directory
        icons_dir = app_path / "icons"
        icons_dir.mkdir(exist_ok=True)

        for size in sizes:
            icon = self._generate_icon(size, logo_text)
            filename = icons_dir / f"app_icon_{size}.png"
            icon.save(filename, "PNG")

        # Main icon (512px)
        icon = self._generate_icon(512, logo_text)
        icon.save(app_path / "app_icon.png", "PNG")
        icon.save(icons_dir / "app_icon.png", "PNG")

        log_func(f"  ✓ Created {len(sizes)} icon sizes")

    def _generate_icon(self, size: int, letter: str) -> Image:
        """Generate single icon with Electric Coral styling."""
        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Colors from C3 theme (Electric Coral)
        bg_color = (255, 107, 53, 255)  # ACCENT_500: #FF6B35
        text_color = (237, 232, 220, 255)  # LIGHT_BG: #EDE8DC
        border_color = (229, 90, 43, 255)  # ACCENT_600: #E55A2B

        # Draw rounded rectangle background
        margin = size // 10
        border_width = size // 30

        # Draw border
        draw.rounded_rectangle(
            [(margin, margin), (size - margin, size - margin)],
            radius=size // 8,
            fill=border_color
        )

        # Draw inner background
        draw.rounded_rectangle(
            [(margin + border_width, margin + border_width),
             (size - margin - border_width, size - margin - border_width)],
            radius=size // 8 - border_width,
            fill=bg_color
        )

        # Draw letter
        try:
            # Try to use a bold system font
            font_size = size // 2
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()

        text = letter.upper()

        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the text
        text_x = (size - text_width) // 2 - bbox[0]
        text_y = (size - text_height) // 2 - bbox[1]

        # Draw text
        draw.text((text_x, text_y), text, fill=text_color, font=font)

        return img

    def _init_git(self, app_path: Path, log_func: Callable):
        """Initialize git repository with .gitignore."""
        try:
            # Create .gitignore
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyQt
*.qrc.py
moc_*.cpp
ui_*.py

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Local config
*.local.json
.env
"""
            gitignore_path = app_path / ".gitignore"
            gitignore_path.write_text(gitignore_content)

            # Initialize git
            subprocess.run(
                ["git", "init"],
                cwd=app_path,
                capture_output=True,
                check=True
            )

            # Initial commit
            subprocess.run(
                ["git", "add", "."],
                cwd=app_path,
                capture_output=True,
                check=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Initial commit: App created by SW2 App Builder"],
                cwd=app_path,
                capture_output=True,
                check=True
            )

            log_func("  ✓ Git initialized with initial commit")

        except subprocess.CalledProcessError as e:
            log_func(f"  ⚠️  Git init failed: {e}")
        except Exception as e:
            log_func(f"  ⚠️  Git error: {e}")

    def _create_claude_structure(self, app_path: Path, config: Dict, log_func: Callable):
        """Create .claude directory with CLAUDE.md."""
        try:
            claude_dir = app_path / ".claude"
            claude_dir.mkdir(exist_ok=True)

            # Create CLAUDE.md
            claude_md_content = f"""# {config['app_name']} - Development Guide

**Project:** {config['app_name']}
**Version:** {config['version']}
**Created:** With SW2 App Builder
**Framework:** PyQt6 + Silver Wizard Libraries

---

## Project Overview

{config['app_name']} is a Silver Wizard application built with:

"""

            # Add enabled components
            if config['components'].get('mesh'):
                claude_md_content += "- **Mesh Integration**: Connected to MM mesh for service discovery\n"
            if config['components'].get('parent_cc'):
                claude_md_content += "- **Parent CC Protocol**: Can spawn Claude workers for assistance\n"
            if config['components'].get('module_monitor'):
                claude_md_content += "- **Module Monitor**: Tracks code quality (<600 lines per module)\n"
            if config['components'].get('settings'):
                claude_md_content += "- **Settings & Themes**: User preferences with dark/light themes\n"

            claude_md_content += f"""
---

## Architecture

### UI Structure
"""

            if config['tabs']:
                claude_md_content += f"""
**Tabbed Interface:**
{chr(10).join(f"- {tab}" for tab in config['tabs'])}
"""
            else:
                claude_md_content += """
**Single Window Interface**
"""

            claude_md_content += """

### Libraries Used

- **sw_core**: Base application, mesh integration, settings, module monitoring
- **sw_pcc**: Parent CC protocol (if enabled)
- **PyQt6**: UI framework

---

## Development Guidelines

### Code Quality Standards

- Keep modules under 400 lines (warning at 600, critical at 800)
- Use type hints for all function parameters
- Write docstrings for all classes and public methods
- Follow PEP 8 style guidelines

### Testing

Run tests with:
```bash
python3 run_tests.py
```

### Version Management

Update version with:
```bash
python3 version_manager.py bump [major|minor|patch]
```

---

## Getting Started

1. **Install Dependencies**
   ```bash
   # Ensure sw_core and sw_pcc are in PYTHONPATH
   export PYTHONPATH="/path/to/EE/shared:$PYTHONPATH"
   ```

2. **Run Application**
   ```bash
   python3 main.py
   ```

3. **Run Tests**
   ```bash
   python3 run_tests.py
   ```

---

## Next Steps

- Implement your application logic in `main.py`
- Add tests in `tests/` directory
- Customize themes and settings as needed
- Connect to mesh services (if enabled)
- Use Parent CC for complex tasks (if enabled)

---

**Built with ❤️ using Silver Wizard Software tools**
"""

            claude_md = claude_dir / "CLAUDE.md"
            claude_md.write_text(claude_md_content)

            # Create basic settings.json for Claude Code
            settings_content = """{
  "allowedPrompts": [
    {
      "type": "bash",
      "pattern": "*",
      "description": "Allow all bash commands"
    }
  ]
}
"""
            settings_json = claude_dir / "settings.json"
            settings_json.write_text(settings_content)

            log_func("  ✓ Created .claude/CLAUDE.md and settings.json")

        except Exception as e:
            log_func(f"  ⚠️  Claude structure error: {e}")
