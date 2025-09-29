"""
FastAPI application with WebSocket endpoint for Multi-Robot D* Lite.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from typing import Dict, Any

from .game_manager import GameManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Multi-Robot D* Lite API")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Robot D* Lite WebSocket API"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for game communication."""
    await manager.connect(websocket)
    game = GameManager()

    try:
        # Send initial state
        await websocket.send_json(game.get_state())

        while True:
            # Receive command from client
            data = await websocket.receive_json()
            command_type = data.get("type")

            logger.info(f"Received command: {command_type}")

            # Process commands
            if command_type == "step":
                response = game.step()
                await websocket.send_json(response)

            elif command_type == "add_obstacle":
                x, y = data.get("x"), data.get("y")
                response = game.add_obstacle(x, y)
                await websocket.send_json(response)

            elif command_type == "remove_obstacle":
                x, y = data.get("x"), data.get("y")
                response = game.remove_obstacle(x, y)
                await websocket.send_json(response)

            elif command_type == "set_goal":
                robot_id = data.get("robot_id")
                x, y = data.get("x"), data.get("y")
                success = game.set_goal(robot_id, x, y)
                if success:
                    await websocket.send_json(game.get_state())
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to set goal for {robot_id}"
                    })

            elif command_type == "add_robot":
                start = tuple(data.get("start", [0, 0]))
                goal = tuple(data.get("goal", [9, 9]))
                robot_id = game.add_robot(start, goal)
                if robot_id:
                    await websocket.send_json(game.get_state())
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to add robot"
                    })

            elif command_type == "pause":
                game.pause()
                await websocket.send_json(game.get_state())

            elif command_type == "resume":
                game.resume()
                await websocket.send_json(game.get_state())

            elif command_type == "reset":
                game.reset()
                await websocket.send_json(game.get_state())

            elif command_type == "remove_robot":
                robot_id = data.get("robot_id")
                if robot_id:
                    success = game.remove_robot(robot_id)
                    if success:
                        await websocket.send_json(game.get_state())
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to remove {robot_id}"
                        })

            elif command_type == "resize_arena":
                width = data.get("width", 10)
                height = data.get("height", 10)
                response = game.resize_arena(width, height)
                await websocket.send_json(response)

            elif command_type == "clear_obstacles":
                # Clear all obstacles
                response = game.clear_obstacles()
                await websocket.send_json(response)

            else:
                # Unknown command
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)