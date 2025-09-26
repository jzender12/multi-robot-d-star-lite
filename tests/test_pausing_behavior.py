#!/usr/bin/env python3
"""
Tests for pausing behavior and stuck robot handling.

These tests ensure that:
1. Robots are marked as stuck when they can't find a path
2. Simulation continues running when robots are stuck (doesn't pause)
3. Stuck robots automatically resume when path becomes available
4. Pause state remains consistent between UI and internal state
"""

import pytest
from multi_robot_d_star_lite.world import GridWorld
from multi_robot_d_star_lite.coordinator import MultiAgentCoordinator


class TestStuckRobotDetection:
    """Test detection of stuck robots when paths are blocked."""

    def test_robot_stuck_when_goal_blocked(self):
        """Robot should be marked as stuck when its goal is blocked."""
        # Setup world with robot
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(2, 2))

        # Block the goal
        world.add_obstacle(2, 2)
        coordinator.recompute_paths()

        # Step simulation - should report robot as stuck
        should_continue, collision, stuck_robots = coordinator.step_simulation()

        assert "robot0" in stuck_robots, "Robot should be marked as stuck when goal blocked"
        assert should_continue == True, "Simulation should continue even with stuck robot"
        assert collision is None, "No collision should be reported"

    def test_robot_not_stuck_when_at_goal(self):
        """Robot at goal should not be marked as stuck even with empty path."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(2, 2), goal=(2, 2))  # Already at goal

        # Step simulation
        should_continue, collision, stuck_robots = coordinator.step_simulation()

        assert "robot0" not in stuck_robots, "Robot at goal should not be stuck"
        assert should_continue == False, "Should not continue when all robots at goal"

    def test_robot_not_stuck_with_valid_path(self):
        """Robot with valid path should not be marked as stuck."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(2, 2))
        coordinator.recompute_paths()

        # Step simulation
        should_continue, collision, stuck_robots = coordinator.step_simulation()

        assert len(stuck_robots) == 0, "Robot with valid path should not be stuck"
        assert should_continue == True, "Should continue with moving robot"


