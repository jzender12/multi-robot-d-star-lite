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

        # Partial pausing state management
        self.paused_robots = {}  # robot_id -> pause reason
        self.collision_pairs = []  # List of (robot1, robot2, collision_type) tuples
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
        robot_ids = list(self.paths.keys())

        if len(robot_ids) < 2:
            return None

        # Get next positions for each robot
        next_positions = {}
        for robot_id in robot_ids:
            # If robot is paused and we're excluding paused, it stays in place
            if exclude_paused and robot_id in self.paused_robots:
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

                # Skip checking between two paused robots
                if exclude_paused and robot1 in self.paused_robots and robot2 in self.paused_robots:
                    continue

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

    def recompute_paths(self, changed_cells: Set[Tuple[int, int]] = None,
                       treat_paused_as_obstacles: bool = False):
        """
        Recompute paths for all robots.
        Each robot sees others as obstacles at their current positions.

        Args:
            changed_cells: Set of (x, y) cells that have changed (obstacles added/removed)
            treat_paused_as_obstacles: If True, treat paused robots as obstacles
        """
        # Store original robot positions if treating paused as obstacles
        if treat_paused_as_obstacles:
            # Temporarily add paused robots as obstacles
            for robot_id in self.paused_robots:
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
            for robot_id in self.paused_robots:
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
        Returns (should_continue, collision_info, stuck_robots, paused_robots).
        should_continue is False if all robots are at goal.
        collision_info is None or (robot1, robot2, collision_type) if collision would occur.
        stuck_robots is a list of robot IDs that have no valid path but are not at goal.
        paused_robots is a dict of robot_id -> pause reason.
        """
        # First check for collisions in next step (only for non-paused robots)
        collision_detected = self.detect_collision_at_next_step(exclude_paused=True)
        if collision_detected:
            # Pause only the robots involved in the collision
            robot1, robot2, collision_type = collision_detected
            self.pause_robots_for_collision((robot1, robot2, collision_type))
            # Don't return here - let other robots continue moving

        any_robot_moving = False

        # Detect stuck robots (updates self.stuck_robots)
        self.detect_stuck_robots()
        stuck_robots = list(self.stuck_robots)

        # Check for recovery of paused robots
        self.check_paused_robot_recovery()

        # Move all non-paused robots one step along their current paths
        for robot_id, path in self.paths.items():
            # Skip paused robots
            if robot_id in self.paused_robots:
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

        # After moving, clean up collision pairs where robots have moved apart
        # This allows robots to auto-resume when collision is resolved
        if self.collision_pairs:
            remaining_pairs = []
            for pair in self.collision_pairs:
                robot1, robot2, collision_type = pair

                # Check if collision would still occur at next step
                # This is more accurate than just checking distance
                next_collision = self.detect_collision_at_next_step(exclude_paused=False)

                # Keep pair if these specific robots would still collide
                if next_collision:
                    next_r1, next_r2, _ = next_collision
                    if (robot1 in [next_r1, next_r2]) and (robot2 in [next_r1, next_r2]):
                        remaining_pairs.append(pair)
                # If no collision detected between these robots, they can be cleared

            self.collision_pairs = remaining_pairs

        # After moving, recompute paths from new positions
        if any_robot_moving or stuck_robots:
            self.recompute_paths()

        # Determine if we should continue
        # Continue if any robot is moving OR if any robot is stuck (waiting for path) OR robots are paused
        should_continue = any_robot_moving or len(stuck_robots) > 0 or len(self.paused_robots) > 0

        # Return the collision detected this step (if any)
        return should_continue, collision_detected, stuck_robots, self.paused_robots

    def add_dynamic_obstacle(self, x: int, y: int):
        """
        Add an obstacle during execution and replan affected robots.
        This demonstrates D* Lite's incremental replanning capability.
        """
        self.world.add_obstacle(x, y)

        # Pass the changed cell so D* Lite can update properly
        self.recompute_paths(changed_cells={(x, y)})

        # Re-evaluate collision pairs with new paths
        # This allows robots to auto-resume if obstacle placement resolves collision
        self.re_evaluate_collision_pairs()

        # Check for recovery of paused robots
        self.check_paused_robot_recovery()

    def remove_dynamic_obstacle(self, x: int, y: int):
        """
        Remove an obstacle during execution and replan affected robots.
        """
        self.world.remove_obstacle(x, y)

        # Pass the changed cell so D* Lite can update properly
        self.recompute_paths(changed_cells={(x, y)})

        # Re-evaluate collision pairs with new paths
        # This allows robots to auto-resume if obstacle removal resolves collision
        self.re_evaluate_collision_pairs()

        # Check for recovery of paused robots
        self.check_paused_robot_recovery()

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

        # Clear collision pairs involving this robot since goal changed
        # This allows the robot to find a new path and potentially resolve collisions
        self.collision_pairs = [
            pair for pair in self.collision_pairs
            if robot_id not in pair
        ]

        # Also resume the robot if it was paused (goal change is user intervention)
        if robot_id in self.paused_robots:
            del self.paused_robots[robot_id]

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

    # ==================== Partial Pausing Methods ====================

    def pause_robot(self, robot_id: str, reason: str):
        """Pause a specific robot with a given reason."""
        if robot_id in self.planners:
            self.paused_robots[robot_id] = reason

    def resume_robot(self, robot_id: str):
        """Resume a paused robot."""
        if robot_id in self.paused_robots:
            del self.paused_robots[robot_id]

    def is_robot_paused(self, robot_id: str) -> bool:
        """Check if a robot is paused."""
        return robot_id in self.paused_robots

    def get_paused_robots(self) -> List[str]:
        """Get list of all paused robots."""
        return list(self.paused_robots.keys())

    def get_pause_reason(self, robot_id: str) -> Optional[str]:
        """Get the reason why a robot is paused."""
        return self.paused_robots.get(robot_id)

    def pause_robots_for_collision(self, collision: Tuple[str, str, str]):
        """Pause robots involved in a collision."""
        robot1, robot2, collision_type = collision
        self.pause_robot(robot1, f"{collision_type}_collision")
        self.pause_robot(robot2, f"{collision_type}_collision")
        self.add_collision_pair(robot1, robot2, collision_type)

    def add_collision_pair(self, robot1: str, robot2: str, collision_type: str):
        """Add a collision pair to tracking."""
        self.collision_pairs.append((robot1, robot2, collision_type))

    def remove_collision_pair(self, robot1: str, robot2: str):
        """Remove a collision pair from tracking."""
        self.collision_pairs = [
            pair for pair in self.collision_pairs
            if not ((robot1 in pair and robot2 in pair))
        ]

    def get_collision_partner(self, robot_id: str) -> Optional[str]:
        """Get the collision partner for a robot."""
        for pair in self.collision_pairs:
            if robot_id == pair[0]:
                return pair[1]
            elif robot_id == pair[1]:
                return pair[0]
        return None

    def clear_collision_pairs(self):
        """Clear all collision pairs."""
        self.collision_pairs = []

    def check_robots_would_collide(self, robot1_id: str, robot2_id: str) -> bool:
        """
        Check if two specific robots would collide based on their current paths.
        Returns True if they would collide, False otherwise.
        """
        if robot1_id not in self.paths or robot2_id not in self.paths:
            return False

        path1 = self.paths[robot1_id]
        path2 = self.paths[robot2_id]

        if not path1 or not path2:
            return False

        # Check for same-cell collision at next step
        if len(path1) > 1 and len(path2) > 1:
            next1 = path1[1]
            next2 = path2[1]

            # Same cell collision
            if next1 == next2:
                return True

            # Swap collision
            curr1 = self.current_positions[robot1_id]
            curr2 = self.current_positions[robot2_id]
            if next1 == curr2 and next2 == curr1:
                return True

            # Shear collision
            if next1 == curr2 and next2 != curr1:
                # Check if perpendicular movement
                dx = next2[0] - curr2[0]
                dy = next2[1] - curr2[1]
                # Robot2 is moving, check if perpendicular to robot1's movement
                dx1 = next1[0] - curr1[0]
                dy1 = next1[1] - curr1[1]
                if (dx != dx1 or dy != dy1):  # Different directions
                    return True

        return False

    def re_evaluate_collision_pairs(self):
        """
        Re-evaluate all collision pairs after path changes.
        Clears pairs that no longer have conflicting paths.
        """
        if not self.collision_pairs:
            return

        new_pairs = []
        cleared_robots = []

        for pair in self.collision_pairs:
            robot1, robot2, collision_type = pair

            # Check if these robots would still collide with new paths
            if self.check_robots_would_collide(robot1, robot2):
                new_pairs.append(pair)
            else:
                # Collision resolved - track which robots are cleared
                cleared_robots.extend([robot1, robot2])

        self.collision_pairs = new_pairs

        # Log if any collisions were resolved
        if cleared_robots:
            print(f"Collision resolved for robots: {', '.join(set(cleared_robots))}")

    def check_paused_robot_recovery(self):
        """
        Check if paused robots can resume.
        Robots resume when their path becomes clear.
        """
        robots_to_resume = []

        for robot_id in self.paused_robots:
            # Only auto-recover collision-paused robots, not manually paused ones
            pause_reason = self.paused_robots.get(robot_id, "")
            if pause_reason in ["manual", "test", "user"]:
                continue  # Don't auto-recover manually paused robots

            # Don't auto-resume if robot is part of an active collision pair
            # This prevents robots in shear/swap collisions from escaping
            if self.get_collision_partner(robot_id) is not None:
                continue  # Skip recovery check for robots in collision pairs

            # Check if robot's next move is now clear
            if robot_id in self.paths and len(self.paths[robot_id]) > 1:
                next_pos = self.paths[robot_id][1]

                # Check if next position is free
                position_free = True
                blocking_robot = None

                for other_robot_id, other_pos in self.current_positions.items():
                    if other_robot_id != robot_id and other_pos == next_pos:
                        blocking_robot = other_robot_id
                        # Position is only free if blocker is NOT paused
                        # (paused robots still block positions)
                        position_free = False
                        break

                # Check if the blockage has been resolved
                # (e.g., blocking robot moved away or goal changed)
                if position_free:
                    robots_to_resume.append(robot_id)
                elif blocking_robot:
                    # Check if blocking robot has moved or will move away
                    if blocking_robot not in self.paused_robots:
                        # Blocking robot is active, check if it's moving away
                        if blocking_robot in self.paths and len(self.paths[blocking_robot]) > 1:
                            blocker_next = self.paths[blocking_robot][1]
                            if blocker_next != next_pos:
                                # Blocker is moving away, can resume
                                robots_to_resume.append(robot_id)

        # Resume robots that can move
        for robot_id in robots_to_resume:
            self.resume_robot(robot_id)
            # Remove from collision pairs
            partner = self.get_collision_partner(robot_id)
            if partner:
                self.remove_collision_pair(robot_id, partner)