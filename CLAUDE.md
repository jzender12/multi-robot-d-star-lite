# Multi-Robot D* Lite Path Planning System

This is a complete multi-agent path planning system using D* Lite for a 10x10 grid with multiple robots. The implementation focuses on correctness and clarity. The system demonstrates D* Lite's incremental replanning capabilities with iterative collision detection that blocks all robots involved in collisions.

**Important**: In this implementation, robots do NOT act as obstacles during path planning. This allows paths to potentially overlap, with collision detection catching conflicts at runtime and blocking affected robots until the collision is resolved.

## Understanding D* Lite

D* Lite maintains two distance values for each cell: the g-value (current best distance) and the rhs-value (one-step lookahead distance). When these values disagree, the cell is inconsistent and needs processing. The algorithm searches backward from goal to start, enabling efficient replanning as the robot moves.

## Key Design Decisions

### 4-Connected Grid with Manhattan Distance
- **Movement**: Robots can only move to cardinal neighbors (up, down, left, right) - no diagonal movement
- **Heuristic**: Manhattan distance (`|x1-x2| + |y1-y2|`)
- **Cost**: All moves have cost 1.0

### Multi-Agent Coordination Strategy
1. **Independent Planning**: Robots plan paths without considering other robots as obstacles
2. **Iterative Collision Detection**: Single-pass algorithm with cascading detection
   - **Same-Cell**: Both robots trying to enter the same cell
   - **Swap**: Robots exchanging positions
   - **Shear**: Robot entering cell that another is leaving perpendicularly
   - **Blocked Robot**: Robot trying to move through a collision-blocked robot's position
3. **Collision Resolution via Obstacles**: Placing obstacles during collisions can resolve deadlocks
   - All robots replan when obstacles change
   - Collisions are recalculated with new paths
   - Robots automatically unblock when collisions no longer exist
4. **Stuck Robot Handling**: Robots unable to reach goals are visually indicated and logged
   - Simulation continues without pausing
   - Red border indicates stuck robots
   - Game log shows warning messages
5. **Dynamic Replanning**: When obstacles are added/removed, all robots replan using D* Lite's incremental updates
6. **Clean Slate Resizing**: Arena resize clears everything and places robot1 at start
7. **Duplicate Prevention**: Robots cannot share starting positions

## Project Structure (Unified Package)

```
multi-robot-d-star-lite/
├── multi_robot_d_star_lite/    # Main Python package (unified structure)
│   ├── __init__.py             # Package initialization with exports
│   ├── core/                   # Core pathfinding logic (shared by all interfaces)
│   │   ├── __init__.py
│   │   ├── world.py            # Grid environment with 4-connected movement
│   │   ├── coordinator.py      # Multi-agent coordination with collision detection
│   │   └── path_planners/      # Path planning algorithms
│   │       ├── __init__.py
│   │       ├── base_planner.py       # Abstract base planner
│   │       └── dstar_lite_planner.py # D* Lite algorithm (iteration limit: width*height*100)
│   ├── [REMOVED] pygame/       # Pygame interface removed for simplification
│   ├── web/                    # Web application (modern interface)
│   │   ├── __init__.py
│   │   ├── __main__.py         # Entry point for web server
│   │   ├── main.py             # FastAPI application with WebSocket support
│   │   └── game_manager.py     # Game state manager for web interface
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       ├── export_grid.py      # Export current state to visual format
│       ├── parse_test_grid.py  # Parser for visual test format
│       └── colors.py           # Dynamic color generation for robots
├── frontend/                    # React TypeScript frontend (Vite)
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Grid2D.tsx      # Interactive 2D grid visualization
│   │   │   ├── Controls.tsx    # Control panel component
│   │   │   └── StatusPanel.tsx # Status and info display
│   │   ├── store/              # State management (Zustand)
│   │   │   └── gameStore.ts    # Game state and WebSocket management
│   │   └── App.tsx            # Main application component
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite configuration
├── tests/                      # All test files (108 tests passing)
│   ├── web/                    # Web application tests
│   │   ├── test_game_manager.py      # GameManager tests
│   │   ├── test_game_manager_stuck.py # Stuck robot detection in web
│   │   └── test_websocket.py         # WebSocket endpoint tests
│   ├── test_world.py           # Grid world functionality tests
│   ├── test_iterative_collision_system.py  # Iterative collision detection tests
│   ├── test_placement_validation.py  # Placement validation tests
│   ├── test_robot_management.py      # Robot add/remove tests
│   ├── test_world_resize.py          # Arena resizing tests
│   ├── test_stuck_robot_detection.py # Stuck robot detection tests
│   ├── test_export.py                # Grid export functionality tests
│   ├── test_color_generation.py      # Color generation tests
│   ├── test_world.py                 # World management tests
│   └── fixtures/
│       └── test_cases.txt      # Visual test cases for all tests
├── [REMOVED] main.py           # Removed with pygame interface
├── run_dev.sh                  # Universal launcher with RAII-style venv management
├── run_tests.sh                # Test runner for all components
├── requirements.txt            # All dependencies (core + pygame + web + testing)
├── setup.py                    # Package installation configuration
├── pyproject.toml             # Modern Python project configuration
├── tox.ini                    # Testing automation
├── README.md                  # Public documentation
├── CLAUDE.md                  # This file - internal documentation
├── .gitignore                 # Git ignore patterns
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions CI/CD pipeline
```

