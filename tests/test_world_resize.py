#!/usr/bin/env python3
"""
Test suite for world resizing functionality.
Tests dynamic arena size changes while preserving content.
"""

import pytest
import numpy as np
from multi_robot_d_star_lite.core.world import GridWorld
from multi_robot_d_star_lite.core.coordinator import MultiAgentCoordinator


class TestBasicResize:
    """Basic world resizing tests"""

    def test_resize_smaller(self):
        """Should resize world to smaller dimensions"""
        world = GridWorld(10, 10)

        # Resize smaller
        world.resize(5, 5)

        assert world.width == 5
        assert world.height == 5
        assert world.grid.shape == (5, 5)

    def test_resize_larger(self):
        """Should resize world to larger dimensions"""
        world = GridWorld(5, 5)

        # Resize larger
        world.resize(15, 15)

        assert world.width == 15
        assert world.height == 15
        assert world.grid.shape == (15, 15)

    def test_resize_non_square(self):
        """Should handle non-square dimensions"""
        world = GridWorld(10, 10)

        # Resize to rectangle
        world.resize(8, 12)

        assert world.width == 8
        assert world.height == 12
        assert world.grid.shape == (12, 8)

    def test_resize_minimum_size(self):
        """Should enforce minimum size limit"""
        world = GridWorld(10, 10)

        # Try to resize too small - should clamp to minimum
        world.resize(2, 2)

        # Assuming minimum is 3x3
        assert world.width >= 3
        assert world.height >= 3

    def test_resize_maximum_size(self):
        """Should enforce maximum size limit"""
        world = GridWorld(10, 10)

        # Try to resize too large - should clamp to maximum
        world.resize(50, 50)

        # Assuming maximum is 30x30
        assert world.width <= 30
        assert world.height <= 30


class TestObstaclePreservation:
    """Tests for obstacle handling during resize"""

    def test_preserve_obstacles_within_bounds(self):
        """Should keep obstacles that fit in new size"""
        world = GridWorld(10, 10)

        # Add obstacles
        world.add_obstacle(3, 3)
        world.add_obstacle(4, 4)
        world.add_obstacle(5, 5)

        # Resize to still include these
        world.resize(8, 8)

        # Obstacles should be preserved
        assert (3, 3) in world.static_obstacles
        assert (4, 4) in world.static_obstacles
        assert (5, 5) in world.static_obstacles

    def test_remove_out_of_bounds_obstacles(self):
        """Should remove obstacles outside new bounds"""
        world = GridWorld(10, 10)

        # Add obstacles
        world.add_obstacle(3, 3)
        world.add_obstacle(7, 7)
        world.add_obstacle(9, 9)

        # Resize smaller
        world.resize(5, 5)

        # Only obstacle within bounds should remain
        assert (3, 3) in world.static_obstacles
        assert (7, 7) not in world.static_obstacles
        assert (9, 9) not in world.static_obstacles
        assert len(world.static_obstacles) == 1

    def test_preserve_obstacles_on_enlarge(self):
        """All obstacles should remain when enlarging"""
        world = GridWorld(5, 5)

        # Add obstacles
        world.add_obstacle(2, 2)
        world.add_obstacle(3, 3)
        world.add_obstacle(4, 4)

        # Resize larger
        world.resize(10, 10)

        # All obstacles should be preserved
        assert (2, 2) in world.static_obstacles
        assert (3, 3) in world.static_obstacles
        assert (4, 4) in world.static_obstacles
        assert len(world.static_obstacles) == 3


class TestRobotHandling:
    """Tests for robot position handling during resize"""

    def test_remove_robots_outside_bounds(self):
        """Should handle robots outside new bounds"""
        world = GridWorld(10, 10)

        # Add robots at various positions
        world.robot_positions["robot1"] = (2, 2)
        world.robot_positions["robot2"] = (8, 8)
        world.robot_positions["robot3"] = (9, 9)

        # Resize smaller
        world.resize(5, 5)

        # Only robot1 should remain
        assert "robot1" in world.robot_positions
        assert world.robot_positions["robot1"] == (2, 2)
        assert "robot2" not in world.robot_positions
        assert "robot3" not in world.robot_positions

    def test_preserve_robots_on_enlarge(self):
        """All robots should remain when enlarging"""
        world = GridWorld(5, 5)

        # Add robots
        world.robot_positions["robot1"] = (2, 2)
        world.robot_positions["robot2"] = (4, 4)

        # Resize larger
        world.resize(10, 10)

        # All robots should be preserved
        assert "robot1" in world.robot_positions
        assert "robot2" in world.robot_positions
        assert world.robot_positions["robot1"] == (2, 2)
        assert world.robot_positions["robot2"] == (4, 4)


