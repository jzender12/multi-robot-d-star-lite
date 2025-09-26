"""Multi-Robot D* Lite Path Planning System

A Python implementation of D* Lite algorithm for multi-robot path planning
with collision detection on a 2D grid.
"""

from .world import GridWorld, CellType
from .path_planners.dstar_lite_planner import DStarLitePlanner
from .coordinator import MultiAgentCoordinator
from .visualizer import GridVisualizer
from .simple_visualizer import SimpleVisualizer

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = [
    "GridWorld",
    "CellType",
    "DStarLitePlanner",
    "MultiAgentCoordinator",
    "GridVisualizer",
    "SimpleVisualizer"
]