## Core Implementation Details

### GridWorld (core/world.py)
- Manages grid with static obstacles and robot positions
- `is_free()` checks if a cell is traversable (only checks static obstacles, NOT robots)
- `get_neighbors()` returns only 4 cardinal neighbors with cost 1.0
- Robots stored in `robot_positions` but don't block paths during planning
- **NEW**: `resize(width, height)` - Dynamically resize grid (3x3 to 30x30)
  - Preserves obstacles within new bounds
  - Removes out-of-bounds content
  - Enforces min/max size limits

### D* Lite Algorithm (core/path_planners/dstar_lite_planner.py)
- **Critical**: `km` parameter accumulates with each robot move for correctness
- Uses Manhattan heuristic: `abs(a[0] - b[0]) + abs(a[1] - b[1])`
- Lexicographic priority queue ordering via tuple comparison
- `update_edge_costs()` enables incremental replanning when obstacles change

### Multi-Agent Coordinator (core/coordinator.py)
Key methods:
- `recompute_paths()`: Computes paths for all robots after changes
- `calculate_collisions()`: Iterative collision detection algorithm:
  1. **Pass 1 - Path Collisions**: Detects same-cell, swap, and shear collisions between robot pairs
  2. **Pass 2 - Blocked Robot Collisions**: Iteratively finds robots blocked by collision-blocked robots
  - Continues iterating until no new collisions found (handles cascades elegantly)
  - Returns dict mapping robot_id to collision reason (e.g., "swap_collision", "blocked_robot_collision")
  - Note: Robots moving in same direction (series/convoy) are correctly allowed
- `step_simulation()`: Moves robots, detects collisions, and identifies stuck robots
  - Uses `calculate_collisions()` for comprehensive detection
  - Returns tuple: (should_continue, collision_info, stuck_robots, collision_blocked_robots)
  - Stuck robots continue simulation without blocking
- `set_new_goal()`: Sets new goal with validation:
  - Returns `True` if successful, `False` if invalid
  - Prevents goals on obstacles
  - Prevents multiple robots having same goal
- **NEW**: `remove_robot(robot_id)` - Remove a robot from the system
- **NEW**: `get_next_robot_id()` - Generate next sequential robot ID
- **NEW**: `clear_all_robots()` - Remove all robots
- **NEW**: `resize_world(width, height)` - Resize to clean slate with robot1
- **NEW**: `reset_to_default()` - Reset to 10x10 clean slate
- **NEW**: `add_robot()` returns bool - False if position occupied

### Visualization

