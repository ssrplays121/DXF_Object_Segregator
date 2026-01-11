"""Helper functions and utilities."""

from typing import List, Tuple, Any


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten a nested list.

    Args:
        nested_list: List to flatten.

    Returns:
        Flattened list.
    """
    result = []
    for item in nested_list:
        if isinstance(item, (list, tuple)):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def group_by_key(items: List[dict], key: str) -> dict:
    """
    Group items by dictionary key.

    Args:
        items: List of dictionaries.
        key: Key to group by.

    Returns:
        Dictionary with grouped items.
    """
    groups = {}
    for item in items:
        value = item.get(key)
        if value not in groups:
            groups[value] = []
        groups[value].append(item)
    return groups


def calculate_distance(p1: Tuple[float, float],
                       p2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        p1: First point (x, y).
        p2: Second point (x, y).

    Returns:
        Distance between points.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return (dx * dx + dy * dy) ** 0.5


def get_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box of points.

    Args:
        points: List of (x, y) points.

    Returns:
        Tuple of (min_x, min_y, max_x, max_y).
    """
    if not points:
        return (0, 0, 0, 0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return (min(xs), min(ys), max(xs), max(ys))
