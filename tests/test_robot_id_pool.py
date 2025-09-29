#!/usr/bin/env python3
"""
Test robot ID pool management for limiting to 10 robots and reusing IDs.
"""

import pytest
from multi_robot_playground.web.game_manager import GameManager


class TestRobotIDPool:
    """Test that robot ID pool correctly manages robot IDs 0-9."""

    def test_initial_pool_has_ten_ids(self):
        """Pool should start with 10 available IDs (0-9)."""
        game = GameManager()
        # Pool should have 10 IDs available
        assert len(game.robot_id_pool) == 10
        # Should contain all numbers 0-9
        pool_numbers = sorted(game.robot_id_pool)
        assert pool_numbers == list(range(10))

    def test_adding_robot_uses_id_from_pool(self):
        """Adding a robot should take an ID from the pool."""
        game = GameManager()
        initial_pool_size = len(game.robot_id_pool)

        robot_id = game.add_robot((0, 0), (5, 5))

        assert robot_id is not None
        assert len(game.robot_id_pool) == initial_pool_size - 1
        # Should get robot0 first (since pool is [9,8,7,6,5,4,3,2,1,0])
        assert robot_id == "robot0"

    def test_can_add_exactly_ten_robots(self):
        """Should be able to add exactly 10 robots."""
        game = GameManager()
        added_robots = []

        for i in range(10):
            robot_id = game.add_robot((i, 0), (i, 9))
            assert robot_id is not None
            added_robots.append(robot_id)

        # Should have all robot IDs 0-9
        robot_numbers = sorted([int(rid.replace("robot", "")) for rid in added_robots])
        assert robot_numbers == list(range(10))

        # Pool should be empty
        assert len(game.robot_id_pool) == 0

    def test_cannot_add_eleventh_robot(self):
        """Should not be able to add more than 10 robots."""
        game = GameManager()

        # Add 10 robots
        for i in range(10):
            robot_id = game.add_robot((i, 0), (i, 9))
            assert robot_id is not None

        # Try to add 11th robot
        robot_id = game.add_robot((0, 5), (9, 5))
        assert robot_id is None  # Should fail

        # Should still have 10 robots
        assert len(game.coordinator.current_positions) == 10

    def test_removing_robot_returns_id_to_pool(self):
        """Removing a robot should return its ID to the pool."""
        game = GameManager()

        # Add a robot
        robot_id = game.add_robot((0, 0), (5, 5))
        assert robot_id == "robot0"
        assert len(game.robot_id_pool) == 9

        # Remove the robot
        success = game.remove_robot("robot0")
        assert success
        assert len(game.robot_id_pool) == 10
        assert 0 in game.robot_id_pool

    def test_reuses_removed_robot_id(self):
        """Should reuse the ID of a removed robot."""
        game = GameManager()

        # Add robot0, robot1, robot2
        robot0 = game.add_robot((0, 0), (5, 5))
        robot1 = game.add_robot((1, 0), (6, 5))
        robot2 = game.add_robot((2, 0), (7, 5))

        assert robot0 == "robot0"
        assert robot1 == "robot1"
        assert robot2 == "robot2"

        # Remove robot1
        game.remove_robot("robot1")

        # Next added robot should reuse robot1's ID
        new_robot = game.add_robot((3, 0), (8, 5))
        assert new_robot == "robot1"

    def test_lifo_behavior_for_removed_ids(self):
        """Removed IDs should be reused in LIFO order."""
        game = GameManager()

        # Add 5 robots
        for i in range(5):
            game.add_robot((i, 0), (i, 9))

        # Remove robot2 then robot4
        game.remove_robot("robot2")
        game.remove_robot("robot4")

        # Next robot should get robot4's ID (last removed)
        new_robot1 = game.add_robot((5, 0), (5, 9))
        assert new_robot1 == "robot4"

        # Next robot should get robot2's ID
        new_robot2 = game.add_robot((6, 0), (6, 9))
        assert new_robot2 == "robot2"

    def test_pool_after_resize(self):
        """Pool should reset after arena resize."""
        game = GameManager()

        # Add some robots
        game.add_robot((0, 0), (5, 5))
        game.add_robot((1, 0), (6, 5))
        game.add_robot((2, 0), (7, 5))

        # Resize arena (should clear all robots)
        game.resize_arena(15, 15)

        # Pool should be full again
        assert len(game.robot_id_pool) == 10
        pool_numbers = sorted(game.robot_id_pool)
        assert pool_numbers == list(range(10))

    def test_remove_nonexistent_robot_doesnt_affect_pool(self):
        """Trying to remove non-existent robot shouldn't affect pool."""
        game = GameManager()
        initial_pool = game.robot_id_pool.copy()

        success = game.remove_robot("robot99")
        assert not success
        assert game.robot_id_pool == initial_pool

    def test_failed_add_returns_id_to_pool(self):
        """If adding robot fails (e.g., invalid position), ID should return to pool."""
        game = GameManager()
        initial_pool_size = len(game.robot_id_pool)

        # Add obstacle at (0, 0)
        game.add_obstacle(0, 0)

        # Try to add robot at obstacle position (should fail)
        robot_id = game.add_robot((0, 0), (5, 5))

        # Should fail and return None
        assert robot_id is None
        # Pool should be unchanged
        assert len(game.robot_id_pool) == initial_pool_size


if __name__ == "__main__":
    test = TestRobotIDPool()
    test.test_initial_pool_has_ten_ids()
    test.test_adding_robot_uses_id_from_pool()
    test.test_can_add_exactly_ten_robots()
    test.test_cannot_add_eleventh_robot()
    test.test_removing_robot_returns_id_to_pool()
    test.test_reuses_removed_robot_id()
    test.test_lifo_behavior_for_removed_ids()
    test.test_pool_after_resize()
    test.test_remove_nonexistent_robot_doesnt_affect_pool()
    test.test_failed_add_returns_id_to_pool()
    print("\nAll robot ID pool tests passed!")