#### [REMOVED] Pygame Interface
The pygame interface has been completely removed to simplify the codebase and focus on the web interface. All pygame-related components including the visualizer, game log panel, and UI components have been deleted.

#### Web Interface (web/main.py & frontend/)
- **FastAPI Backend**: WebSocket server for real-time communication
- **React Frontend**: Modern TypeScript UI with Vite build system
- **Zustand State Management**: Centralized game state
- **Real-time Updates**: WebSocket-based bidirectional communication
- **Interactive Grid**: Click to add/remove obstacles, set goals
- **Responsive Design**: Works on desktop and tablet devices

### Shared Utilities

#### Color Generation (utils/colors.py)
- **Dynamic color generation**: Unique colors for unlimited robots
- **HSV color space**: Even distribution around color wheel
- **Predefined colors**: Robot1 (blue) and Robot2 (red) fixed
- **Color sets**: Matching colors for robot/goal/path
- **Color caching**: Consistent colors across sessions

**Note**: `main.py` now serves as a simple entry point for the pygame version

## Unified Package Architecture

The project has been restructured into a unified Python package that supports both pygame and web interfaces:

### Why Unified Structure?
- **Code Reuse**: Core pathfinding logic shared between interfaces
- **Maintainability**: Single source of truth for algorithms
- **Flexibility**: Easy to add new interfaces (CLI, API, etc.)
- **Testing**: Unified test suite covers all components

### Package Organization
- `core/`: Contains all pathfinding logic, world management, and coordination
- `web/`: Modern web interface with React frontend and FastAPI backend
- `utils/`: Shared utilities
- **Removed**: `pygame/` directory and all pygame-related code

## Recent Features (Added via TDD)

### Stuck Robot Detection
- **Problem**: Robots would appear paused when goals blocked but UI showed "Running"
- **Solution**: Added stuck robot detection that continues simulation
- **Implementation**:
  - `coordinator.step_simulation()` returns stuck robots list
  - Visual red border indicator for stuck robots
  - Warning messages in game log
  - Simulation continues without pausing

### Game Log Panel
- **Problem**: Status messages at bottom were hard to track
- **Solution**: Added dedicated scrollable log panel on left side
- **Implementation**:
  - 200px wide panel with timestamp support
  - Color-coded messages by type
  - Auto-scroll with manual override
  - Mouse wheel scrolling support

### Obstacle Draw Mode
- **Problem**: Placing multiple obstacles required many clicks
- **Solution**: Added draw mode for continuous obstacle placement
- **Implementation**:
  - Toggle between Place and Draw modes via button or 'O' key
  - Place Mode: Click individual cells (default behavior)
  - Draw Mode: Click and drag to place obstacles continuously
  - Maintains all placement validation (no obstacles on robots/goals)
  - Visual mode indicator in control panel

### Iterative Collision System Overhaul
- **Problem**: Pair-based collision system was complex and couldn't handle cascades properly
- **Solution**: Iterative detection algorithm that finds all collisions systematically
- **Implementation**:
  - **Pass 1**: Detects path-to-path collisions (same_cell, swap, shear) between all robot pairs
  - **Pass 2**: Iteratively detects blocked robot collisions (cascade detection)
    - Each iteration finds robots trying to move through blocked robots
    - Continues until no new collisions found (convergence)
    - Maximum 100 iterations to prevent infinite loops
  - No collision pairs tracking - simpler state management
  - All robots involved in collisions blocked simultaneously (fairness)
  - Renamed all "paused_robots" references to "collision_blocked_robots" for clarity
- **Testing**:
  - Created `test_iterative_collision_system.py` with 8 comprehensive tests
  - Test coverage: basic collisions, cascade chains (5+ robots), multiple simultaneous collisions, recovery scenarios
  - Deleted 5 obsolete test files based on old pair system
- **Benefits**:
  - Handles cascade collisions elegantly through iteration
  - Cleaner code - removed ~200 lines of pair management
  - More predictable behavior - no arbitrary priorities
  - Simpler recovery logic - just recalculate collisions each step

