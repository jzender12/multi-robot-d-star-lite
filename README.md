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
./run_dev.sh python main.py
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

### Running the Interactive Demo

After installation, you can run the demo in several ways:

```bash
# If installed from GitHub with pip
python -m multi_robot_d_star_lite

# If cloned for development
./run_dev.sh python main.py
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

- **P**: Pause/Resume simulation
- **While paused**:
  - Click robot to select (yellow highlight)
  - Click empty cell to set new goal (auto-resumes)
  - Click to add/remove obstacles
- **While running**:
  - **SPACE**: Add obstacle at (5,5)
  - **R**: Remove obstacle at (5,5)
  - Click to add/remove obstacles dynamically
- **C** (while paused): Copy grid state to clipboard for test cases
- **Q**: Quit

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
│   ├── world.py                # Grid environment
│   ├── dstar_lite.py           # D* Lite algorithm
│   ├── coordinator.py          # Multi-agent coordination
│   ├── visualizer.py           # Pygame visualization
│   ├── simple_visualizer.py    # ASCII visualization
│   └── utils/
│       ├── export_grid.py      # Grid export utilities
│       └── parse_test_grid.py  # Test case parser
├── tests/                       # Test suite
│   ├── test_world.py           # World tests
│   ├── test_collision.py       # Collision detection tests
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
- Series movement (convoy) and parallel movement are correctly allowed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- D* Lite algorithm by Sven Koenig and Maxim Likhachev
- Built with Python, NumPy, and Pygame