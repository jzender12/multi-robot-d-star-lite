"""
Tests for goal-blocked robot detection.
"""
import pytest
from multi_robot_playground.core.world import GridWorld
from multi_robot_playground.core.coordinator import MultiAgentCoordinator


class TestGoalBlockedDetection:
    """Test detection of robots with goals blocked by obstacles."""

    def test_goal_blocked_robot_detection(self):
        """Test that robots with obstacles on their goals are detected as goal-blocked."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot with goal at (5, 5)
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))

        # Initially not goal-blocked
        coordinator.detect_stuck_robots()
        assert "robot1" not in coordinator.goal_blocked_robots

        # Place obstacle on goal
        world.add_obstacle(5, 5)
        coordinator.recompute_paths()

        # Now should be goal-blocked
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots
        assert "robot1" in coordinator.stuck_robots  # Also in stuck for compatibility

    def test_goal_blocked_cleared_when_obstacle_removed(self):
        """Test that goal-blocked status is cleared when obstacle is removed."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot and obstacle on goal
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        world.add_obstacle(5, 5)
        coordinator.recompute_paths()

        # Should be goal-blocked
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots

        # Remove obstacle
        world.remove_obstacle(5, 5)
        coordinator.recompute_paths()

        # Should no longer be goal-blocked
        coordinator.detect_stuck_robots()
        assert "robot1" not in coordinator.goal_blocked_robots
        assert "robot1" not in coordinator.stuck_robots

    def test_multiple_goal_blocked_robots(self):
        """Test multiple robots can be goal-blocked simultaneously."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add multiple robots with different goals
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        coordinator.add_robot("robot2", start=(9, 9), goal=(7, 7))
        coordinator.add_robot("robot3", start=(0, 9), goal=(3, 3))

        # Block robot1 and robot2's goals
        world.add_obstacle(5, 5)
        world.add_obstacle(7, 7)
        coordinator.recompute_paths()

        # Check goal-blocked status
        coordinator.detect_stuck_robots()
        assert "robot1" in coordinator.goal_blocked_robots
        assert "robot2" in coordinator.goal_blocked_robots
        assert "robot3" not in coordinator.goal_blocked_robots

    def test_goal_blocked_vs_stuck_distinction(self):
        """Test distinction between goal-blocked and stuck (no path) robots."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Robot1: goal blocked by obstacle on goal
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        world.add_obstacle(5, 5)

        # Robot2: stuck because goal is unreachable (surrounded by obstacles)
        coordinator.add_robot("robot2", start=(9, 0), goal=(9, 9))
        # Surround goal but don't place obstacle on it
        for x in range(8, 10):
            for y in range(8, 10):
                if (x, y) != (9, 9):
                    world.add_obstacle(x, y)

        coordinator.recompute_paths()
        coordinator.detect_stuck_robots()

        # Robot1 is goal-blocked
        assert "robot1" in coordinator.goal_blocked_robots
        assert "robot1" in coordinator.stuck_robots

        # Robot2 is stuck but not goal-blocked
        assert "robot2" not in coordinator.goal_blocked_robots
        assert "robot2" in coordinator.stuck_robots

    def test_robot_at_goal_not_goal_blocked(self):
        """Test that robot at its goal is not marked as goal-blocked even if obstacle placed."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot at its goal
        coordinator.add_robot("robot1", start=(5, 5), goal=(5, 5))

        # Place obstacle on the goal (where robot is)
        world.add_obstacle(5, 5)
        coordinator.recompute_paths()

        # Should not be goal-blocked since it's at goal
        coordinator.detect_stuck_robots()
        assert "robot1" not in coordinator.goal_blocked_robots
        assert "robot1" not in coordinator.stuck_robots