### Pygame Interface Removal
- **Problem**: Maintaining two interfaces (pygame and web) created complexity
- **Solution**: Complete removal of pygame interface
- **Changes**:
  - Deleted entire `multi_robot_d_star_lite/pygame/` directory
  - Removed `main.py` (pygame entry point)
  - Deleted pygame-specific tests
  - Updated package imports and documentation
- **Result**: Cleaner codebase focused on web interface

### Frontend-Backend Collision Format Fix
- **Problem 1**: Frontend crashed (white screen) when collisions occurred
  - Backend sent: `{"robot1": "swap", "robot2": "swap"}`
  - Frontend expected: `[{type: "swap", robots: ["robot1", "robot2"]}]`
- **Problem 2**: "undefined" robot in collision messages after goal changes
  - Single robots could end up alone in collision type groups
  - Frontend assumed all collisions involve 2+ robots
- **Solution**:
  - Updated `_get_collision_info()` in `game_manager.py` to format properly
  - Added pairing logic for path collisions (swap, same_cell, shear)
  - Frontend gracefully handles both paired and single-robot collisions
- **Result**: Stable web interface with proper collision display and no crashes

## Installation and Setup

```bash
# Install system dependencies (one-time setup)
sudo apt-get install python3-venv python3-pip nodejs npm

# Clone and setup
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite

# Install package in development mode (optional)
./run_dev.sh pip install -e .

# The run_dev.sh script handles all virtual environment setup automatically
```

## Running the Application

### Web Interface (Default - Recommended)
```bash
# Launch web application (default mode)
./run_dev.sh
# Opens: Backend at http://localhost:8000, Frontend at http://localhost:5173
```

### [REMOVED] Pygame Interface
```bash
# Pygame interface has been removed for simplification
# Use the web interface instead: ./run_dev.sh
```

### Custom Commands
```bash
# Run any Python command in the virtual environment
./run_dev.sh python3 your_script.py
```

## Running Tests

```bash
# Run all tests (recommended - uses helper script)
./run_tests.sh

# Run all tests manually
./run_dev.sh pytest tests/

# Run with coverage
./run_dev.sh pytest tests/ --cov=multi_robot_d_star_lite

# Run specific test categories
./run_dev.sh pytest tests/web/          # Web interface tests
./run_dev.sh pytest tests/test_world.py # Specific test file

# Run with tox for multiple Python versions
./run_dev.sh tox
```

## Controls

### Web Interface Controls
- **Click Grid**: Add/remove obstacles
- **Click Robot**: Select robot (when paused)
- **Click Empty Cell**: Set goal for selected robot
- **Control Panel**:
  - Start/Pause/Reset simulation
  - Add/Remove robots
  - Clear obstacles
  - Adjust simulation speed
  - Arena size presets

### [REMOVED] Pygame Interface Controls
The pygame interface has been removed. Please use the web interface controls instead.

## Using run_dev.sh

The `run_dev.sh` script is the universal launcher that provides RAII-style virtual environment management:

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
- Installs all dependencies from requirements.txt
- Launches the requested interface (web by default, pygame with 'pygame' argument)
- Runs your command in the proper environment
- Cleans up on exit (even on errors)

### Script Modes:
- **No arguments**: Launches web application (backend + frontend)
- **Any other command**: Executes in virtual environment
- **Note**: Pygame mode has been removed

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

1. **Initial State**: Clean 10x10 grid with robot0 at (0,0), goal at (9,9)
2. **Path Planning**: Each robot runs D* Lite independently WITHOUT considering other robots
3. **Collision Detection**: Iterative system checks for collisions BEFORE movement:
   - Same-cell: Both robots trying to enter same position
   - Swap: Robots exchanging positions
   - Shear: Perpendicular crossing where one robot enters a cell another is leaving
   - Blocked Robot: Robot trying to move through a collision-blocked robot's position
4. **Collision Blocking**: All robots involved in collisions are blocked (orange border)
   - Non-colliding robots continue moving normally
   - Blocked robots keep their paths visible
   - Cascading collisions handled through iteration
