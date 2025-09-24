# Multi-Robot D* Lite Path Planning System

This is a complete multi-agent path planning system using D* Lite for a 10x10 grid with two robots. The implementation focuses on correctness and clarity. The system demonstrates D* Lite's incremental replanning capabilities with collision detection that pauses simulation when robots would collide.

**Important**: In this implementation, robots do NOT act as obstacles during path planning. This allows paths to potentially overlap, with collision detection catching conflicts at runtime and pausing the simulation for user intervention.

## Understanding D* Lite

D* Lite maintains two distance values for each cell: the g-value (current best distance) and the rhs-value (one-step lookahead distance). When these values disagree, the cell is inconsistent and needs processing. The algorithm searches backward from goal to start, enabling efficient replanning as the robot moves.

## Key Design Decisions

### 4-Connected Grid with Manhattan Distance
- **Movement**: Robots can only move to cardinal neighbors (up, down, left, right) - no diagonal movement
- **Heuristic**: Manhattan distance (`|x1-x2| + |y1-y2|`)
- **Cost**: All moves have cost 1.0

### Multi-Agent Coordination Strategy
1. **Independent Planning**: Robots plan paths without considering other robots as obstacles
2. **Comprehensive Collision Detection**: System detects three collision types and pauses simulation:
   - **Same-Cell**: Both robots trying to enter the same cell
   - **Swap**: Robots exchanging positions
   - **Shear**: Robot entering cell that another is leaving perpendicularly
3. **Dynamic Replanning**: When obstacles are added/removed, all robots replan using D* Lite's incremental updates

## Project Structure

```
multi-robot-d-star-lite/
├── multi_robot_d_star_lite/    # Main Python package
│   ├── __init__.py
│   ├── world.py                # Grid environment with 4-connected movement
│   ├── dstar_lite.py           # Core D* Lite algorithm (iteration limit: width*height*100)
│   ├── coordinator.py          # Multi-agent coordination with collision detection
│   ├── visualizer.py           # Pygame visualization with interactive controls
│   ├── simple_visualizer.py    # ASCII visualization for debugging
│   └── utils/
│       ├── __init__.py
│       ├── export_grid.py      # Export current state to visual format
│       └── parse_test_grid.py  # Parser for visual test format
├── tests/                       # All test files
│   ├── __init__.py
│   ├── requirements.txt        # Test-specific dependencies
│   ├── test_world.py           # Grid world functionality tests
│   ├── test_collision.py       # Collision detection tests (formerly test_all.py)
│   ├── test_placement_validation.py  # Placement validation tests
│   ├── test_export.py          # Export/import test
│   └── fixtures/
│       └── test_cases.txt      # Visual test cases for all tests
├── main.py                      # Main demo with dynamic obstacles and goal setting
├── run_dev.sh                   # Virtual environment manager with RAII-style cleanup
├── requirements.txt             # Core dependencies (numpy, pygame, colorama)
├── setup.py                     # Package installation configuration
├── pyproject.toml              # Modern Python project configuration
├── tox.ini                     # Testing automation
├── README.md                    # Public documentation
├── CLAUDE.md                    # This file - internal documentation
├── .gitignore                  # Git ignore patterns
└── .github/
    └── workflows/
        └── ci.yml               # GitHub Actions CI/CD pipeline
```

## Core Implementation Details

### GridWorld (world.py)
- Manages grid with static obstacles and robot positions
- `is_free()` checks if a cell is traversable (only checks static obstacles, NOT robots)
- `get_neighbors()` returns only 4 cardinal neighbors with cost 1.0
- Robots stored in `robot_positions` but don't block paths during planning

### D* Lite Algorithm (dstar_lite.py)
- **Critical**: `km` parameter accumulates with each robot move for correctness
- Uses Manhattan heuristic: `abs(a[0] - b[0]) + abs(a[1] - b[1])`
- Lexicographic priority queue ordering via tuple comparison
- `update_edge_costs()` enables incremental replanning when obstacles change

### Multi-Agent Coordinator (coordinator.py)
Key methods:
- `recompute_paths()`: Computes paths for all robots after changes
- `detect_collision_at_next_step()`: Comprehensive collision detection that checks for:
  1. **Same-cell collisions**: Both robots entering same position
  2. **Swap collisions**: Robots exchanging positions
  3. **Shear collisions**: Perpendicular crossing (one enters as another exits)
  - Note: Robots moving in the same direction (series/convoy) are correctly allowed
- `step_simulation()`: Moves robots and reports collisions without auto-resolution
- `set_new_goal()`: Sets new goal with validation:
  - Returns `True` if successful, `False` if invalid
  - Prevents goals on obstacles
  - Prevents multiple robots having same goal

### Visualization (visualizer.py & __main__.py)
Interactive features:
- **Start paused**: Shows initial setup with clear "PAUSED" overlay
- **Dynamic goal setting**: While paused, click robot then click to set new goal
- **Obstacle manipulation**: Click to add/remove obstacles with validation
- **Placement validation**: Prevents invalid placements:
  - Cannot place obstacles on robots or goals
  - Cannot place goals on obstacles or other robot goals
