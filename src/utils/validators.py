"""Input validation utilities."""

from typing import Any, List
import re


def validate_file_path(filepath: str) -> bool:
    """
    Validate that a file path is valid.

    Args:
        filepath: File path to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(filepath, str):
        return False
    if len(filepath) == 0:
        return False
    return True


def validate_dxf_file(filepath: str) -> bool:
    """
    Validate that a file is a DXF file.

    Args:
        filepath: File path to validate.

    Returns:
        True if valid DXF file, False otherwise.
    """
    if not validate_file_path(filepath):
        return False
    return filepath.lower().endswith('.dxf')


def validate_positive_number(value: Any) -> bool:
    """
    Validate that a value is a positive number.

    Args:
        value: Value to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_coordinates(coords: tuple, dimensions: int = 2) -> bool:
    """
    Validate coordinate tuple.

    Args:
        coords: Coordinate tuple.
        dimensions: Expected number of dimensions.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(coords, (tuple, list)):
        return False
    if len(coords) != dimensions:
        return False
    try:
        [float(c) for c in coords]
        return True
    except (ValueError, TypeError):
        return False
