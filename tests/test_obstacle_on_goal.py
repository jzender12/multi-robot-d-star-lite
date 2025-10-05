"""
Tests for placing obstacles on goals.
"""
import pytest
from multi_robot_playground.core.world import GridWorld
from multi_robot_playground.core.coordinator import MultiAgentCoordinator


class TestObstacleOnGoal:
    """Test placing obstacles on robot goals."""

    def test_can_place_obstacle_on_goal(self):
        """Test that obstacles can be placed on robot goals."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot with goal
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))

        # Place obstacle on goal - should be allowed
        world.add_obstacle(5, 5)
        assert (5, 5) in world.static_obstacles

        # Robot should now be goal-blocked
        coordinator.recompute_paths()
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots

    def test_obstacle_on_multiple_robots_goals(self):
        """Test that obstacle on position that is goal for multiple robots affects all."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # NOTE: Currently the system prevents multiple robots from having the same goal
        # This test documents expected behavior if that restriction is lifted
        # For now, we test with goals close to each other
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        coordinator.add_robot("robot2", start=(9, 9), goal=(5, 4))  # Adjacent goal

        # Place obstacles on both goals
        world.add_obstacle(5, 5)
        world.add_obstacle(5, 4)
        coordinator.recompute_paths()
        coordinator.detect_stuck_robots()

        # Both should be goal-blocked
        assert "robot1" in coordinator.goal_blocked_robots
        assert "robot2" in coordinator.goal_blocked_robots

    def test_dynamic_obstacle_on_goal(self):
        """Test adding and removing obstacles on goals dynamically."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))

        # Dynamically add obstacle on goal
        coordinator.add_dynamic_obstacle(5, 5)
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots

        # Remove obstacle
        coordinator.remove_dynamic_obstacle(5, 5)
        coordinator.detect_stuck_robots()
        assert "robot1" not in coordinator.goal_blocked_robots

    def test_robot_can_still_move_with_goal_blocked(self):
        """Test that robot with blocked goal can still move (not collision-blocked)."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        world.add_obstacle(5, 5)
        coordinator.recompute_paths()

        # Robot is goal-blocked but not collision-blocked
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots
        assert "robot1" not in coordinator.collision_blocked_robots

        # Robot should still try to get as close as possible
        # (exact behavior depends on pathfinding algorithm)