class TestCoordinatorResize:
    """Tests for coordinator handling during resize"""

    def test_coordinator_resize_updates_paths(self):
        """Resizing should create clean slate with robot0 and valid path"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots
        coordinator.add_robot("robot1", start=(1, 1), goal=(8, 8))
        coordinator.add_robot("robot2", start=(8, 1), goal=(1, 8))

        # Initial path computation
        coordinator.recompute_paths()

        # Resize world - creates clean slate
        if hasattr(coordinator, 'resize_world'):
            coordinator.resize_world(15, 15)

            # Only robot0 should exist with new path
            assert "robot0" in coordinator.paths
            assert "robot2" not in coordinator.paths  # Clean slate removes robot2
            # robot0 should have valid path from (0,0) to (14,14)
            assert len(coordinator.paths["robot0"]) > 0
            assert coordinator.current_positions["robot0"] == (0, 0)
            assert coordinator.goals["robot0"] == (14, 14)

    def test_coordinator_removes_invalid_robots(self):
        """Coordinator should handle robots outside new bounds"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots
        coordinator.add_robot("robot1", start=(2, 2), goal=(4, 4))
        coordinator.add_robot("robot2", start=(8, 8), goal=(9, 9))

        # Resize smaller
        if hasattr(coordinator, 'resize_world'):
            coordinator.resize_world(5, 5)

            # Only robot0 should remain after clean slate
            assert "robot0" in coordinator.planners
            assert "robot2" not in coordinator.planners
            assert "robot0" in coordinator.current_positions
            assert "robot2" not in coordinator.current_positions

    def test_coordinator_resize_clean_slate(self):
        """Resize should create clean slate with robot0"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add robots and obstacles
        coordinator.add_robot("robot1", start=(2, 2), goal=(8, 8))
        coordinator.add_robot("robot2", start=(3, 3), goal=(7, 7))
        world.add_obstacle(5, 5)

        # Resize smaller
        if hasattr(coordinator, 'resize_world'):
            coordinator.resize_world(5, 5)

            # Should have clean slate with only robot0
            assert len(coordinator.planners) == 1
            assert "robot0" in coordinator.planners
            assert "robot2" not in coordinator.planners
            assert coordinator.current_positions["robot0"] == (0, 0)
            assert coordinator.goals["robot0"] == (4, 4)  # bottom-right of 5x5
            assert len(world.static_obstacles) == 0


class TestEdgeCases:
    """Edge case tests for resizing"""

    def test_resize_to_same_size(self):
        """Resizing to same size should preserve everything"""
        world = GridWorld(10, 10)

        # Add content
        world.add_obstacle(5, 5)
        world.robot_positions["robot1"] = (3, 3)

        # Resize to same
        world.resize(10, 10)

        # Everything preserved
        assert (5, 5) in world.static_obstacles
        assert world.robot_positions["robot1"] == (3, 3)
        assert world.width == 10
        assert world.height == 10

    def test_resize_empty_world(self):
        """Should handle resizing empty world"""
        world = GridWorld(10, 10)

        # Resize empty world
        world.resize(5, 5)

        assert world.width == 5
        assert world.height == 5
        assert len(world.static_obstacles) == 0
        assert len(world.robot_positions) == 0

    def test_multiple_resizes(self):
        """Should handle multiple consecutive resizes"""
        world = GridWorld(10, 10)

        # Add obstacle
        world.add_obstacle(3, 3)

        # Multiple resizes
        world.resize(15, 15)
        assert (3, 3) in world.static_obstacles

        world.resize(8, 8)
        assert (3, 3) in world.static_obstacles

        world.resize(4, 4)
        assert (3, 3) in world.static_obstacles

        world.resize(2, 2)  # Should clamp to minimum
        # Obstacle may be removed if minimum is enforced


class TestIntegration:
    """Integration tests for world resizing"""

    def test_full_resize_workflow(self):
        """Test complete resize workflow with coordinator"""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Setup initial state
        world.add_obstacle(4, 4)
        world.add_obstacle(8, 8)
        coordinator.add_robot("robot1", start=(1, 1), goal=(7, 7))
        coordinator.add_robot("robot2", start=(9, 9), goal=(2, 2))

        # Compute initial paths
        coordinator.recompute_paths()

        # Resize to medium - creates clean slate
        if hasattr(coordinator, 'resize_world'):
            coordinator.resize_world(6, 6)

            # Check state - clean slate
            assert world.width == 6
            assert world.height == 6
            assert len(world.static_obstacles) == 0  # All obstacles cleared

            # Only robot0 exists at new position
            assert len(coordinator.planners) == 1
            assert "robot0" in coordinator.planners
            assert "robot2" not in coordinator.planners

            # robot0 at top-left, goal at bottom-right
            assert coordinator.current_positions["robot0"] == (0, 0)
            assert coordinator.goals["robot0"] == (5, 5)

            # Path should be computable
            if "robot0" in coordinator.paths:
                assert len(coordinator.paths["robot0"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])