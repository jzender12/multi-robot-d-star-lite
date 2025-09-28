from typing import Dict, List, Tuple, Set, Optional
from .path_planners import get_planner_class, DEFAULT_PLANNER, get_planner_names

class MultiAgentCoordinator:
    """
    Coordinates multiple D* Lite planners for multi-agent navigation.
    Detects collisions but does not resolve them - just reports them.
    """

    def __init__(self, world):
        self.world = world
        self.planners = {}  # robot_id -> PathPlanner instance
        self.paths = {}  # robot_id -> current planned path
        self.current_positions = {}  # robot_id -> current position
        self.goals = {}  # robot_id -> goal position
        self.robot_algorithms = {}  # robot_id -> algorithm name

        # Collision blocking state management
        self.collision_blocked_robots = {}  # robot_id -> block reason
        # Collision tracking - using iterative detection now
        self.stuck_robots = set()  # Track robots with no path to goal

    def add_robot(self, robot_id: str, start: Tuple[int, int],
                  goal: Tuple[int, int]) -> bool:
        """
        Add a robot to the system with its start and goal positions.
        Returns False if position is occupied or max robots reached, True if successful.
        Maximum of 10 robots allowed (robot0-robot9).
        """
        # Check if we've reached the maximum number of robots
        if len(self.planners) >= 10:
            print(f"Cannot add {robot_id}: Maximum of 10 robots reached")
            return False

        # Check if start position is already occupied
        for existing_robot_id, pos in self.current_positions.items():
            if pos == start:
                print(f"Cannot add {robot_id}: Position {start} is occupied by {existing_robot_id}")
                return False

        # Create planner for this robot using default algorithm
        planner_class = get_planner_class(DEFAULT_PLANNER)
        planner = planner_class(self.world, robot_id)
        planner.initialize(start, goal)

        # Store robot information
        self.planners[robot_id] = planner
        self.robot_algorithms[robot_id] = DEFAULT_PLANNER
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

        return True

    def detect_collision_at_next_step(self, exclude_paused: bool = False) -> Optional[Tuple[str, str, str]]:
        """
        Check if robots will collide in the next step.
        Returns (robot1, robot2, collision_type) or None.
        collision_type can be 'same_cell', 'swap', or 'shear'.

        Args:
            exclude_paused: If True, skip paused robots from moving (but check collisions with them)
        """
        collisions = self.detect_all_collisions_at_next_step(exclude_paused)
        return collisions[0] if collisions else None

    def calculate_collisions(self) -> Dict[str, str]:
        """
        Calculate all collisions using iterative detection.

        Algorithm:
        1. Detect path-to-path collisions (same_cell, swap, shear)
        2. Iteratively detect blocked robot collisions until no new ones found

        Returns: Dict[robot_id, collision_reason]
        """
        colliding_robots = {}

        # Get all robot IDs with paths
        robot_ids = list(self.paths.keys())

        if len(robot_ids) < 2:
            return colliding_robots

        # Get next positions for each robot
        next_positions = {}
        for robot_id in robot_ids:
            path = self.paths.get(robot_id, [])
            if path and len(path) > 1:
                next_positions[robot_id] = path[1]
            else:
                # Robot stays at current position
                next_positions[robot_id] = self.current_positions[robot_id]

        # Pass 1: Detect path-to-path collisions
        for i in range(len(robot_ids)):
            for j in range(i + 1, len(robot_ids)):
                robot1, robot2 = robot_ids[i], robot_ids[j]

                pos1 = next_positions[robot1]
                pos2 = next_positions[robot2]
                curr_pos1 = self.current_positions[robot1]
                curr_pos2 = self.current_positions[robot2]

                # Same cell collision - both trying to enter same cell
                if pos1 == pos2:
                    colliding_robots[robot1] = "same_cell_collision"
                    colliding_robots[robot2] = "same_cell_collision"
                    continue

                # Swap collision - exchanging positions
                if pos1 == curr_pos2 and pos2 == curr_pos1:
                    colliding_robots[robot1] = "swap_collision"
                    colliding_robots[robot2] = "swap_collision"
                    continue

                # Shear collision - perpendicular crossing
                # Check if robot1 is entering robot2's current position
                if pos1 == curr_pos2 and pos2 != curr_pos2:
                    # Calculate movement directions
                    dx1 = pos1[0] - curr_pos1[0]
                    dy1 = pos1[1] - curr_pos1[1]
                    dx2 = pos2[0] - curr_pos2[0]
                    dy2 = pos2[1] - curr_pos2[1]

                    # If moving in same direction (series/convoy), it's valid - no collision
                    if (dx1, dy1) != (dx2, dy2):
                        # Check if perpendicular (one moves horizontal, other vertical)
                        if (dx1 == 0 and dy1 != 0 and dx2 != 0 and dy2 == 0) or \
                           (dx1 != 0 and dy1 == 0 and dx2 == 0 and dy2 != 0):
                            colliding_robots[robot1] = "shear_collision"
                            colliding_robots[robot2] = "shear_collision"
                            continue

                # Check reverse case - robot2 entering robot1's current position
                if pos2 == curr_pos1 and pos1 != curr_pos1:
                    dx1 = pos1[0] - curr_pos1[0]
                    dy1 = pos1[1] - curr_pos1[1]
                    dx2 = pos2[0] - curr_pos2[0]
                    dy2 = pos2[1] - curr_pos2[1]

                    # Same direction = valid
                    if (dx1, dy1) != (dx2, dy2):
                        # Perpendicular = shear collision
                        if (dx1 == 0 and dy1 != 0 and dx2 != 0 and dy2 == 0) or \
                           (dx1 != 0 and dy1 == 0 and dx2 == 0 and dy2 != 0):
                            colliding_robots[robot1] = "shear_collision"
                            colliding_robots[robot2] = "shear_collision"
                            continue

        # Pass 2: Iteratively detect blocked robot collisions
        # Continue until no new collisions found
        max_iterations = len(robot_ids)  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            new_collisions = {}

            # Check each non-colliding robot
            for robot_id in robot_ids:
                if robot_id in colliding_robots:
                    continue  # Already colliding

                # Check if this robot's next position is blocked by a colliding robot
                next_pos = next_positions[robot_id]

                for blocked_id in colliding_robots:
                    if self.current_positions[blocked_id] == next_pos:
                        # This robot is trying to move into a blocked robot's position
                        new_collisions[robot_id] = "blocked_robot_collision"
                        break

            if not new_collisions:
                break  # No new collisions found

            # Add new collisions to the set
            colliding_robots.update(new_collisions)
            iteration += 1

        return colliding_robots

    def detect_all_collisions_at_next_step(self, exclude_paused: bool = False) -> List[Tuple[str, str, str]]:
        """
        Check for ALL collisions that will occur in the next step.
        Returns a list of (robot1, robot2, collision_type) tuples.
        collision_type can be 'same_cell', 'swap', or 'shear'.

        Args:
            exclude_paused: If True, skip paused robots from moving (but check collisions with them)
        """
        robot_ids = list(self.paths.keys())
        collisions = []

        if len(robot_ids) < 2:
            return collisions

        # Get next positions for each robot
        next_positions = {}
        for robot_id in robot_ids:
            # If robot is collision blocked and we're excluding blocked, it stays in place
            if exclude_paused and robot_id in self.collision_blocked_robots:
                next_positions[robot_id] = self.current_positions[robot_id]
            else:
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

                # Skip checking between two collision blocked robots
                if exclude_paused and robot1 in self.collision_blocked_robots and robot2 in self.collision_blocked_robots:
                    continue

                pos1 = next_positions[robot1]
                pos2 = next_positions[robot2]
                curr_pos1 = self.current_positions[robot1]
                curr_pos2 = self.current_positions[robot2]

                # Same cell collision - both trying to enter same cell
                if pos1 == pos2:
                    collisions.append((robot1, robot2, 'same_cell'))
                    continue

                # Swap collision - exchanging positions
                if pos1 == curr_pos2 and pos2 == curr_pos1:
                    collisions.append((robot1, robot2, 'swap'))
                    continue

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
                            collisions.append((robot1, robot2, 'shear'))
                            continue

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
                            collisions.append((robot2, robot1, 'shear'))
                            continue

        return collisions

    def recompute_paths(self, changed_cells: Set[Tuple[int, int]] = None,
                       treat_paused_as_obstacles: bool = False):
        """
        Recompute paths for all robots.
        Each robot sees others as obstacles at their current positions.

        Args:
            changed_cells: Set of (x, y) cells that have changed (obstacles added/removed)
            treat_paused_as_obstacles: If True, treat paused robots as obstacles
        """
        # Store original robot positions if treating blocked as obstacles
        if treat_paused_as_obstacles:
            # Temporarily add collision blocked robots as obstacles
            for robot_id in self.collision_blocked_robots:
                pos = self.current_positions[robot_id]
                self.world.add_obstacle(pos[0], pos[1])

        for robot_id in self.planners.keys():
            planner = self.planners[robot_id]

            # Note: We DO replan for paused robots when obstacles change
            # This allows collision resolution via obstacle placement

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

        # Remove temporary obstacles
        if treat_paused_as_obstacles:
            for robot_id in self.collision_blocked_robots:
                pos = self.current_positions[robot_id]
                self.world.remove_obstacle(pos[0], pos[1])

        # Update stuck robots after recomputing paths
        self.detect_stuck_robots()

    def detect_stuck_robots(self) -> set:
        """
        Detect robots that are stuck (no path to goal and not at goal).
        Returns a set of stuck robot IDs.
        Updates self.stuck_robots instance variable.
        """
        stuck = set()
        for robot_id in self.planners:
            current_pos = self.current_positions[robot_id]
            goal_pos = self.goals[robot_id]

            # If at goal, not stuck
            if current_pos == goal_pos:
                continue

            # If no path, empty path, or path only contains current position, robot is stuck
            path = self.paths.get(robot_id, [])
            if not path or len(path) == 0 or (len(path) == 1 and path[0] == current_pos):
                stuck.add(robot_id)

        self.stuck_robots = stuck
        return stuck

    def step_simulation(self) -> Tuple[bool, Optional[Tuple[str, str, str]], List[str], Dict[str, str]]:
        """
        Move all robots one step along their paths.
        Returns (should_continue, collision_info, stuck_robots, collision_blocked_robots).
        should_continue is False if all robots are at goal.
        collision_info is None or (robot1, robot2, collision_type) if collision would occur.
        stuck_robots is a list of robot IDs that have no valid path but are not at goal.
        collision_blocked_robots is a dict of robot_id -> block reason.
        """
        # Calculate all collisions using the new iterative method
        new_collisions = self.calculate_collisions()

        # Update collision blocked robots with new collisions
        self.collision_blocked_robots = new_collisions

        # For backward compatibility, create a collision tuple for the first collision
        collision_detected = None
        if new_collisions:
            # Just report the first collision found for backward compatibility
            first_robot = list(new_collisions.keys())[0]
            collision_detected = (first_robot, "unknown", new_collisions[first_robot].replace("_collision", ""))

        any_robot_moving = False

        # Detect stuck robots (updates self.stuck_robots)
        self.detect_stuck_robots()
        stuck_robots = list(self.stuck_robots)

        # Move all non-blocked robots one step along their current paths
        for robot_id, path in self.paths.items():
            # Skip collision blocked robots
            if robot_id in self.collision_blocked_robots:
                continue

            current_pos = self.current_positions[robot_id]
            goal_pos = self.goals[robot_id]

            # Check if at goal
            if current_pos == goal_pos:
                continue  # At goal, not stuck

            # Check if robot has no path (stuck)
            if not path or len(path) == 0:
                # Already tracked in detect_stuck_robots()
                continue  # Can't move, but track as stuck

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
        if any_robot_moving or stuck_robots:
            self.recompute_paths()

        # Determine if we should continue
        # Continue if any robot is moving OR if any robot is stuck (waiting for path) OR robots are collision blocked
        should_continue = any_robot_moving or len(stuck_robots) > 0 or len(self.collision_blocked_robots) > 0

        # Return the collision detected this step (if any)
        return should_continue, collision_detected, stuck_robots, self.collision_blocked_robots

    def add_dynamic_obstacle(self, x: int, y: int):
        """
        Add an obstacle during execution and replan affected robots.
        This demonstrates D* Lite's incremental replanning capability.
        """
        self.world.add_obstacle(x, y)

        # Pass the changed cell so D* Lite can update properly
        self.recompute_paths(changed_cells={(x, y)})

        # Collisions will be recalculated on next step with new paths

    def remove_dynamic_obstacle(self, x: int, y: int):
        """
        Remove an obstacle during execution and replan affected robots.
        """
        self.world.remove_obstacle(x, y)

        # Pass the changed cell so D* Lite can update properly
        self.recompute_paths(changed_cells={(x, y)})

        # Collisions will be recalculated on next step with new paths

    def set_new_goal(self, robot_id: str, new_goal: Tuple[int, int]) -> bool:
        """
        Set a new goal for a robot and recompute its path.
        Returns True if successful, False if goal is invalid.
        """
        if robot_id not in self.planners:
            print(f"Warning: Robot {robot_id} not found")
            return False

        # Validation: Check if goal is on an obstacle
        if new_goal in self.world.static_obstacles:
            print(f"Cannot set goal at {new_goal}: Position has an obstacle")
            return False

        # Validation: Check if goal conflicts with another robot's goal
        for other_robot_id, other_goal in self.goals.items():
            if other_robot_id != robot_id and other_goal == new_goal:
                print(f"Cannot set goal at {new_goal}: Another robot ({other_robot_id}) has this goal")
                return False

        # Update the goal
        self.goals[robot_id] = new_goal

        # Unblock the robot if it was collision blocked (goal change is user intervention)
        if robot_id in self.collision_blocked_robots:
            del self.collision_blocked_robots[robot_id]

        # Get the planner and current position
        planner = self.planners[robot_id]
        current_pos = self.current_positions[robot_id]

        # Reinitialize the planner with new goal
        planner.initialize(current_pos, new_goal)

        # Recompute all paths
        self.recompute_paths()

        print(f"Set new goal for {robot_id}: {new_goal}")
        return True

    def change_robot_planner(self, robot_id: str, planner_name: str) -> bool:
        """
        Change the path planner for a specific robot.

        Args:
            robot_id: ID of the robot
            planner_name: Name of the new planner algorithm

        Returns:
            True if successful, False otherwise
        """
        if robot_id not in self.planners:
            print(f"Warning: Robot {robot_id} not found")
            return False

        planner_class = get_planner_class(planner_name)
        if not planner_class:
            print(f"Warning: Unknown planner {planner_name}")
            return False

        # Create new planner with current position and goal
        current_pos = self.current_positions[robot_id]
        goal = self.goals[robot_id]

        new_planner = planner_class(self.world, robot_id)
        new_planner.initialize(current_pos, goal)

        # Replace the planner
        self.planners[robot_id] = new_planner
        self.robot_algorithms[robot_id] = planner_name

        # Recompute path with new planner
        success, reason = new_planner.compute_shortest_path()
        if success:
            self.paths[robot_id] = new_planner.get_path()
        else:
            self.paths[robot_id] = []
            print(f"Warning: No path found with {planner_name} for {robot_id} - {reason}")

        print(f"Changed {robot_id} to use {planner_name} algorithm")
        return True

    def remove_robot(self, robot_id: str) -> bool:
        """
        Remove a robot from the system.
        Returns True if successful, False if robot doesn't exist.
        """
        if robot_id not in self.planners:
            print(f"Warning: Robot {robot_id} not found")
            return False

        # Remove from all tracking dictionaries
        del self.planners[robot_id]
        del self.current_positions[robot_id]
        del self.goals[robot_id]
        del self.robot_algorithms[robot_id]

        if robot_id in self.paths:
            del self.paths[robot_id]

        if robot_id in self.world.robot_positions:
            del self.world.robot_positions[robot_id]

        print(f"Removed robot {robot_id}")

        # Recompute paths for remaining robots
        self.recompute_paths()

        return True

    def get_next_robot_id(self) -> Optional[str]:
        """
        Generate the next available robot ID.
        Returns robotN where N is the next available number (0-9).
        Returns None if maximum robots reached.
        """
        existing_ids = set(self.planners.keys())

        # Check if we've reached the maximum of 10 robots
        if len(existing_ids) >= 10:
            return None

        # Find the next available number (0-9)
        for i in range(10):
            if f"robot{i}" not in existing_ids:
                return f"robot{i}"

        return None  # Should not reach here if logic is correct

    def clear_all_robots(self):
        """
        Remove all robots from the system.
        """
        # Clear all dictionaries
        self.planners.clear()
        self.paths.clear()
        self.current_positions.clear()
        self.goals.clear()
        self.robot_algorithms.clear()
        self.world.robot_positions.clear()

        print("Cleared all robots")

    def resize_world(self, new_width: int, new_height: int):
        """
        Resize world to new dimensions with clean slate.
        Clears everything and places robot1 at start.
        """
        # Clear all robots and obstacles
        self.clear_all_robots()

        # Resize and clear the world
        self.world.resize(new_width, new_height)
        self.world.static_obstacles.clear()
        self.world.grid.fill(0)  # All empty cells

        # Add robot0 at top-left with goal at bottom-right
        self.add_robot("robot0",
                       start=(0, 0),
                       goal=(new_width - 1, new_height - 1))

        print(f"Resized world to {new_width}x{new_height} - Clean slate with robot0")

    def reset_to_default(self):
        """
        Reset to default 10x10 clean slate.
        """
        self.resize_world(10, 10)

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

    # ==================== Collision Blocking Methods ====================

    def block_robot_for_collision(self, robot_id: str, reason: str):
        """Block a specific robot due to collision with a given reason."""
        if robot_id in self.planners:
            self.collision_blocked_robots[robot_id] = reason

    def unblock_robot(self, robot_id: str):
        """Unblock a collision blocked robot."""
        if robot_id in self.collision_blocked_robots:
            del self.collision_blocked_robots[robot_id]

    def is_robot_blocked(self, robot_id: str) -> bool:
        """Check if a robot is collision blocked."""
        return robot_id in self.collision_blocked_robots

    def get_collision_blocked_robots(self) -> List[str]:
        """Get list of all collision blocked robots."""
        return list(self.collision_blocked_robots.keys())

    def get_block_reason(self, robot_id: str) -> Optional[str]:
        """Get the reason why a robot is collision blocked."""
        return self.collision_blocked_robots.get(robot_id)

