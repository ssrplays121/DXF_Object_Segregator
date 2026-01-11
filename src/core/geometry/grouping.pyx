"""Cython implementation of object grouping."""

from typing import List, Dict


def group_objects_by_proximity(object_positions: List[tuple],
                               proximity_threshold: float = 1.0) -> List[List[int]]:
    """
    Group objects by proximity.

    Args:
        object_positions: List of (x, y) center positions.
        proximity_threshold: Maximum distance for grouping.

    Returns:
        List of object groups (each group is a list of object indices).
    """
    cdef int num_objects = len(object_positions)
    cdef list groups = []
    cdef list visited = [False] * num_objects
    cdef int i, j
    cdef double dx, dy, dist_sq

    for i in range(num_objects):
        if not visited[i]:
            group = [i]
            visited[i] = True

            for j in range(i + 1, num_objects):
                if not visited[j]:
                    dx = object_positions[i][0] - object_positions[j][0]
                    dy = object_positions[i][1] - object_positions[j][1]
                    dist_sq = dx * dx + dy * dy

                    if dist_sq <= proximity_threshold * proximity_threshold:
                        group.append(j)
                        visited[j] = True

            groups.append(group)

    return groups


def group_by_attribute(objects: List[Dict], attribute: str) -> Dict[str, List[int]]:
    """
    Group objects by a common attribute.

    Args:
        objects: List of object dictionaries.
        attribute: Attribute key to group by.

    Returns:
        Dictionary mapping attribute values to object indices.
    """
    groups = {}
    for idx, obj in enumerate(objects):
        value = obj.get(attribute)
        if value not in groups:
            groups[value] = []
        groups[value].append(idx)
    return groups
