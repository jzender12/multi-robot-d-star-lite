# Multi-Robot D* Lite Path Planning

[![CI](https://github.com/jzender12/multi-robot-d-star-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/jzender12/multi-robot-d-star-lite/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python implementation of the D* Lite algorithm for multi-robot path planning with comprehensive collision detection on a 2D grid.

## Features

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

## Installation

### Method 1: Install from GitHub with pip (Recommended for Users)

Install directly from GitHub without cloning:

```bash
# Install the package and all dependencies
pip install git+https://github.com/jzender12/multi-robot-d-star-lite.git

# Run the demo as a Python module
python -m multi_robot_d_star_lite
```

### Method 2: Clone and Use run_dev.sh (Recommended for Development)

The easiest way for development is using the provided script:

```bash
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite
./run_dev.sh python3 main.py
```

The `run_dev.sh` script automatically:
- Creates/activates a virtual environment
- Installs all dependencies
- Runs your command
- Cleans up on exit

### Method 3: Manual Installation (For Development)

```bash
# Clone the repository
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in editable mode
pip install -e .

# Run the demo
python main.py
# Or as a module
python -m multi_robot_d_star_lite
```

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

After installation, you can run the demo in several ways:

```bash
# If installed from GitHub with pip
python -m multi_robot_d_star_lite

# If cloned for development
./run_dev.sh python3 main.py
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

