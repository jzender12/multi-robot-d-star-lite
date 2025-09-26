# Multi-Robot D* Lite Path Planning

Multi-robot path planning demo using D* Lite algorithm with collision detection.

## Requirements

- Python 3.8+
- python3-venv

<<<<<<< HEAD
- **D* Lite Algorithm**: Efficient incremental path replanning for dynamic environments
- **Multi-Robot Coordination**: Support for multiple robots navigating simultaneously
- **Collision Detection**: Three types of collision detection:
  - Same-cell collisions (robots trying to occupy same position)
  - Swap collisions (robots exchanging positions)
  - Shear collisions (perpendicular crossing conflicts)
- **Dynamic Obstacles**: Real-time obstacle addition/removal with automatic replanning
- **Interactive Visualization**: Pygame-based GUI with real-time simulation
- **Game Log Panel**: Scrollable event log with timestamped, color-coded messages
- **Stuck Robot Detection**: Visual indicators when robots cannot reach their goals
- **Enhanced Control Panel**: Comprehensive controls for:
  - Adding/removing robots dynamically
  - Resizing arena (5x5 to 30x30)
  - Speed control
  - Obstacle mode toggle (Place/Draw modes)
  - Clear all obstacles / Reset simulation
- **Three-Panel Layout**: Clean interface with Log (left), Grid (center), and Control Panel (right)
- **Dynamic Color Generation**: Automatic color assignment for unlimited robots
- **Visual Test Format**: Intuitive ASCII-based test case definitions

## Quick Start

The easiest way to get started:
=======
## Installation
>>>>>>> 716763ffe1614a8d2d1b213e99649f1037e851c2

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

<<<<<<< HEAD
## Usage

### Getting Started

The simulation starts with a clean slate:
- 10x10 grid (no obstacles)
- Robot1 at top-left corner (0,0)
- Robot1's goal at bottom-right corner (9,9)

Build your scenario by:
- **Adding robots**: Use the "Add Robot" button
- **Placing obstacles**: Click on grid cells (Place mode) or drag to draw walls (Draw mode)
- **Resizing arena**: Select size (creates new clean slate)

### Running the Interactive Demo

Simply run:

```bash
./run_app.sh
```

### Using in Your Own Python Code

```python
from multi_robot_d_star_lite import GridWorld, DStarLite, MultiAgentCoordinator

# Create a 10x10 grid world
world = GridWorld(10, 10)

# Add obstacles
world.add_obstacle(5, 5)

# Create coordinator for multi-robot planning
coordinator = MultiAgentCoordinator(world)

# Add robots with start and goal positions
coordinator.add_robot("robot1", start=(0, 0), goal=(9, 9))
coordinator.add_robot("robot2", start=(9, 0), goal=(0, 9))

# Compute paths
coordinator.recompute_paths()

# Step through simulation
should_continue, collision = coordinator.step_simulation()
```

#### Controls

- **SPACE**: Pause/Resume simulation
- **O**: Toggle obstacle mode (Place/Draw)
- **While paused**:
  - Click robot to select (yellow highlight)
  - Click empty cell to set new goal
  - Click to add/remove obstacles
    - **Place Mode**: Click individual cells
    - **Draw Mode**: Click and drag to draw walls
  - **C**: Copy grid state to clipboard for test cases
- **While running**:
  - Click to add/remove obstacles dynamically
- **Mouse Wheel**: Scroll through game log messages
- **Q**: Quit

**Control Panel**:
- **Add Robot**: Add new robot at free position
- **Remove Robot**: Remove selected robot
- **Obstacle Mode**: Toggle between Place and Draw modes
- **Arena Size** (10x10, 15x15, 20x20): Resize and reset to clean slate
- **Speed +/-**: Control simulation speed
- **Reset**: Return to default 10x10 with robot1 only

**Note**: The system prevents invalid placements:
- Cannot place obstacles on robots or goals
- Cannot place goals on obstacles
- Cannot have two robots with the same goal or position

### Running Tests

```bash
# Run all tests
./run_dev.sh pytest tests/

# Run with coverage
./run_dev.sh pytest tests/ --cov=multi_robot_d_star_lite

# Run specific test file
./run_dev.sh pytest tests/test_world.py

# Run with tox for multiple Python versions
./run_dev.sh tox
```

## Architecture

### Project Structure

```
multi-robot-d-star-lite/
├── multi_robot_d_star_lite/    # Main package
│   ├── world.py                # Grid environment with resizing
│   ├── dstar_lite.py           # D* Lite algorithm
│   ├── coordinator.py          # Multi-agent coordination & robot management
│   ├── visualizer.py           # Pygame visualization with three-panel layout
│   ├── game_log.py             # Scrollable game log component
│   ├── ui_components.py        # Control panel UI components
│   ├── simple_visualizer.py    # ASCII visualization
│   └── utils/
│       ├── export_grid.py      # Grid export utilities
│       ├── parse_test_grid.py  # Test case parser
│       └── colors.py           # Dynamic color generation
├── tests/                       # Test suite (118+ tests)
│   ├── test_world.py           # World tests
│   ├── test_collision.py       # Collision detection tests
│   ├── test_placement_validation.py # Placement validation tests
│   ├── test_robot_management.py    # Robot management tests
│   ├── test_world_resize.py        # World resizing tests
│   ├── test_pausing_behavior.py    # Stuck robot detection tests
│   ├── test_game_log.py            # Game log component tests
│   ├── test_visualizer_with_log.py # Visualizer integration tests
│   ├── test_color_generation.py    # Color generation tests
│   ├── test_control_panel.py       # UI component tests
│   ├── test_export.py          # Export/import tests
│   └── fixtures/
│       └── test_cases.txt      # Visual test cases
└── main.py                      # Demo entry point
```

### Key Components

- **GridWorld**: Manages the grid environment with obstacles and robot positions
- **DStarLite**: Implements the D* Lite incremental pathfinding algorithm
- **MultiAgentCoordinator**: Coordinates multiple robots and detects collisions
- **Visualizer**: Provides real-time pygame visualization

## Test Case Format

Test cases use an intuitive visual format in `tests/fixtures/test_cases.txt`:

```
TEST_NAME
5x5
1 . . . A   # 1=robot1 start, A=robot1 goal
. X X X .   # X=obstacle, .=empty
. . . . .
. X X X .
B . . . 2   # 2=robot2 start, B=robot2 goal
```

## Algorithm Details

### D* Lite

The implementation uses D* Lite for efficient replanning in dynamic environments:
- Searches backward from goal to start
- Maintains g-values (current best distance) and rhs-values (one-step lookahead)
- Uses Manhattan distance heuristic for 4-connected grid
- Iteration limit: width × height × 100

### Multi-Agent Coordination

- Robots plan paths independently without considering other robots as obstacles
- Comprehensive collision detection catches conflicts at runtime
- Simulation pauses on collision detection for user intervention
- Stuck robots (no path to goal) are visually indicated and logged
- Simulation continues when robots are stuck, allowing dynamic resolution
=======
## License
>>>>>>> 716763ffe1614a8d2d1b213e99649f1037e851c2

MIT