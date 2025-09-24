from typing import Dict, List, Tuple, Set, Optional
from .dstar_lite import DStarLite

class MultiAgentCoordinator:
    """
    Coordinates multiple D* Lite planners for multi-agent navigation.
    Detects collisions but does not resolve them - just reports them.
    """

    def __init__(self, world):
        self.world = world
        self.planners = {}  # robot_id -> DStarLite instance
        self.paths = {}  # robot_id -> current planned path
        self.current_positions = {}  # robot_id -> current position
        self.goals = {}  # robot_id -> goal position

    def add_robot(self, robot_id: str, start: Tuple[int, int],
                  goal: Tuple[int, int]):
        """
        Add a robot to the system with its start and goal positions.
        """
        # Create planner for this robot
        planner = DStarLite(self.world, robot_id)
        planner.initialize(start, goal)

        # Store robot information
        self.planners[robot_id] = planner
        self.current_positions[robot_id] = start
        self.goals[robot_id] = goal
        self.world.robot_positions[robot_id] = start

        # Compute initial path
        success, reason = planner.compute_shortest_path()
        if success:
            self.paths[robot_id] = planner.get_path()
        else:
            self.paths[robot_id] = []
            print(f"Warning: No initial path found for robot {robot_id} - Reason: {reason}")

    def detect_collision_at_next_step(self) -> Optional[Tuple[str, str, str]]:
        """
        Check if robots will collide in the next step.
        Returns (robot1, robot2, collision_type) or None.
        collision_type can be 'same_cell', 'swap', or 'shear'.
        """
        robot_ids = list(self.paths.keys())

        if len(robot_ids) < 2:
            return None

        # Get next positions for each robot
        next_positions = {}
        for robot_id in robot_ids:
            path = self.paths.get(robot_id, [])
            if path and len(path) > 1:
                next_positions[robot_id] = path[1]
            else:
                # Robot stays at current position
                next_positions[robot_id] = self.current_positions[robot_id]

        # Check for collisions between pairs
        for i in range(len(robot_ids)):
            for j in range(i + 1, len(robot_ids)):
                robot1, robot2 = robot_ids[i], robot_ids[j]
                pos1 = next_positions[robot1]
                pos2 = next_positions[robot2]
                curr_pos1 = self.current_positions[robot1]
                curr_pos2 = self.current_positions[robot2]

                # Same cell collision - both trying to enter same cell
                if pos1 == pos2:
                    return (robot1, robot2, 'same_cell')

                # Swap collision - exchanging positions
                if pos1 == curr_pos2 and pos2 == curr_pos1:
                    return (robot1, robot2, 'swap')

                # Shear collision - one robot enters cell that another is leaving perpendicularly
                # Check if robot1 is entering robot2's current position
                if pos1 == curr_pos2:
                    # Robot2 must be moving (not stationary)
                    if pos2 != curr_pos2:
                        # Calculate movement directions
                        dx1 = pos1[0] - curr_pos1[0]
                        dy1 = pos1[1] - curr_pos1[1]
                        dx2 = pos2[0] - curr_pos2[0]
                        dy2 = pos2[1] - curr_pos2[1]

                        # If moving in same direction (series/convoy), it's valid - no collision
                        if (dx1, dy1) == (dx2, dy2):
                            continue

                        # Check if perpendicular (one moves horizontal, other vertical)
                        # This is a shear collision
                        if (dx1 == 0 and dy1 != 0 and dx2 != 0 and dy2 == 0) or \
                           (dx1 != 0 and dy1 == 0 and dx2 == 0 and dy2 != 0):
                            return (robot1, robot2, 'shear')

                # Check reverse case - robot2 entering robot1's current position
                if pos2 == curr_pos1:
                    # Robot1 must be moving
                    if pos1 != curr_pos1:
                        dx1 = pos1[0] - curr_pos1[0]
                        dy1 = pos1[1] - curr_pos1[1]
                        dx2 = pos2[0] - curr_pos2[0]
                        dy2 = pos2[1] - curr_pos2[1]

                        # Same direction = valid
                        if (dx1, dy1) == (dx2, dy2):
                            continue

                        # Perpendicular = shear collision
                        if (dx1 == 0 and dy1 != 0 and dx2 != 0 and dy2 == 0) or \
                           (dx1 != 0 and dy1 == 0 and dx2 == 0 and dy2 != 0):
                            return (robot2, robot1, 'shear')

        return None

    def recompute_paths(self, changed_cells=None):
        """
        Recompute paths for all robots.
        Each robot sees others as obstacles at their current positions.

        Args:
            changed_cells: Set of (x, y) cells that have changed (obstacles added/removed)
        """
        for robot_id in self.planners.keys():
            planner = self.planners[robot_id]

            # If cells have changed, inform the planner
            if changed_cells:
                planner.update_edge_costs(changed_cells)

            # Recompute path
            success, reason = planner.compute_shortest_path()

            # If no_path_exists, try a complete replan from scratch to escape local minima
            if not success and reason == "no_path_exists (goal unreachable)":
                print(f"Robot {robot_id}: no path found, attempting complete replan...")
                # Reinitialize the planner completely
                current_pos = self.current_positions[robot_id]
                goal = self.goals[robot_id]
                planner.initialize(current_pos, goal)
                # Try again with fresh state
                success, reason = planner.compute_shortest_path()
                if success:
                    print(f"Robot {robot_id}: Complete replan successful!")
                else:
                    print(f"Robot {robot_id}: Complete replan also failed - {reason}")

            if success:
                new_path = planner.get_path()
                if new_path:
                    self.paths[robot_id] = new_path
                else:
                    print(f"Warning: Failed to extract path for robot {robot_id}")
                    self.paths[robot_id] = []
            else:
                print(f"Warning: No path found for robot {robot_id} - Reason: {reason}")
                self.paths[robot_id] = []

    def step_simulation(self) -> Tuple[bool, Optional[Tuple[str, str, str]]]:
        """
        Move all robots one step along their paths.
        Returns (should_continue, collision_info).
        should_continue is False if all robots are at goal.
        collision_info is None or (robot1, robot2, collision_type) if collision would occur.
        """
        # First check for collisions in next step
        collision = self.detect_collision_at_next_step()
        if collision:
            return True, collision  # Don't move, report collision

        any_robot_moving = False

        # Move all robots one step along their current paths
        for robot_id, path in self.paths.items():
            if not path:
                continue

            current_pos = self.current_positions[robot_id]
            goal_pos = self.goals[robot_id]

            # Check if at goal
            if current_pos == goal_pos:
                continue

            any_robot_moving = True

            # Move to next position in path
            if len(path) > 1:
                new_pos = path[1]

                # Update positions
                self.current_positions[robot_id] = new_pos
                self.world.robot_positions[robot_id] = new_pos

                # Update planner's start position
                self.planners[robot_id].start = new_pos

                # Remove the first element from path since we moved
                self.paths[robot_id] = path[1:]

        # After moving, recompute paths from new positions
        if any_robot_moving:
            self.recompute_paths()

        return any_robot_moving, None

    def add_dynamic_obstacle(self, x: int, y: int):
        """
        Add an obstacle during execution and replan affected robots.
        This demonstrates D* Lite's incremental replanning capability.
        """
        self.world.add_obstacle(x, y)

        # Pass the changed cell so D* Lite can update properly
        self.recompute_paths(changed_cells={(x, y)})

    def set_new_goal(self, robot_id: str, new_goal: Tuple[int, int]):
        """
        Set a new goal for a robot and recompute its path.
        """
        if robot_id not in self.planners:
            print(f"Warning: Robot {robot_id} not found")
            return

        # Update the goal
        self.goals[robot_id] = new_goal

        # Get the planner and current position
        planner = self.planners[robot_id]
        current_pos = self.current_positions[robot_id]

        # Reinitialize the planner with new goal
        planner.initialize(current_pos, new_goal)

        # Recompute all paths
        self.recompute_paths()

        print(f"Set new goal for {robot_id}: {new_goal}")

    def get_robot_at_position(self, position: Tuple[int, int]) -> Optional[str]:
        """
        Get the robot at the given position, or None if no robot there.
        """
        for robot_id, robot_pos in self.current_positions.items():
            if robot_pos == position:
                return robot_id
        return None

    def get_status(self) -> Dict:
        """
        Get current status of all robots for debugging.
        """
        status = {}
        for robot_id in self.planners.keys():
            status[robot_id] = {
                'current': self.current_positions[robot_id],
                'goal': self.goals[robot_id],
                'path_length': len(self.paths[robot_id]) if self.paths[robot_id] else 0,
                'at_goal': self.current_positions[robot_id] == self.goals[robot_id]
            }
        return status