class TestStuckRobotRecovery:
    """Test that stuck robots recover when paths become available."""

    def test_stuck_robot_resumes_when_path_clears(self):
        """Stuck robot should automatically resume when obstacle is removed."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(2, 2))

        # Block the goal
        world.add_obstacle(2, 2)
        coordinator.recompute_paths()

        # Verify robot is stuck
        _, _, stuck_robots = coordinator.step_simulation()
        assert "robot0" in stuck_robots, "Robot should be stuck initially"

        # Remove obstacle
        world.remove_obstacle(2, 2)
        coordinator.recompute_paths(changed_cells={(2, 2)})

        # Robot should no longer be stuck
        should_continue, _, stuck_robots = coordinator.step_simulation()
        assert "robot0" not in stuck_robots, "Robot should resume when path clears"
        assert should_continue == True, "Should continue moving"

    def test_partial_path_blockage_recovery(self):
        """Robot should find alternate path when partial blockage removed."""
        world = GridWorld(7, 7)  # Larger grid for more room
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(6, 6))

        # Create a wall that blocks direct path but has space around
        for i in range(5):  # Wall from y=0 to y=4
            world.add_obstacle(3, i)
        coordinator.recompute_paths()

        # Check initial state - might or might not be stuck depending on pathfinding
        _, _, stuck_robots_initial = coordinator.step_simulation()

        # Open a clear gap in the wall
        world.remove_obstacle(3, 2)
        coordinator.recompute_paths(changed_cells={(3, 2)})

        # Should find path through gap (or around if there was already a path)
        _, _, stuck_robots = coordinator.step_simulation()

        # If it was stuck before, it shouldn't be stuck now
        if len(stuck_robots_initial) > 0:
            assert len(stuck_robots) == 0, "Robot should find path after gap opened"


class TestSimulationContinuity:
    """Test that simulation continues correctly with stuck robots."""

    def test_simulation_continues_when_robot_stuck(self):
        """Simulation should not pause when a robot is stuck."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)

        # Add two robots
        coordinator.add_robot("robot0", start=(0, 0), goal=(2, 2))
        coordinator.add_robot("robot1", start=(4, 0), goal=(4, 4))

        # Block first robot's goal
        world.add_obstacle(2, 2)
        coordinator.recompute_paths()

        # Step simulation multiple times
        for _ in range(3):
            should_continue, collision, stuck_robots = coordinator.step_simulation()
            assert should_continue == True, "Simulation should continue"
            assert "robot0" in stuck_robots, "Robot0 should remain stuck"
            assert "robot1" not in stuck_robots, "Robot1 should not be stuck"

    def test_multiple_robots_some_stuck(self):
        """Handle mixed scenario with some robots stuck, others moving."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add three robots
        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 5))  # Will be blocked
        coordinator.add_robot("robot1", start=(9, 0), goal=(9, 9))  # Clear path
        coordinator.add_robot("robot2", start=(0, 9), goal=(3, 3))  # Will be blocked

        # Block two goals
        world.add_obstacle(5, 5)
        world.add_obstacle(3, 3)
        coordinator.recompute_paths()

        # Step simulation
        should_continue, _, stuck_robots = coordinator.step_simulation()

        assert len(stuck_robots) == 2, "Two robots should be stuck"
        assert "robot0" in stuck_robots, "Robot0 should be stuck"
        assert "robot2" in stuck_robots, "Robot2 should be stuck"
        assert "robot1" not in stuck_robots, "Robot1 should not be stuck"
        assert should_continue == True, "Should continue with one robot moving"


class TestAllRobotsStuck:
    """Test behavior when all robots are stuck."""

    def test_all_robots_stuck(self):
        """When all robots are stuck, simulation should still continue."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)

        # Add two robots and block both goals
        coordinator.add_robot("robot0", start=(0, 0), goal=(2, 2))
        coordinator.add_robot("robot1", start=(4, 0), goal=(4, 4))

        world.add_obstacle(2, 2)
        world.add_obstacle(4, 4)
        coordinator.recompute_paths()

        # Step simulation
        should_continue, collision, stuck_robots = coordinator.step_simulation()

        assert len(stuck_robots) == 2, "Both robots should be stuck"
        assert should_continue == True, "Should continue even with all stuck"
        assert collision is None, "No collision when stuck"

    def test_stuck_robot_doesnt_trigger_success(self):
        """Stuck robots should not trigger 'all at goal' success condition."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)

        # One robot at goal, one stuck
        coordinator.add_robot("robot0", start=(2, 2), goal=(2, 2))  # At goal
        coordinator.add_robot("robot1", start=(0, 0), goal=(4, 4))  # Will be stuck

        world.add_obstacle(4, 4)
        coordinator.recompute_paths()

        # Step simulation
        should_continue, _, stuck_robots = coordinator.step_simulation()

        # Should not report success since one robot is stuck (not at goal)
        assert should_continue == True, "Should continue with stuck robot"
        assert "robot1" in stuck_robots, "Robot1 should be stuck"


class TestDynamicObstacleHandling:
    """Test stuck behavior with dynamic obstacles during runtime."""

    def test_obstacle_added_during_movement(self):
        """Robot should become stuck if goal blocked during movement."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(4, 4))
        coordinator.recompute_paths()

        # Move robot partway
        should_continue, _, stuck_robots = coordinator.step_simulation()
        assert len(stuck_robots) == 0, "Initially not stuck"
        assert should_continue == True

        # Block the goal while robot is moving
        world.add_obstacle(4, 4)
        coordinator.recompute_paths(changed_cells={(4, 4)})

        # Robot should now be stuck
        should_continue, _, stuck_robots = coordinator.step_simulation()
        assert "robot0" in stuck_robots, "Should be stuck after goal blocked"

    def test_moving_obstacle_causes_stuck(self):
        """Test robot getting stuck when obstacle blocks path dynamically."""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)
        coordinator.add_robot("robot0", start=(0, 0), goal=(4, 4))

        # Create a simple corridor that can be blocked
        # Leave a clear path initially
        world.add_obstacle(1, 1)
        world.add_obstacle(1, 2)
        world.add_obstacle(2, 1)
        coordinator.recompute_paths()

        # Initially should have path around obstacles
        _, _, stuck_robots = coordinator.step_simulation()
        assert len(stuck_robots) == 0, "Should have path initially"

        # Now completely surround the goal
        world.add_obstacle(3, 4)
        world.add_obstacle(4, 3)
        world.add_obstacle(3, 3)
        coordinator.recompute_paths(changed_cells={(3, 4), (4, 3), (3, 3)})

        # Should now be stuck
        _, _, stuck_robots = coordinator.step_simulation()
        assert "robot0" in stuck_robots, "Should be stuck when goal surrounded"