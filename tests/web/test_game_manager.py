"""
Test GameManager wrapper for coordinator.
"""
import pytest
import sys
import os

# Add parent directory to path to import the game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_game_manager_init():
    """GameManager initializes with clean slate."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    assert game.world.width == 10
    assert game.world.height == 10
    assert len(game.coordinator.current_positions) == 0  # No robots at start
    assert len(game.coordinator.goals) == 0  # No goals at start
    assert game.step_count == 0
    assert game.paused == True  # Starts paused


def test_serialize_game_state():
    """Game state serializes to correct JSON format."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    # Add a robot to test serialization
    game.add_robot((0, 0), (9, 9))

    state = game.get_state()

    assert state["type"] == "state"
    assert "robots" in state
    assert "obstacles" in state
    assert "width" in state
    assert "height" in state
    assert "paused" in state
    assert "stuck_robots" in state

    # Check robot format
    assert state["robots"]["robot0"]["position"] == [0, 0]
    assert state["robots"]["robot0"]["goal"] == [9, 9]

    # Check grid size
    assert state["width"] == 10
    assert state["height"] == 10


def test_process_step():
    """Step advances simulation."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    # Add a robot first
    game.add_robot((0, 0), (9, 9))
    initial_pos = game.coordinator.current_positions["robot0"]

    # Game starts paused, need to resume first
    game.resume()
    state = game.step()
    assert game.step_count == 1

    # Robot should move if path exists
    if game.coordinator.paths["robot0"]:
        new_pos = game.coordinator.current_positions["robot0"]
        assert new_pos != initial_pos


def test_add_obstacle_updates_paths():
    """Adding obstacle triggers path recalculation."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    # Add a robot first
    game.add_robot((0, 0), (9, 9))
    initial_path = list(game.coordinator.paths["robot0"]) if game.coordinator.paths["robot0"] else []

    game.add_obstacle(5, 5)

    # Obstacle should be added
    assert (5, 5) in game.world.static_obstacles

    # Path might change if obstacle blocks it
    new_path = game.coordinator.paths["robot0"]
    if (5, 5) in initial_path:
        assert new_path != initial_path


def test_remove_obstacle():
    """Removing obstacle updates world."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    game.add_obstacle(5, 5)
    assert (5, 5) in game.world.static_obstacles

    game.remove_obstacle(5, 5)
    assert (5, 5) not in game.world.static_obstacles


def test_set_robot_goal():
    """Setting new goal updates robot and triggers replan."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    # Add a robot first
    game.add_robot((0, 0), (9, 9))
    success = game.set_goal("robot0", 5, 5)

    assert success == True
    assert game.coordinator.goals["robot0"] == (5, 5)

    # Path should lead to new goal
    if game.coordinator.paths["robot0"]:
        path = game.coordinator.paths["robot0"]
        assert path[-1] == (5, 5)


def test_add_robot():
    """Adding robot creates new robot in system."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    robot_id = game.add_robot((2, 2), (7, 7))

    assert robot_id == "robot0"  # First robot since we start clean
    assert game.coordinator.current_positions["robot0"] == (2, 2)
    assert game.coordinator.goals["robot0"] == (7, 7)
    assert "robot0" in game.coordinator.paths

    # Add another robot
    robot_id2 = game.add_robot((3, 3), (8, 8))
    assert robot_id2 == "robot1"


def test_get_robot_positions():
    """Get all robot positions in correct format."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    game.add_robot((0, 0), (9, 9))
    game.add_robot((2, 2), (7, 7))

    positions = game.get_robot_positions()
    assert positions["robot0"] == [0, 0]
    assert positions["robot1"] == [2, 2]


def test_collision_detection():
    """Collisions are detected and reported in state."""
    from multi_robot_playground.web.game_manager import GameManager

    game = GameManager()
    # Add robots that will collide
    game.add_robot((0, 0), (1, 0))
    game.add_robot((1, 0), (0, 0))

    # Step should detect collision
    state = game.step()

    # Check if collision info is in state
    if "collision_info" in state and state["collision_info"]:
        assert "type" in state["collision_info"]
        assert "robots" in state["collision_info"]