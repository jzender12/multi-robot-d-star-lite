"""
Test stuck robot detection in GameManager integration.
GameManager should always report stuck robots, even when paused.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_robot_d_star_lite.web.game_manager import GameManager


class TestGameManagerStuckDetection:
    """Test that GameManager properly reports stuck robots."""

    def test_stuck_robot_in_initial_state(self):
        """Stuck robots should be detected even in initial paused state."""
        game = GameManager(10, 10)

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

        # Block the path
        for x in range(10):
            game.add_obstacle(x, 5)

        state = game.get_state()

        # Check robot info
        assert "robots" in state
        assert "robot0" in state["robots"]
        robot_info = state["robots"]["robot0"]

        assert "is_stuck" in robot_info, "Robot info should have is_stuck flag"
        assert robot_info["is_stuck"] == True, "robot0 should be marked as stuck"

    def test_stuck_cleared_after_path_opens(self):
        """Stuck status should clear when path becomes available."""
        game = GameManager(10, 10)

        # Block the path
        for x in range(10):
            game.add_obstacle(x, 5)

        state = game.get_state()
        assert "robot0" in state["stuck_robots"], "Should be stuck initially"

        # Clear one obstacle
        game.remove_obstacle(5, 5)

        state = game.get_state()
        assert "robot0" not in state["stuck_robots"], "Should not be stuck after path opens"

        # Check is_stuck flag
        robot_info = state["robots"]["robot0"]
        assert robot_info["is_stuck"] == False, "is_stuck flag should be False"

    def test_stuck_robot_during_simulation(self):
        """Stuck robots should be detected during running simulation."""
        game = GameManager(10, 10)

        # Create a situation where robot will become stuck
        for x in range(10):
            game.add_obstacle(x, 5)

        # Resume and step
        game.resume()
        state = game.step()

        assert "robot0" in state["stuck_robots"], "Should detect stuck during step"

    def test_multiple_stuck_robots_reported(self):
        """All stuck robots should be reported."""
        game = GameManager(10, 10)

        # Add more robots
        robot2 = game.add_robot((1, 1), (8, 8))
        robot3 = game.add_robot((2, 2), (7, 7))

        # Block all paths
        for x in range(10):
            game.add_obstacle(x, 5)

        state = game.get_state()

        assert len(state["stuck_robots"]) == 3, "All three robots should be stuck"
        assert "robot0" in state["stuck_robots"]
        assert robot2 in state["stuck_robots"]
        assert robot3 in state["stuck_robots"]

    def test_stuck_vs_paused_distinction(self):
        """Stuck and paused robots should be reported separately."""
        game = GameManager(10, 10)

        # Add collision robots
        game.add_robot((1, 0), (0, 0))  # Will swap with robot0

        # Add stuck robot
        stuck_id = game.add_robot((5, 0), (5, 9))
        for x in range(10):
            game.add_obstacle(x, 2)

        # Step to trigger potential collision
        game.resume()
        state = game.step()

        # Check separate lists
        assert "stuck_robots" in state
        assert "paused_robots" in state

        # stuck_id should only be in stuck list
        assert stuck_id in state["stuck_robots"]
        assert stuck_id not in state["paused_robots"], "Should not be both stuck and paused"

    def test_stuck_persists_when_paused(self):
        """Stuck status should persist when simulation is paused."""
        game = GameManager(10, 10)

        # Block path
        for x in range(10):
            game.add_obstacle(x, 5)

        # Resume, step, then pause
        game.resume()
        game.step()
        game.pause()

        # Should still show as stuck when paused
        state = game.get_state()
        assert "robot0" in state["stuck_robots"], "Stuck status should persist when paused"

    def test_stuck_robot_at_goal_not_stuck(self):
        """Robot at goal should never be stuck."""
        game = GameManager(10, 10)

        # Set goal to current position
        game.set_goal("robot0", 0, 0)

        state = game.get_state()
        assert "robot0" not in state["stuck_robots"], "Robot at goal is not stuck"

        # Check flag
        robot_info = state["robots"]["robot0"]
        assert robot_info["is_stuck"] == False, "is_stuck should be False at goal"

    def test_stuck_after_resize(self):
        """Stuck detection should work after arena resize."""
        game = GameManager(10, 10)

        # Resize arena (creates new robot1)
        game.resize_arena(15, 15)

        # Block the new robot's path
        for x in range(15):
            game.add_obstacle(x, 5)

        state = game.get_state()
        # After resize, there should be robot0
        if "robot0" in state["robots"]:
            assert "robot0" in state["stuck_robots"], "Robot should be stuck after resize"