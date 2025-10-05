"""
Tests for obstacle placement validation - cannot place on robots.
"""
import pytest
from multi_robot_playground.core.world import GridWorld
from multi_robot_playground.core.coordinator import MultiAgentCoordinator


class TestObstacleOnRobotValidation:
    """Test that obstacles cannot be placed on robot positions."""

    def test_cannot_place_obstacle_on_robot(self):
        """Test that placing obstacle on robot position is rejected."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot at position (5, 5)
        coordinator.add_robot("robot1", start=(5, 5), goal=(9, 9))

        # Try to place obstacle on robot - should fail
        success = coordinator.add_dynamic_obstacle(5, 5)
        assert success is False, "Should not be able to place obstacle on robot"

        # Verify obstacle was not added
        assert (5, 5) not in world.static_obstacles

    def test_can_place_obstacle_after_robot_moves(self):
        """Test that obstacle can be placed after robot moves away."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot and let it move
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.step_simulation()  # Robot moves from (0,0)

        # Now should be able to place obstacle at (0, 0)
        success = coordinator.add_dynamic_obstacle(0, 0)
        assert success is True, "Should be able to place obstacle where robot was"
        assert (0, 0) in world.static_obstacles

    def test_multiple_robots_blocking_obstacle_placement(self):
        """Test that obstacle cannot be placed on any robot position."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add multiple robots
        coordinator.add_robot("robot1", start=(3, 3), goal=(8, 8))
        coordinator.add_robot("robot2", start=(5, 5), goal=(0, 0))
        coordinator.add_robot("robot3", start=(7, 7), goal=(2, 2))

        # Try to place obstacles on each robot - all should fail
        assert coordinator.add_dynamic_obstacle(3, 3) is False
        assert coordinator.add_dynamic_obstacle(5, 5) is False
        assert coordinator.add_dynamic_obstacle(7, 7) is False

        # Try to place obstacle on empty space - should succeed
        assert coordinator.add_dynamic_obstacle(1, 1) is True
        assert (1, 1) in world.static_obstacles

    def test_obstacle_validation_with_goal(self):
        """Test that obstacle can be placed on goal but not on robot."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))

        # Can place obstacle on goal
        success = coordinator.add_dynamic_obstacle(5, 5)
        assert success is True, "Should be able to place obstacle on goal"

        # Cannot place obstacle on robot
        success = coordinator.add_dynamic_obstacle(0, 0)
        assert success is False, "Should not be able to place obstacle on robot"