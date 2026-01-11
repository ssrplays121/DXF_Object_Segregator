"""Compile Qt resource files."""

import os
import subprocess
from pathlib import Path


def compile_resources():
    """Compile Qt .qrc resource files to Python modules."""
    resources_dir = Path(__file__).parent.parent / "resources"
    qrc_file = resources_dir / "icons.qrc"

    if qrc_file.exists():
        output_file = resources_dir / "resources_rc.py"
        try:
            # Try using pyrcc6 (PyQt6)
            subprocess.run(
                ["pyrcc6", "-o", str(output_file), str(qrc_file)],
                check=True
            )
            print(f"Successfully compiled {qrc_file} to {output_file}")
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                # Fallback to pyrcc5 (PyQt5)
                subprocess.run(
                    ["pyrcc5", "-o", str(output_file), str(qrc_file)],
                    check=True
                )
                print(f"Successfully compiled {qrc_file} to {output_file}")
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"Warning: Could not compile resources: {e}")
    else:
        print(f"Resource file not found: {qrc_file}")


if __name__ == "__main__":
    compile_resources()
