"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_dxf_file():
    """Provide a sample DXF file path."""
    return str(Path(__file__).parent.parent / "examples" / "sample_dxf_files" / "simple_shapes.dxf")


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary output directory."""
    return str(tmp_path)
