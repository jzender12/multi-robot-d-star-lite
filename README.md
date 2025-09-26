# Multi-Robot D* Lite Path Planning

Multi-robot path planning demo using D* Lite algorithm with collision detection.

## Requirements

- Python 3.8+
- python3-venv

## Installation

```bash
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite
./run_app.sh
```

The `run_app.sh` script handles virtual environment setup and dependency installation.

## Game Setup

The simulation starts with:
- 10x10 grid world
- Robot0 at position (0,0) with goal at (9,9)
- No obstacles initially

You can:
- Add up to 10 robots dynamically
- Click to place/remove obstacles
- Resize the arena (10x10, 15x15, 20x20)
- Click robots to select them and set new goals

## Controls

- **SPACE**: Pause/Resume
- **Click robot**: Select (when paused)
- **Click empty cell**: Set new goal for selected robot
- **Click grid**: Add/remove obstacles
- **Q**: Quit

Control panel buttons handle robot management and arena sizing.

## Adding Your Own Planner

To add a custom path planning algorithm, implement the `PathPlanner` interface:

```python
from multi_robot_d_star_lite.path_planners.base_planner import PathPlanner

class MyPlanner(PathPlanner):
    def initialize(self, start, goal):
        # Initialize your planner
        pass

    def compute_shortest_path(self):
        # Compute the path
        return success, reason

    def get_path(self):
        # Return list of (x,y) positions
        return path

    def update_edge_costs(self, changed_cells):
        # Handle dynamic obstacle changes
        pass

    def get_algorithm_name(self):
        return "My Algorithm"
```

Then use it in the coordinator:
```python
coordinator.add_robot("robot0", start=(0,0), goal=(9,9), planner_class=MyPlanner)
```

## Collision Handling

The system detects three types of collisions:
- Same-cell: Two robots trying to occupy the same position
- Swap: Robots exchanging positions
- Shear: Perpendicular crossing conflicts

When a collision is detected, the simulation pauses. **Collision resolution is a separate planning problem that should be triggered at this point - implementation is a TODO**. Users can manually resolve by changing goals or obstacles.

## Development

```bash
# Run tests
./run_dev.sh pytest tests/

# Interactive shell in venv
./run_dev.sh bash

# Run any Python script
./run_dev.sh python3 script.py
```

## License

MIT