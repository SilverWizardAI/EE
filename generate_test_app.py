"""
Generate a test app to validate intelligent component placement.
"""

from pathlib import Path
import sys
import shutil

# Add SW2 App Builder to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "SW2_App_Builder"))

from app_builder_engine import AppBuilderEngine


def log_message(msg: str):
    """Simple log function."""
    print(msg)


def main():
    engine = AppBuilderEngine()

    # Test app output directory
    output_dir = Path(__file__).parent / "apps"
    test_app_name = "IntelligentMatchTest"
    test_app_path = output_dir / test_app_name

    # Clean up if exists
    if test_app_path.exists():
        print(f"🗑️  Removing existing test app: {test_app_path}")
        shutil.rmtree(test_app_path)

    # Configuration with tabs that should match components
    config = {
        'app_name': test_app_name,
        'version': '1.0.0',
        'folder': output_dir,
        'logo_text': 'IM',
        'git': False,  # Skip git for faster testing
        'claude': False,  # Skip Claude structure
        'tabs': ['Home', 'Settings', 'System Info', 'Help'],
        'components': {
            'settings': True,       # Should go to Settings tab
            'mesh': True,           # Should go to System Info tab (contains 'info')
            'module_monitor': True, # Should go to Settings tab (module_monitor keywords include 'settings')
            'parent_cc': True       # Should go to Help tab
        }
    }

    print("=" * 70)
    print("Generating Test App with Intelligent Component Placement")
    print("=" * 70)
    print(f"\nApp Name: {config['app_name']}")
    print(f"Tabs: {config['tabs']}")
    print(f"Components: {[k for k, v in config['components'].items() if v]}")
    print("\nExpected placement:")
    print("  - Settings component → Settings tab")
    print("  - Module Monitor → Settings tab (keyword: 'settings')")
    print("  - Mesh → System Info tab (keyword: 'info')")
    print("  - Parent CC → Help tab")
    print("\n" + "=" * 70 + "\n")

    # Build the app
    try:
        app_path = engine.build_app(config, log_message)
        print(f"\n✅ App generated successfully at: {app_path}")

        # Read and display key parts of generated main.py
        main_py = app_path / "main.py"
        if main_py.exists():
            print("\n" + "=" * 70)
            print("Generated main.py (init_ui method preview)")
            print("=" * 70)

            content = main_py.read_text()

            # Extract init_ui method
            start = content.find("def init_ui(self):")
            if start != -1:
                # Find the next method definition or end of class
                end = content.find("\n    def ", start + 1)
                if end == -1:
                    end = content.find("\nif __name__", start)

                init_ui_code = content[start:end] if end != -1 else content[start:]

                # Show first 100 lines of init_ui
                lines = init_ui_code.split('\n')[:100]
                for line in lines:
                    print(line)

                if len(init_ui_code.split('\n')) > 100:
                    print("\n... (truncated)")

            print("\n" + "=" * 70)
            print("✨ Success! Check the generated app structure:")
            print("=" * 70)
            print(f"\n📁 {app_path}/")
            print(f"   ├── main.py           (component UIs should be in matching tabs)")
            print(f"   ├── app_icon.png      (IM logo)")
            print(f"   └── version.json")
            print(f"\n🚀 Run with: cd {app_path} && python3 main.py\n")

    except Exception as e:
        print(f"❌ Error generating app: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