- **Visual feedback**: Selected robots highlighted, paths shown in different colors

**Note**: `main.py` now simply imports from `__main__.py` to avoid code duplication

## Installation and Setup

```bash
# Install system dependencies (one-time setup)
sudo apt-get install python3-venv python3-pip

# Clone and setup
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite

# Install package in development mode
./run_dev.sh pip install -e .
```

## Running the Demo

```bash
# Run the main demo
./run_dev.sh python3 main.py

# Alternative: After installation
python3 main.py
```

## Running Tests

```bash
# Run all tests with pytest
./run_dev.sh pytest tests/

# Run with coverage
./run_dev.sh pytest tests/ --cov=multi_robot_d_star_lite

# Run specific test
./run_dev.sh pytest tests/test_world.py

# Run with tox for multiple Python versions
./run_dev.sh tox
```

## Controls

- **SPACE**: Pause/Resume simulation
- **While paused**:
  - Click robot to select (yellow highlight)
  - Click empty cell to set new goal
  - Click to add/remove obstacles
  - **C**: Copy current grid state to clipboard
- **While running**:
  - Click: Add/remove obstacles
- **Q**: Quit

**Validation**: The system prevents invalid placements:
- Cannot place obstacles on robots or goals
- Cannot place goals on obstacles
- Cannot have two robots with the same goal

## Using run_dev.sh

The `run_dev.sh` script provides RAII-style virtual environment management:

```bash
# Run any Python script
./run_dev.sh python3 main.py

# Run all tests with pytest
./run_dev.sh pytest tests/

# Run specific test file
./run_dev.sh pytest tests/test_world.py

# Run with coverage
./run_dev.sh pytest tests/ --cov=multi_robot_d_star_lite

# Run with tox
./run_dev.sh tox
```

The script automatically:
- Creates/activates virtual environment
- Installs requirements.txt
- Runs your command
- Cleans up on exit (even on errors)

## Visual Test Format

Test cases are defined in `test_cases.txt` using an intuitive visual format:

```
TEST_NAME
5x5
1 . . . A   # 1=robot1 start, A=robot1 goal
. X X X .   # X=obstacle, .=empty
. . . . .
. X X X .
B . . . 2   # 2=robot2 start, B=robot2 goal
```

### Tools for Test Cases

- **multi_robot_d_star_lite/utils/parse_test_grid.py**: Parses visual format into GridWorld setup
- **multi_robot_d_star_lite/utils/export_grid.py**: Exports current grid state to visual format
- **tests/test_collision.py**: Unified test runner that loads all tests from test_cases.txt

During simulation, press 'C' when paused to copy the current grid state to clipboard for creating new test cases.

## How It Works

1. **Path Planning**: Each robot runs D* Lite independently WITHOUT considering other robots
2. **Collision Detection**: System checks for three types of collisions:
   - Same-cell: Both robots trying to enter same position
   - Swap: Robots exchanging positions
   - Shear: Perpendicular crossing where one robot enters a cell another is leaving
3. **Collision Response**: Simulation PAUSES when collision detected, displaying the specific collision type
4. **Placement Validation**: Prevents invalid configurations:
   - Goals cannot be placed on obstacles
   - Multiple robots cannot have the same goal
   - Obstacles cannot be placed on robots or goals
5. **Dynamic Updates**: When obstacles change, D* Lite efficiently replans using incremental updates

## Key Insights from Development

### Current Implementation Approach
- Robots plan independently without considering each other as obstacles
- This can lead to path overlaps, which are caught by collision detection
- Simulation pauses on collision, displaying the collision type (same-cell, swap, or shear)
- Series movement (convoy) and parallel movement are correctly allowed without triggering collisions
- This approach is simpler and makes robot behavior more predictable

### Why This Design
- Treating robots as obstacles can lead to no valid paths in tight spaces
- Independent planning ensures robots always find paths if one exists
- Collision detection provides safety without complex resolution logic

### Critical Implementation Details
1. **km accumulation**: Must update every robot move, not just during replanning
2. **Iteration limit**: Set to width * height * 100 to handle complex grids
3. **Manhattan heuristic**: Uses 4-connected grid, no diagonal movement
4. **Dynamic obstacles**: Modify world and call `update_edge_costs()` for efficient replanning

## Future Enhancements

For production systems:
- Spatial indexing for faster neighbor queries
- CBS (Conflict-Based Search) for many robots
- Compiled extensions for performance
- Predictive collision avoidance
- Multi-resolution planning for large grids

## Summary

This implementation demonstrates that multi-agent pathfinding doesn't require complex frameworks. By leveraging D* Lite's natural obstacle avoidance and adding simple temporal collision resolution, we achieve robust multi-robot coordination. The key is understanding that robots are just dynamic obstacles, and D* Lite already knows how to handle obstacles efficiently.