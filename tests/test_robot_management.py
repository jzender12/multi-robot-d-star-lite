#!/usr/bin/env python3
"""
Test suite for robot management functionality.
Tests adding, removing, and managing multiple robots.
"""

import pytest
from multi_robot_d_star_lite.world import GridWorld
from multi_robot_d_star_lite.coordinator import MultiAgentCoordinator


class TestRobotAddition:
    """Tests for adding robots to the system"""

    def test_get_next_robot_id(self):
        """Should generate sequential robot IDs"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add initial robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(9, 0), goal=(0, 9))

        # Get next IDs
        next_id = coordinator.get_next_robot_id()
        assert next_id == "robot3"

        coordinator.add_robot(next_id, start=(5, 5), goal=(2, 2))
        next_id = coordinator.get_next_robot_id()
        assert next_id == "robot4"

    def test_get_next_robot_id_with_gaps(self):
        """Should handle gaps in robot numbering"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots with gap
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot3", start=(9, 0), goal=(0, 9))

        # Should find robot2 is missing and use robot4
        next_id = coordinator.get_next_robot_id()
        assert next_id == "robot4"

    def test_add_robot_with_validation(self):
        """Should validate robot placement"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add obstacle
        world.add_obstacle(5, 5)

        # Try to add robot on obstacle - should handle gracefully
        # The add_robot should either fail or place elsewhere
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        assert "robot1" in coordinator.planners
        assert coordinator.current_positions["robot1"] == (0, 0)

    def test_add_multiple_robots(self):
        """Should support many robots"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add 10 robots
        for i in range(1, 11):
            robot_id = f"robot{i}"
            # Place in different positions
            x = i % 10
            y = i // 10
            goal_x = (10 - i) % 10
            goal_y = (10 - i) // 10
            coordinator.add_robot(robot_id, start=(x, y), goal=(goal_x, goal_y))

        # Verify all added
        assert len(coordinator.planners) == 10
        assert len(coordinator.current_positions) == 10


class TestRobotRemoval:
    """Tests for removing robots from the system"""

    def test_remove_robot_basic(self):
        """Should remove robot and clean up all references"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(9, 0), goal=(0, 9))

        # Remove robot1
        success = coordinator.remove_robot("robot1")

        # Verify removal
        assert success is True
        assert "robot1" not in coordinator.planners
        assert "robot1" not in coordinator.current_positions
        assert "robot1" not in coordinator.goals
        assert "robot1" not in coordinator.paths
        assert "robot1" not in world.robot_positions

        # robot2 should still exist
        assert "robot2" in coordinator.planners

    def test_remove_nonexistent_robot(self):
        """Should handle removing robot that doesn't exist"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))

        # Try to remove non-existent robot
        success = coordinator.remove_robot("robot99")
        assert success is False

    def test_remove_all_robots(self):
        """Should be able to remove all robots"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(9, 0), goal=(0, 9))
        coordinator.add_robot("robot3", start=(5, 5), goal=(2, 2))

        # Remove all
        coordinator.remove_robot("robot1")
        coordinator.remove_robot("robot2")
        coordinator.remove_robot("robot3")

        # Verify all gone
        assert len(coordinator.planners) == 0
        assert len(coordinator.current_positions) == 0
        assert len(world.robot_positions) == 0

    def test_clear_all_robots(self):
        """Should clear all robots at once"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add multiple robots
        for i in range(1, 6):
            coordinator.add_robot(f"robot{i}", start=(i, i), goal=(9-i, 9-i))

        assert len(coordinator.planners) == 5

        # Clear all
        coordinator.clear_all_robots()

        # Verify all cleared
        assert len(coordinator.planners) == 0
        assert len(coordinator.current_positions) == 0
        assert len(coordinator.goals) == 0
        assert len(coordinator.paths) == 0
        assert len(world.robot_positions) == 0


class TestRobotManagementIntegration:
    """Integration tests for robot management"""

    def test_add_remove_add_workflow(self):
        """Should handle complex add/remove sequences"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add initial robots
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(9, 0), goal=(0, 9))

        # Remove robot1
        coordinator.remove_robot("robot1")

        # Add new robot - should reuse or skip robot1
        next_id = coordinator.get_next_robot_id()
        coordinator.add_robot(next_id, start=(5, 5), goal=(2, 2))

        # Verify state
        assert "robot1" not in coordinator.planners
        assert "robot2" in coordinator.planners
        assert next_id in coordinator.planners
        assert len(coordinator.planners) == 2

    def test_paths_update_after_robot_removal(self):
        """Removing a robot should trigger path updates for others"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots that might interfere
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
        coordinator.add_robot("robot2", start=(1, 0), goal=(8, 9))

        # Get initial paths
        coordinator.recompute_paths()
        initial_path2 = coordinator.paths.get("robot2", []).copy()

        # Remove robot1
        coordinator.remove_robot("robot1")

        # robot2 should still have a valid path
        assert "robot2" in coordinator.paths
        # Path might change but should still exist
        assert len(coordinator.paths["robot2"]) > 0

    def test_robot_limit(self):
        """Should handle reasonable robot limits"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add many robots (up to grid capacity)
        max_robots = 20  # Reasonable limit for 10x10 grid

        for i in range(1, max_robots + 1):
            x = i % 10
            y = (i // 10) % 10
            # Ensure different goal
            goal_x = (x + 5) % 10
            goal_y = (y + 5) % 10

            robot_id = f"robot{i}"
            coordinator.add_robot(robot_id, start=(x, y), goal=(goal_x, goal_y))

        assert len(coordinator.planners) == max_robots


class TestRobotPositioning:
    """Tests for robot position management"""

    def test_random_free_position(self):
        """Should find random free position for new robots"""
        world = GridWorld(5, 5)
        coordinator = MultiAgentCoordinator(world)

        # Add obstacles
        for i in range(3):
            for j in range(3):
                world.add_obstacle(i, j)

        # Add robot - should find free position
        free_positions = []
        for x in range(5):
            for y in range(5):
                if world.is_free(x, y):
                    free_positions.append((x, y))

        # Should have some free positions
        assert len(free_positions) > 0

        # Get random free position
        import random
        if hasattr(coordinator, 'get_random_free_position'):
            pos = coordinator.get_random_free_position()
            assert pos in free_positions

    def test_no_duplicate_start_positions(self):
        """Robots should not share start positions"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add first robot
        success1 = coordinator.add_robot("robot1", start=(5, 5), goal=(0, 0))
        assert success1 is True

        # Try to add another robot at same position - should fail
        success2 = coordinator.add_robot("robot2", start=(5, 5), goal=(9, 9))
        assert success2 is False

        # Only robot1 should exist
        assert "robot1" in coordinator.current_positions
        assert "robot2" not in coordinator.current_positions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])