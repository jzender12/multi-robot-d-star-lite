"""
Test stuck robot detection in GameManager for web interface.
"""

import pytest
import sys
import os

# Add parent directory to path to import the game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from multi_robot_playground.web.game_manager import GameManager


class TestGameManagerStuckDetection:
    """Test that GameManager properly reports stuck robots."""

    def test_stuck_robot_in_initial_state(self):
        """Stuck robots should be detected even in initial paused state."""
        game = GameManager(10, 10)

        # Add a robot first
        game.add_robot((0, 0), (9, 9))

        # Block robot0's path to (9,9)
        for x in range(10):
            game.add_obstacle(x, 5)

        # Get initial state (paused)
        state = game.get_state()

        assert "stuck_robots" in state, "State should include stuck_robots"
        assert isinstance(state["stuck_robots"], list), "stuck_robots should be a list"
        assert "robot0" in state["stuck_robots"], "robot0 should be stuck with blocked path"

    def test_stuck_robot_after_adding(self):
        """Newly added stuck robots should be detected immediately."""
        game = GameManager(10, 10)

        # Add a new robot with blocked goal
        robot_id = game.add_robot((2, 2), (8, 8))

        # Block the new robot's goal
        for x in range(7, 10):
            for y in range(7, 10):
                if (x, y) != (8, 8):
                    game.add_obstacle(x, y)

        # Isolate the goal
        for x in range(6, 10):
            game.add_obstacle(x, 6)
        for y in range(6, 10):
            game.add_obstacle(6, y)

        state = game.get_state()
        assert robot_id in state["stuck_robots"], "New robot should be detected as stuck"

    def test_stuck_robot_info_flag(self):
        """Robot info should include is_stuck flag."""
        game = GameManager(10, 10)

        # Add a robot first
        game.add_robot((0, 0), (9, 9))

        # Block the path
        for x in range(10):
            game.add_obstacle(x, 5)

        state = game.get_state()
        assert "robot0" in state["robots"], "robot0 should exist"
        assert "is_stuck" in state["robots"]["robot0"], "Robot should have is_stuck flag"
        assert state["robots"]["robot0"]["is_stuck"] == True, "Robot should be marked as stuck"

    def test_stuck_cleared_after_path_opens(self):
        """Stuck status clears when path becomes available."""
        game = GameManager(10, 10)

        # Add a robot first
        game.add_robot((0, 0), (9, 9))

        # Block the path initially
        for x in range(10):
            game.add_obstacle(x, 5)

        # Check initially stuck
        state = game.get_state()
        assert "robot0" in state["stuck_robots"], "Should be stuck initially"

        # Open a path
        game.remove_obstacle(4, 5)

        # Check no longer stuck
        state = game.get_state()
        assert "robot0" not in state["stuck_robots"], "Should not be stuck after path opens"
        assert state["robots"]["robot0"]["is_stuck"] == False, "is_stuck flag should be False"

    def test_stuck_robot_during_simulation(self):
        """Stuck detection works during active simulation."""
        game = GameManager(10, 10)

        # Add a robot first
        game.add_robot((0, 0), (9, 9))

        # Block after a few cells
        for x in range(10):
            game.add_obstacle(x, 3)

        game.resume()
        # Step the simulation
        for _ in range(5):
            state = game.step()

        # Should detect stuck during simulation
        assert "robot0" in state["stuck_robots"], "Should detect stuck during step"

    def test_multiple_stuck_robots_reported(self):
        """Multiple stuck robots are all reported."""
        game = GameManager(10, 10)

        # Add three robots
        game.add_robot((0, 0), (9, 9))
        game.add_robot((1, 1), (8, 8))
        game.add_robot((2, 2), (7, 7))

        # Block all paths with a wall
        for x in range(10):
            game.add_obstacle(x, 5)

        state = game.get_state()
        assert len(state["stuck_robots"]) == 3, "All three robots should be stuck"
        assert "robot0" in state["stuck_robots"]
        assert "robot1" in state["stuck_robots"]
        assert "robot2" in state["stuck_robots"]

    def test_stuck_vs_paused_distinction(self):
        """Stuck robots different from collision-paused robots."""
        game = GameManager(10, 10)

        # Add two robots that will collide
        game.add_robot((0, 0), (2, 0))
        game.add_robot((2, 0), (0, 0))

        game.resume()
        state = game.step()

        # Both might be paused due to collision
        collision_info = state.get("collision_info", {})

        # Add wall to make robot stuck
        game.add_robot((5, 5), (9, 9))
        for x in range(10):
            game.add_obstacle(x, 7)

        state = game.get_state()

        # robot2 should be stuck but not necessarily collision-paused
        assert "robot2" in state["stuck_robots"], "robot2 should be stuck"

        # Check both flags exist and are distinct
        for robot_id in state["robots"]:
            robot_info = state["robots"][robot_id]
            assert "is_stuck" in robot_info, f"{robot_id} should have is_stuck flag"
            assert "is_paused" in robot_info, f"{robot_id} should have is_paused flag"

    def test_stuck_persists_when_paused(self):
        """Stuck status persists regardless of pause state."""
        game = GameManager(10, 10)

        # Add a robot first
        game.add_robot((0, 0), (9, 9))

        # Block path
        for x in range(10):
            game.add_obstacle(x, 5)

        # Check while paused
        state = game.get_state()
        assert state["paused"] == True
        assert "robot0" in state["stuck_robots"], "Stuck status should persist when paused"

        # Resume and check
        game.resume()
        state = game.get_state()
        assert state["paused"] == False
        assert "robot0" in state["stuck_robots"], "Stuck status should persist when running"

        # Pause again
        game.pause()
        state = game.get_state()
        assert state["paused"] == True
        assert "robot0" in state["stuck_robots"], "Stuck status should persist after re-pause"

    def test_stuck_robot_at_goal_not_stuck(self):
        """Robot at goal is not stuck even if no path exists."""
        game = GameManager(10, 10)

        # Add a robot already at its goal
        game.add_robot((5, 5), (5, 5))

        # Surround with obstacles (robot is already at goal)
        for x in range(4, 7):
            for y in range(4, 7):
                if (x, y) != (5, 5):
                    game.add_obstacle(x, y)

        state = game.get_state()
        assert "robot0" not in state["stuck_robots"], "Robot at goal should not be stuck"
        assert state["robots"]["robot0"]["is_stuck"] == False

    def test_stuck_after_resize(self):
        """Stuck detection works after arena resize."""
        game = GameManager(10, 10)

        # Resize arena - creates clean slate
        game.resize_arena(5, 5)

        # Add a robot after resize
        game.add_robot((0, 0), (4, 4))

        # Block path in smaller arena
        for x in range(5):
            game.add_obstacle(x, 2)

        state = game.get_state()
        assert state["width"] == 5
        assert state["height"] == 5
        assert "robot0" in state["stuck_robots"], "Should detect stuck in resized arena"