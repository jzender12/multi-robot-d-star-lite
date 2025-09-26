"""
Path planning algorithms module.

This module contains various path planning algorithms that can be used
for robot navigation. All algorithms implement the PathPlanner interface.
"""

from .base_planner import PathPlanner
from .dstar_lite_planner import DStarLitePlanner

# Simple registry of available planners
AVAILABLE_PLANNERS = {
    "D* Lite": DStarLitePlanner,
    # Add more planners here as they're implemented
}

# Default algorithm
DEFAULT_PLANNER = "D* Lite"


def get_planner_class(name: str):
    """Get planner class by name."""
    return AVAILABLE_PLANNERS.get(name)


def get_planner_names():
    """Get list of available planner names."""
    return list(AVAILABLE_PLANNERS.keys())


__all__ = ['PathPlanner', 'DStarLitePlanner', 'AVAILABLE_PLANNERS',
           'DEFAULT_PLANNER', 'get_planner_class', 'get_planner_names']