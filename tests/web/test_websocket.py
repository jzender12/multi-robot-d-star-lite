"""
Test WebSocket connection and basic commands.
Following TDD - writing tests before implementation.
"""
import pytest
import json
from fastapi.testclient import TestClient


def test_websocket_connection():
    """WebSocket accepts connection and sends initial state."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Should receive initial state immediately
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert "robots" in data
        assert "obstacles" in data
        assert "width" in data
        assert "height" in data
        assert data["width"] == 10


def test_receive_initial_state():
    """Initial state contains correct game setup."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

        # Check initial state has no robots (clean slate)
        assert len(data["robots"]) == 0

        # Check initial grid
        assert data["width"] == 10
        assert data["height"] == 10
        assert data["obstacles"] == []


def test_step_command():
    """Step command advances simulation and returns updated state."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        initial = websocket.receive_json()

        # Add a robot first
        websocket.send_json({
            "type": "add_robot",
            "x": 0,
            "y": 0,
            "goal_x": 9,
            "goal_y": 9
        })
        robot_added = websocket.receive_json()

        # Resume the game first (starts paused)
        websocket.send_json({"type": "resume"})
        resumed = websocket.receive_json()

        # Send step command
        websocket.send_json({"type": "step"})

        # Receive updated state
        updated = websocket.receive_json()
        assert updated["type"] == "state"
        # Robot should have moved (if path exists)
        if "robot0" in updated["robots"] and updated["robots"]["robot0"].get("path"):
            assert updated["robots"]["robot0"]["position"] != robot_added["robots"]["robot0"]["position"]


def test_add_obstacle_command():
    """Add obstacle command updates grid and triggers replan."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Add a robot first
        websocket.send_json({
            "type": "add_robot",
            "x": 0,
            "y": 0,
            "goal_x": 9,
            "goal_y": 9
        })
        robot_added = websocket.receive_json()

        # Add obstacle at (5, 5)
        websocket.send_json({
            "type": "add_obstacle",
            "x": 5,
            "y": 5
        })

        # Receive updated state
        updated = websocket.receive_json()
        assert updated["type"] == "state"
        assert [5, 5] in updated["obstacles"]
        # Path should be recalculated
        assert "robot0" in updated["robots"]


def test_remove_obstacle_command():
    """Remove obstacle command updates grid."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Add obstacle first
        websocket.send_json({"type": "add_obstacle", "x": 5, "y": 5})
        websocket.receive_json()

        # Remove obstacle
        websocket.send_json({
            "type": "remove_obstacle",
            "x": 5,
            "y": 5
        })

        # Receive updated state
        updated = websocket.receive_json()
        assert [5, 5] not in updated["obstacles"]


def test_set_goal_command():
    """Set goal command updates robot goal and replans."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Add a robot first
        websocket.send_json({
            "type": "add_robot",
            "x": 0,
            "y": 0,
            "goal_x": 9,
            "goal_y": 9
        })
        robot_added = websocket.receive_json()

        # Set new goal for robot0
        websocket.send_json({
            "type": "set_goal",
            "robot_id": "robot0",
            "x": 5,
            "y": 5
        })

        # Receive updated state
        updated = websocket.receive_json()
        assert updated["robots"]["robot0"]["goal"] == [5, 5]
        # Path should be recalculated to new goal
        if updated["robots"]["robot0"].get("path") and len(updated["robots"]["robot0"]["path"]) > 0:
            assert updated["robots"]["robot0"]["path"][-1] == [5, 5]


def test_add_robot_command():
    """Add robot command creates new robot."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Add new robot
        websocket.send_json({
            "type": "add_robot",
            "start": [2, 2],
            "goal": [7, 7]
        })

        # Receive updated state
        updated = websocket.receive_json()
        assert "robot0" in updated["robots"]
        assert updated["robots"]["robot0"]["position"] == [2, 2]
        assert updated["robots"]["robot0"]["goal"] == [7, 7]


def test_invalid_command_handling():
    """Invalid commands return error message."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send invalid command
        websocket.send_json({
            "type": "invalid_command"
        })

        # Should receive error response
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "message" in response


def test_pause_resume_command():
    """Pause and resume commands control simulation state."""
    from multi_robot_d_star_lite.web.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send pause command
        websocket.send_json({"type": "pause"})
        response = websocket.receive_json()
        assert response["paused"] == True

        # Send resume command
        websocket.send_json({"type": "resume"})
        response = websocket.receive_json()
        assert response["paused"] == False