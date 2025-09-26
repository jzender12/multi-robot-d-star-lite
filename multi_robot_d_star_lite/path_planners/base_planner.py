"""
Abstract base class for path planning algorithms.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Set


class PathPlanner(ABC):
    """
    Abstract base class for all path planning algorithms.

    All path planners must implement this interface to ensure
    compatibility with the multi-agent coordinator.
    """

    def __init__(self, world, robot_id: str):
        """
        Initialize the path planner.

        Args:
            world: The grid world environment
            robot_id: Unique identifier for the robot using this planner
        """
        self.world = world
        self.robot_id = robot_id
        self.start = None
        self.goal = None

    @abstractmethod
    def initialize(self, start: Tuple[int, int], goal: Tuple[int, int]):
        """
        Initialize planner with start and goal positions.

        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
        """
        pass

    @abstractmethod
    def compute_shortest_path(self) -> Tuple[bool, str]:
        """
        Compute path from start to goal.

        Returns:
            Tuple of (success, reason)
            - success: True if path found, False otherwise
            - reason: String describing the result or failure reason
        """
        pass

    @abstractmethod
    def get_path(self) -> List[Tuple[int, int]]:
        """
        Get the computed path.

        Returns:
            List of (x, y) positions from start to goal.
            Empty list if no path exists.
        """
        pass

    @abstractmethod
    def update_edge_costs(self, changed_cells: Set[Tuple[int, int]]):
        """
        Update planner when obstacles change.

        This method is called when the environment changes dynamically.
        Algorithms that support incremental replanning should update
        their internal state accordingly.

        Args:
            changed_cells: Set of (x, y) cells that have changed
        """
        pass

    @abstractmethod
    def get_algorithm_name(self) -> str:
        """
        Return name of the algorithm for display purposes.

        Returns:
            String name of the algorithm (e.g., "D* Lite", "A*")
        """
        pass