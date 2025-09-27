"""
Test stuck robot detection in the coordinator.
Stuck robots should be detected both during simulation and when checking state.
"""
import pytest
from multi_robot_d_star_lite.core.world import GridWorld
from multi_robot_d_star_lite.core.coordinator import MultiAgentCoordinator


class TestStuckRobotDetection:
    """Test that stuck robots are properly detected at the coordinator level."""

    def test_detect_stuck_robots_method_exists(self):
        """Coordinator should have a method to detect stuck robots."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Method should exist
        assert hasattr(coordinator, 'detect_stuck_robots'), "Coordinator should have detect_stuck_robots method"

    def test_stuck_robot_basic(self):
        """A robot with no path should be detected as stuck."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot with goal blocked by obstacles
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Completely block the goal
        for x in range(8, 10):
            for y in range(8, 10):
                if (x, y) != (9, 9):
                    world.add_obstacle(x, y)

        # Add walls to isolate the goal
        for x in range(7, 10):
            world.add_obstacle(x, 7)
        for y in range(7, 10):
            world.add_obstacle(7, y)

        # Recompute paths
        coordinator.recompute_paths()

        # Detect stuck robots
        stuck = coordinator.detect_stuck_robots()

        assert "robot1" in stuck, "Robot with no path should be detected as stuck"

    def test_robot_at_goal_not_stuck(self):
        """A robot at its goal should not be considered stuck."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robot at its goal
        coordinator.add_robot("robot1", start=(5, 5), goal=(5, 5))

        # Detect stuck robots
        stuck = coordinator.detect_stuck_robots()

        assert "robot1" not in stuck, "Robot at goal should not be stuck"

    def test_multiple_stuck_robots(self):
        """Multiple stuck robots should all be detected."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add two robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(0, 1), goal=(9, 8))

        # Block both paths with a wall
        for x in range(10):
            world.add_obstacle(x, 5)

        coordinator.recompute_paths()

        # Both should be stuck
        stuck = coordinator.detect_stuck_robots()

        assert len(stuck) == 2, "Both robots should be stuck"
        assert "robot1" in stuck
        assert "robot2" in stuck

    def test_stuck_robot_recovery(self):
        """Stuck robot should recover when path becomes available."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Block the path
        for x in range(10):
            world.add_obstacle(x, 5)

        coordinator.recompute_paths()
        stuck = coordinator.detect_stuck_robots()
        assert "robot1" in stuck, "Robot should be stuck initially"

        # Remove one obstacle to create a path
        world.remove_obstacle(5, 5)
        coordinator.recompute_paths()

        stuck = coordinator.detect_stuck_robots()
        assert "robot1" not in stuck, "Robot should recover when path available"

    def test_stuck_stored_as_instance_variable(self):
        """Stuck robots should be stored in coordinator.stuck_robots."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Block the path
        for x in range(10):
            world.add_obstacle(x, 5)

        coordinator.recompute_paths()
        coordinator.detect_stuck_robots()

        # Should be stored in instance variable
        assert hasattr(coordinator, 'stuck_robots'), "Should have stuck_robots attribute"
        assert "robot1" in coordinator.stuck_robots

    def test_stuck_detection_during_step(self):
        """Stuck robots should be detected during step_simulation."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Block the path
        for x in range(10):
            world.add_obstacle(x, 5)

        coordinator.recompute_paths()

        # Step simulation should detect stuck robots
        should_continue, collision, stuck_robots, paused_robots = coordinator.step_simulation()

        assert "robot1" in stuck_robots, "Step should detect stuck robots"

    def test_stuck_vs_paused_distinction(self):
        """Stuck and paused robots should be tracked separately."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Two robots that will collide
        coordinator.add_robot("robot1", start=(0, 0), goal=(2, 0))
        coordinator.add_robot("robot2", start=(2, 0), goal=(0, 0))

        # Third robot that will be stuck
        coordinator.add_robot("robot3", start=(5, 0), goal=(5, 9))

        # Block robot3's path
        for x in range(10):
            world.add_obstacle(x, 2)

        coordinator.recompute_paths()

        # Step to potentially trigger collision
        should_continue, collision, stuck_robots, paused_robots = coordinator.step_simulation()

        # robot3 should be stuck
        assert "robot3" in stuck_robots, "robot3 should be stuck"

        # robot1 and robot2 might be paused but not stuck
        if paused_robots:
            for paused in paused_robots:
                assert paused not in stuck_robots, f"{paused} should not be both paused and stuck"

    def test_empty_path_means_stuck(self):
        """A robot with empty path (not at goal) should be stuck."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Surround robot completely
        world.add_obstacle(0, 1)
        world.add_obstacle(1, 0)
        world.add_obstacle(1, 1)

        coordinator.recompute_paths()

        # Path should be empty or only contain current position (stuck)
        path = coordinator.paths.get("robot1", [])
        assert len(path) <= 1, "Path should be empty or just current position"
        if len(path) == 1:
            assert path[0] == (0, 0), "Path should only contain current position"

        # Should be detected as stuck
        stuck = coordinator.detect_stuck_robots()
        assert "robot1" in stuck, "Robot with no valid path should be stuck"

    def test_stuck_persists_across_calls(self):
        """Stuck status should persist across multiple detect calls."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Block the path
        for x in range(10):
            world.add_obstacle(x, 5)

        coordinator.recompute_paths()

        # Multiple calls should give same result
        for _ in range(3):
            stuck = coordinator.detect_stuck_robots()
            assert "robot1" in stuck, "Stuck status should persist"
            assert "robot1" in coordinator.stuck_robots, "Instance variable should persist"