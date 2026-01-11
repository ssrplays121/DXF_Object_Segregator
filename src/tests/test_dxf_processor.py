"""Tests for DXF processor."""

import pytest
from core.dxf_processor import DXFProcessor


class TestDXFProcessor:
    """Test cases for DXFProcessor."""

    def test_processor_initialization(self, sample_dxf_file):
        """Test processor initialization."""
        processor = DXFProcessor(sample_dxf_file)
        assert processor.filepath == sample_dxf_file
        assert processor.doc is None
        assert processor.msp is None

    def test_load_file(self, sample_dxf_file):
        """Test loading a DXF file."""
        processor = DXFProcessor(sample_dxf_file)
        processor.load()
        assert processor.doc is not None
        assert processor.msp is not None

    def test_parse_entities(self, sample_dxf_file):
        """Test parsing entities from DXF file."""
        processor = DXFProcessor(sample_dxf_file)
        entities = processor.parse()
        assert isinstance(entities, list)

    def test_get_layers(self, sample_dxf_file):
        """Test getting layers from DXF file."""
        processor = DXFProcessor(sample_dxf_file)
        layers = processor.get_layers()
        assert isinstance(layers, list)
        assert "0" in layers  # Layer 0 always exists