5. **Collision Resolution via Obstacles**:
   - Placing obstacles triggers replanning for ALL robots
   - Collisions are recalculated with new paths
   - Robots automatically unblock if no longer in collision
6. **Placement Validation**: Prevents invalid configurations:
   - Goals cannot be placed on obstacles
   - Multiple robots cannot have the same goal or position
   - Obstacles cannot be placed on robots or goals
7. **Arena Resizing**: Creates clean slate with robot0 only
8. **Dynamic Updates**: When obstacles change, D* Lite efficiently replans using incremental updates

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

## Import Structure

With the unified package architecture, imports are organized by module:

```python
# Core components (shared by all interfaces)
from multi_robot_d_star_lite.core import GridWorld, MultiAgentCoordinator
from multi_robot_d_star_lite.core.path_planners import DStarLitePlanner

# Pygame interface components - REMOVED
# The pygame interface has been completely removed

# Web interface components
from multi_robot_d_star_lite.web import GameManager
from multi_robot_d_star_lite.web.main import app  # FastAPI app

# Shared utilities
from multi_robot_d_star_lite.utils.colors import get_robot_color
from multi_robot_d_star_lite.utils.export_grid import export_to_visual_format
```

## Test-Driven Development

This project follows TDD principles with comprehensive test coverage:
- **108 passing tests** across all components (streamlined after pygame removal)
- Test files for each major component
- Visual test format for complex scenarios
- Tests written BEFORE implementation

### Test Coverage:
- Core functionality:
  - Robot management: 13 tests - duplicate prevention, add/remove
  - World resizing: 17 tests - clean slate behavior
  - Placement validation: 11 tests - goal/obstacle validation
  - Stuck robot detection: 11 tests - detection, recovery, simulation continuity
  - Iterative collision detection: 8 tests - all collision types and cascades
  - Color generation: 15 tests - dynamic colors for unlimited robots
- Web interface:
  - WebSocket communication: 9 tests
  - Game manager: 9 tests including collision handling
  - Stuck robot detection in web: 10 tests
- All obsolete pygame and pair-based collision tests removed

### Recent Test Fixes:
- `test_no_duplicate_start_positions`: Now correctly expects False return
- `test_coordinator_resize_clean_slate`: Tests clean slate behavior
- `test_full_resize_workflow`: Validates robot1 placement after resize

## Future Enhancements

For production systems:
- Spatial indexing for faster neighbor queries
- CBS (Conflict-Based Search) for many robots
- Compiled extensions for performance
- Predictive collision avoidance
- Multi-resolution planning for large grids
- Custom arena size input dialog
- Waypoint-based path editing
- Path history visualization

## Summary

This implementation demonstrates that multi-agent pathfinding doesn't require complex frameworks. By leveraging D* Lite's natural obstacle avoidance and adding simple temporal collision resolution, we achieve robust multi-robot coordination. The unified package architecture allows us to provide both traditional pygame visualization and modern web interfaces while sharing the same core pathfinding logic.

### Key Achievements:
- **Simplified Architecture**: Focused on web interface after pygame removal
- **Iterative Collision System**: Elegant handling of complex collision cascades
- **Modern Stack**: React + TypeScript frontend with FastAPI backend
- **Comprehensive Testing**: 108 tests ensure reliability
- **Developer Experience**: Simple `run_dev.sh` handles all complexity
- **Frontend Stability**: Fixed crash issues and proper collision display

The key insight is understanding that robots are just dynamic obstacles, and D* Lite already knows how to handle obstacles efficiently. The modular architecture ensures that future interfaces can easily be added without duplicating core logic.

## Development Guidelines

- Always run tests after making changes: `./run_tests.sh`
- Use TDD: Write tests first, then implementation
- Keep core logic in `core/` module, UI-specific code in respective modules
- Update both CLAUDE.md (internal) and README.md (public) when adding features
- Ensure all tests pass before committing changes