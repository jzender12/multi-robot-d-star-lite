#!/usr/bin/env python3
"""
Test goal placement rules:
- Robots can place goals on themselves
- Robots can place goals on other robots' positions
- Robots can place goals on free spaces
- Goals cannot be placed on obstacles
- Multiple robots cannot share the same goal (for solvability)
"""

import pytest
from multi_robot_playground.core.world import GridWorld
from multi_robot_playground.core.coordinator import MultiAgentCoordinator


class TestGoalPlacementRules:
    """Test that goal placement follows the correct rules."""

    def test_goal_on_self(self):
        """Test that a robot can place its goal on its own position."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add a robot at (5, 5)
        coordinator.add_robot("robot1", start=(5, 5), goal=(9, 9))

        # Should be able to set goal to its own position
        success = coordinator.set_new_goal("robot1", (5, 5))
        assert success, "Robot should be able to place goal on itself"
        assert coordinator.goals["robot1"] == (5, 5), "Goal should be set to robot's position"

        print("✓ Robot can place goal on itself")

    def test_goal_on_other_robot_position(self):
        """Test that a robot can place its goal on another robot's current position."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add two robots
        coordinator.add_robot("robot1", start=(3, 3), goal=(9, 9))
        coordinator.add_robot("robot2", start=(7, 7), goal=(0, 0))

        # Robot1 should be able to set goal to robot2's current position
        success = coordinator.set_new_goal("robot1", (7, 7))
        assert success, "Robot should be able to place goal on another robot's position"
        assert coordinator.goals["robot1"] == (7, 7), "Goal should be set to other robot's position"

        # But robot1 cannot set goal to robot2's goal position
        success = coordinator.set_new_goal("robot1", (0, 0))
        assert not success, "Robot should NOT be able to place goal on another robot's goal"
        assert coordinator.goals["robot1"] == (7, 7), "Goal should remain unchanged"

        print("✓ Robot can place goal on another robot's position but not their goal")

    def test_multiple_robots_cannot_share_goal(self):
        """Test that multiple robots cannot have the same goal position."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add three robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(5, 5))
        coordinator.add_robot("robot2", start=(9, 9), goal=(3, 3))
        coordinator.add_robot("robot3", start=(0, 9), goal=(7, 7))

        # Set robot1's goal to (4, 4)
        target = (4, 4)
        success1 = coordinator.set_new_goal("robot1", target)
        assert success1, "First robot should be able to set goal"
        assert coordinator.goals["robot1"] == target

        # Robot2 should NOT be able to set the same goal
        success2 = coordinator.set_new_goal("robot2", target)
        assert not success2, "Second robot should NOT be able to set same goal"
        assert coordinator.goals["robot2"] == (3, 3), "Robot2's goal should remain unchanged"

        # Robot3 should also NOT be able to set the same goal
        success3 = coordinator.set_new_goal("robot3", target)
        assert not success3, "Third robot should NOT be able to set same goal"
        assert coordinator.goals["robot3"] == (7, 7), "Robot3's goal should remain unchanged"

        print("✓ Multiple robots cannot share the same goal")

    def test_goal_on_obstacle_fails(self):
        """Test that goals cannot be placed on obstacles."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add a robot
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Add an obstacle
        world.static_obstacles.add((5, 5))

        # Should NOT be able to set goal on obstacle
        success = coordinator.set_new_goal("robot1", (5, 5))
        assert not success, "Robot should NOT be able to place goal on obstacle"
        assert coordinator.goals["robot1"] == (9, 9), "Goal should remain unchanged"

        print("✓ Goals cannot be placed on obstacles")

    def test_goal_on_free_space(self):
        """Test that goals can be placed on any free space."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots and obstacles
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(2, 2), goal=(7, 7))
        world.static_obstacles.add((5, 5))
        world.static_obstacles.add((5, 6))

        # Test various free spaces
        free_positions = [(3, 3), (8, 1), (4, 7), (1, 8), (6, 2)]

        for pos in free_positions:
            # Make sure this position isn't another robot's goal
            if pos not in [coordinator.goals[rid] for rid in coordinator.goals]:
                success = coordinator.set_new_goal("robot1", pos)
                assert success, f"Robot should be able to place goal on free space {pos}"
                assert coordinator.goals["robot1"] == pos, f"Goal should be set to {pos}"

        print("✓ Goals can be placed on any free space")

    def test_goal_placement_with_robot_positions(self):
        """Test complex scenarios with robots at various positions."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Set up a scenario with robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(5, 5), goal=(0, 9))
        coordinator.add_robot("robot3", start=(9, 0), goal=(5, 0))

        # Add some obstacles
        obstacles = [(3, 3), (3, 4), (4, 3), (7, 7), (8, 8)]
        for obs in obstacles:
            world.static_obstacles.add(obs)

        # Robot1 can set goal to robot2's current position (5, 5)
        assert coordinator.set_new_goal("robot1", (5, 5)), "Should place goal on robot2's position"

        # Robot2 can set goal to robot3's current position (9, 0)
        assert coordinator.set_new_goal("robot2", (9, 0)), "Should place goal on robot3's position"

        # Robot3 can set goal to robot1's current position (0, 0)
        assert coordinator.set_new_goal("robot3", (0, 0)), "Should place goal on robot1's position"

        # But robots cannot set goals to each other's goal positions
        assert not coordinator.set_new_goal("robot1", (9, 0)), "Cannot use robot2's goal"
        assert not coordinator.set_new_goal("robot2", (0, 0)), "Cannot use robot3's goal"
        assert not coordinator.set_new_goal("robot3", (5, 5)), "Cannot use robot1's goal"

        # And no robot can set goal on obstacles
        for obs in obstacles:
            assert not coordinator.set_new_goal("robot1", obs), f"Should not place goal on obstacle {obs}"

        print("✓ Complex goal placement scenarios work correctly")


if __name__ == "__main__":
    test = TestGoalPlacementRules()
    test.test_goal_on_self()
    test.test_goal_on_other_robot_position()
    test.test_multiple_robots_cannot_share_goal()
    test.test_goal_on_obstacle_fails()
    test.test_goal_on_free_space()
    test.test_goal_placement_with_robot_positions()
    print("\nAll goal placement tests passed!")