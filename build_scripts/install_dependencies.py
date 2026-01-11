"""Install project dependencies."""

import subprocess
import sys


def install_dependencies():
    """Install project dependencies."""
    dependencies = [
        "ezdxf>=1.0.0",
        "numpy>=1.20.0",
        "cython>=0.29.0",
        "PyQt6>=6.0.0",
    ]

    dev_dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=3.0.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
        "isort>=5.0.0",
        "mypy>=0.950",
    ]

    print("Installing core dependencies...")
    for dep in dependencies:
        print(f"  Installing {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    print("\nInstalling development dependencies...")
    for dep in dev_dependencies:
        print(f"  Installing {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    print("\nDependencies installed successfully!")


if __name__ == "__main__":
    install_dependencies()
