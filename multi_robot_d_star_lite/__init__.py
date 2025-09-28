"""Multi-Robot D* Lite Path Planning System

A Python implementation of D* Lite algorithm for multi-robot path planning
with collision detection on a 2D grid.
"""

from .core.world import GridWorld, CellType
from .core.path_planners.dstar_lite_planner import DStarLitePlanner
from .core.coordinator import MultiAgentCoordinator

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = [
    "GridWorld",
    "CellType",
    "DStarLitePlanner",
    "MultiAgentCoordinator"
]