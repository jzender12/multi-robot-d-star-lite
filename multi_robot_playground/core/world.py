import numpy as np
from enum import Enum
from typing import Tuple, List, Optional, Set

class CellType(Enum):
    """Represents the state of each cell in the grid"""
    EMPTY = 0
    OBSTACLE = 1
    ROBOT = 2
    GOAL = 3

class GridWorld:
    """
    Manages the 2D grid environment for robot navigation.
    Coordinates use (x, y) where x is column and y is row.
    Origin (0, 0) is at top-left corner.
    Uses 4-connected grid (Manhattan movement only).
    """

    def __init__(self, width: int = 10, height: int = 10):
        self.width = width
        self.height = height
        # Initialize empty grid
        self.grid = np.full((height, width), CellType.EMPTY.value, dtype=np.int8)
        self.static_obstacles = set()  # Permanent obstacles
        self.robot_positions = {}  # robot_id -> (x, y)

    def add_obstacle(self, x: int, y: int):
        """Add a static obstacle to the grid"""
        if self.is_valid(x, y):
            self.grid[y, x] = CellType.OBSTACLE.value
            self.static_obstacles.add((x, y))

    def remove_obstacle(self, x: int, y: int):
        """Remove an obstacle (useful for dynamic environments)"""
        if (x, y) in self.static_obstacles:
            self.grid[y, x] = CellType.EMPTY.value
            self.static_obstacles.remove((x, y))

    def is_valid(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, x: int, y: int, exclude_robot: Optional[str] = None) -> bool:
        """
        Check if a cell is traversable.
        Only checks static obstacles, NOT robots.
        This allows robots to plan paths that may collide.
        """
        if not self.is_valid(x, y):
            return False

        # Check static obstacles only
        if (x, y) in self.static_obstacles:
            return False

        # Don't check robot positions - they're not obstacles for planning
        # This allows collision detection to catch when paths overlap

        return True

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        """
        Get all valid neighbors and their movement costs.
        Returns list of (nx, ny, cost) tuples.
        Using 4-connected grid (Manhattan movement only, no diagonals).
        """
        neighbors = []

        # Define only 4 cardinal directions with cost = 1
        directions = [
            ((0, 1), 1.0),   # Down
            ((0, -1), 1.0),  # Up
            ((1, 0), 1.0),   # Right
            ((-1, 0), 1.0),  # Left
            # NO DIAGONAL MOVEMENTS
        ]

        for (dx, dy), cost in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny):
                neighbors.append((nx, ny, cost))

        return neighbors

    def resize(self, new_width: int, new_height: int):
        """
        Resize the world to new dimensions.
        Preserves obstacles and robots within bounds.
        Enforces minimum and maximum size limits.
        """
        # Enforce size limits
        MIN_SIZE = 3
        MAX_SIZE = 30

        new_width = max(MIN_SIZE, min(MAX_SIZE, new_width))
        new_height = max(MIN_SIZE, min(MAX_SIZE, new_height))

        # Create new grid
        new_grid = np.full((new_height, new_width), CellType.EMPTY.value, dtype=np.int8)

        # Preserve obstacles within bounds
        new_obstacles = set()
        for x, y in self.static_obstacles:
            if 0 <= x < new_width and 0 <= y < new_height:
                new_obstacles.add((x, y))
                new_grid[y, x] = CellType.OBSTACLE.value

        # Preserve robots within bounds
        new_robot_positions = {}
        for robot_id, (x, y) in self.robot_positions.items():
            if 0 <= x < new_width and 0 <= y < new_height:
                new_robot_positions[robot_id] = (x, y)

        # Update world properties
        self.width = new_width
        self.height = new_height
        self.grid = new_grid
        self.static_obstacles = new_obstacles
        self.robot_positions = new_robot_positions