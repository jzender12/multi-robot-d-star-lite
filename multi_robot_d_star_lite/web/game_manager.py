"""
GameManager: Wrapper around the existing coordinator for WebSocket communication.
"""
from typing import Dict, List, Tuple, Optional, Any

from ..core.coordinator import MultiAgentCoordinator
from ..core.world import GridWorld


class GameManager:
    """Manages game state and wraps coordinator for WebSocket communication."""

    def __init__(self, width: int = 10, height: int = 10):
        """Initialize game with default setup."""
        self.world = GridWorld(width, height)
        self.coordinator = MultiAgentCoordinator(self.world)
        self.step_count = 0
        self.paused = True  # Start paused

        # Initialize robot ID pool with IDs 0-9 in reverse order (so pop gives 0 first)
        self.robot_id_pool = list(range(9, -1, -1))  # [9,8,7,6,5,4,3,2,1,0]

        # Start with clean slate - no robots

    def get_state(self) -> Dict[str, Any]:
        """Get current game state as JSON-serializable dict."""
        # Always detect stuck robots, even when paused
        self.coordinator.detect_stuck_robots()

        # Get robots in the correct format for frontend
        robots = {}
        for robot_id, pos in self.coordinator.current_positions.items():
            robots[robot_id] = {
                "id": robot_id,
                "position": list(pos),
                "goal": list(self.coordinator.goals[robot_id]),
                "path": self.coordinator.paths.get(robot_id, []),
                "is_stuck": robot_id in self.coordinator.stuck_robots,
                "is_paused": robot_id in self.coordinator.collision_blocked_robots
            }

        return {
            "type": "state",
            "width": self.world.width,
            "height": self.world.height,
            "robots": robots,
            "obstacles": [[x, y] for x, y in self.world.static_obstacles],
            "paused": self.paused,
            "collision_info": self._get_collision_info(),
            "stuck_robots": list(self.coordinator.stuck_robots),
            "collision_blocked_robots": list(self.coordinator.collision_blocked_robots.keys())
        }

    def get_robot_positions_and_goals(self) -> Dict[str, Dict]:
        """Get all robot positions and goals."""
        result = {}
        for robot_id, pos in self.coordinator.current_positions.items():
            result[robot_id] = {
                "pos": list(pos),
                "goal": list(self.coordinator.goals[robot_id])
            }
        return result

    def get_robot_positions(self) -> Dict[str, List[int]]:
        """Get all robot positions as lists."""
        return {
            robot_id: list(pos)
            for robot_id, pos in self.coordinator.current_positions.items()
        }

    def _serialize_paths(self) -> Dict[str, List[List[int]]]:
        """Serialize paths to JSON format."""
        result = {}
        for robot_id, path in self.coordinator.paths.items():
            if path:
                result[robot_id] = [[x, y] for x, y in path]
            else:
                result[robot_id] = []
        return result

    def _get_collision_info(self) -> Optional[List[Dict]]:
        """Get collision information in frontend-compatible format using collision_details."""
        if not hasattr(self.coordinator, 'collision_details') or not self.coordinator.collision_details:
            return None

        # Use collision_details directly - it already has the correct format
        collisions = []
        for detail in self.coordinator.collision_details:
            collision_data = {
                "type": detail["type"],
                "robots": detail["robots"]
            }

            # Add position info for same_cell and shear collisions
            if "position" in detail:
                collision_data["position"] = list(detail["position"])

            # Add positions for swap collision
            if "positions" in detail:
                collision_data["positions"] = [list(p) for p in detail["positions"]]

            # Add blocked_by info for blocked_robot collisions
            if "blocked_by" in detail:
                collision_data["blocked_by"] = detail["blocked_by"]

            collisions.append(collision_data)

        return collisions if collisions else None

    def step(self) -> Dict[str, Any]:
        """Advance simulation by one step."""
        if not self.paused:
            should_continue, collision, stuck_robots, collision_blocked_robots = self.coordinator.step_simulation()
            self.step_count += 1
        return self.get_state()

    def add_obstacle(self, x: int, y: int) -> Dict[str, Any]:
        """Add obstacle at position."""
        self.coordinator.add_dynamic_obstacle(x, y)
        return self.get_state()

    def remove_obstacle(self, x: int, y: int) -> Dict[str, Any]:
        """Remove obstacle at position."""
        self.coordinator.remove_dynamic_obstacle(x, y)
        return self.get_state()

    def set_goal(self, robot_id: str, x: int, y: int) -> bool:
        """Set new goal for robot."""
        return self.coordinator.set_new_goal(robot_id, (x, y))

    def add_robot(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[str]:
        """Add new robot to the system."""
        # Check if we have available robot IDs
        if not self.robot_id_pool:
            return None  # No available robot IDs (max 10 robots)

        # Get next available robot ID from pool
        robot_num = self.robot_id_pool.pop()
        robot_id = f"robot{robot_num}"

        success = self.coordinator.add_robot(robot_id, start=start, goal=goal)
        if success:
            self.coordinator.recompute_paths()
            return robot_id
        else:
            # Return ID to pool if add failed
            self.robot_id_pool.append(robot_num)
            return None

    def pause(self):
        """Pause simulation."""
        self.paused = True

    def resume(self):
        """Resume simulation."""
        self.paused = False

    def resize_arena(self, width: int, height: int):
        """Resize the arena to new dimensions."""
        self.coordinator.resize_world(width, height)
        # Update our world reference since coordinator creates a new one
        self.world = self.coordinator.world
        # Reset robot ID pool to full set and ensure paused
        self.robot_id_pool = list(range(9, -1, -1))  # [9,8,7,6,5,4,3,2,1,0]
        self.paused = True
        return self.get_state()

    def remove_robot(self, robot_id: str) -> bool:
        """Remove a robot from the system."""
        success = self.coordinator.remove_robot(robot_id)
        if success:
            # Return robot ID to pool for reuse
            try:
                robot_num = int(robot_id.replace("robot", ""))
                self.robot_id_pool.append(robot_num)
            except ValueError:
                pass  # Invalid robot ID format, ignore
            self.coordinator.recompute_paths()
        return success

    def clear_obstacles(self):
        """Clear all obstacles from the arena."""
        self.world.static_obstacles.clear()
        self.coordinator.recompute_paths()
        return self.get_state()

    def reset(self):
        """Reset to initial state."""
        self.__init__(self.world.width, self.world.height)