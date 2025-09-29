#!/usr/bin/env python3
"""
Color generation utilities for multi-robot visualization.
Provides distinct colors for robots, goals, and paths.
"""

import colorsys
import math
from typing import Tuple, Dict

# Predefined colors for first two robots
PREDEFINED_COLORS = {
    "robot1": (0, 100, 200),    # Blue
    "robot2": (200, 50, 0),      # Red
}

# Cache for generated colors
_color_cache: Dict[str, Tuple[int, int, int]] = {}


def get_robot_colors() -> Dict[str, Tuple[int, int, int]]:
    """
    Get predefined robot colors.
    Returns dictionary of robot IDs to RGB colors.
    """
    return PREDEFINED_COLORS.copy()


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """
    Convert HSV color to RGB.

    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        v: Value (0-1)

    Returns:
        RGB tuple with values 0-255
    """
    # Normalize hue to 0-1 range
    h_norm = h / 360.0

    # Convert to RGB (returns 0-1 range)
    r, g, b = colorsys.hsv_to_rgb(h_norm, s, v)

    # Convert to 0-255 range
    return (int(r * 255), int(g * 255), int(b * 255))


def generate_robot_color(robot_id: str) -> Tuple[int, int, int]:
    """
    Generate a unique color for a robot.

    Args:
        robot_id: Robot identifier (e.g., "robot3")

    Returns:
        RGB tuple with values 0-255
    """
    # Check predefined colors
    if robot_id in PREDEFINED_COLORS:
        return PREDEFINED_COLORS[robot_id]

    # Check cache
    if robot_id in _color_cache:
        return _color_cache[robot_id]

    # Extract robot number
    try:
        if robot_id.startswith("robot"):
            robot_num = int(robot_id[5:])
        else:
            robot_num = hash(robot_id) % 100
    except (ValueError, IndexError):
        robot_num = hash(robot_id) % 100

    # Generate color using HSV
    # Spread hues evenly around the color wheel
    # Skip first two positions (reserved for predefined)
    if robot_num <= 2:
        robot_num = 3  # Default for invalid numbers

    # Calculate hue based on robot number
    # Start at 120 (green) to avoid blue/red
    # Distribute evenly around remaining color space
    hue_offset = 120  # Start at green
    hue_spacing = 240 / max(10, robot_num)  # Spread across 240 degrees
    hue = (hue_offset + (robot_num - 3) * hue_spacing) % 360

    # Use high saturation and value for vibrant colors
    saturation = 0.8
    value = 0.9

    color = hsv_to_rgb(hue, saturation, value)

    # Cache the result
    _color_cache[robot_id] = color

    return color


def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate Euclidean distance between two colors.

    Args:
        color1: First RGB color
        color2: Second RGB color

    Returns:
        Distance value
    """
    r1, g1, b1 = color1
    r2, g2, b2 = color2

    return math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)


def ensure_color_contrast(color: Tuple[int, int, int],
                         background: Tuple[int, int, int]) -> bool:
    """
    Check if color has sufficient contrast with background.

    Args:
        color: RGB color to check
        background: Background RGB color

    Returns:
        True if contrast is sufficient
    """
    # Calculate distance
    dist = color_distance(color, background)

    # Minimum distance for good contrast
    MIN_DISTANCE = 100

    return dist >= MIN_DISTANCE


def get_color_set(robot_id: str) -> Dict[str, Tuple[int, int, int]]:
    """
    Get a complete color set for a robot (robot, goal, path colors).

    Args:
        robot_id: Robot identifier

    Returns:
        Dictionary with 'robot', 'goal', and 'path' colors
    """
    # Get base robot color
    robot_color = generate_robot_color(robot_id)

    # Generate related colors
    # Goal: Lighter version (higher value, lower saturation)
    # Path: Even lighter version

    # Convert to HSV for manipulation
    r, g, b = [c / 255.0 for c in robot_color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # Goal color: reduce saturation, increase value
    goal_h = h
    goal_s = max(0.3, s * 0.5)
    goal_v = min(1.0, v * 1.2)
    goal_color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(goal_h, goal_s, goal_v))

    # Path color: further reduce saturation, max value
    path_h = h
    path_s = max(0.2, s * 0.3)
    path_v = min(1.0, v * 1.3)
    path_color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(path_h, path_s, path_v))

    return {
        "robot": robot_color,
        "goal": goal_color,
        "path": path_color
    }


def get_hue_for_robot(robot_id: str, total_robots: int = 10) -> float:
    """
    Get hue value for a robot based on even distribution.

    Args:
        robot_id: Robot identifier
        total_robots: Total number of robots for spacing

    Returns:
        Hue value (0-360)
    """
    try:
        if robot_id.startswith("robot"):
            robot_num = int(robot_id[5:])
        else:
            robot_num = 3
    except (ValueError, IndexError):
        robot_num = 3

    # For first two robots, return fixed hues
    if robot_num == 1:
        return 210  # Blue hue
    elif robot_num == 2:
        return 10   # Red hue

    # Distribute remaining robots evenly
    # Start after red/blue, spread across spectrum
    spacing = 360 / max(total_robots, 10)
    return ((robot_num - 1) * spacing) % 360


def clear_color_cache():
    """
    Clear the color cache.
    Useful for testing or resetting colors.
    """
    _color_cache.clear()