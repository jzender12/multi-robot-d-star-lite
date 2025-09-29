# Multi-Robot Playground

Multi-robot path planning playground with collision detection. Currently implements D* Lite algorithm with support for multiple pathfinding algorithms.

## Requirements

- Python 3.8+
- Node.js 16+
- npm

## Installation

```bash
# Clone the repository
git clone https://github.com/jzender12/multi-robot-playground.git
cd multi-robot-playground
```

## Run

```bash
./run_dev.sh
```
Opens at http://localhost:5173

## How to Play

### Basic Gameplay
1. **Start** the simulation - robots will automatically move toward their goals
2. **Add robots** using the "Add Robot" or "Random Robot" buttons (up to 10 total)
3. **(Re)Set goals** - pause simulation for easier selection, select a robot by clicking it, then click an empty cell to set the new goal for the robot
4. **Place/remove obstacles** - click cells with "Draw" or "Erase" cursors to add/remove obstacles and watch robots replan
5. **Observe collisions** - when paths conflict, robots are blocked and highlighted in orange

### Controls
- **Space**: Pause/Resume simulation
- **1/2/3**: Switch cursor modes (Select/Draw/Erase)
- **Escape**: Deselect robot
- **Speed Control**: Adjust simulation speed with +/- buttons
- **Clear Board**: Remove all obstacles and robots

### How It Works
- Robots plan paths independently without considering each other
- Paths are submitted to a central coordinator
- The coordinator detects and enforces collision prevention
- When collisions occur, affected robots are blocked (orange border)

### Collision Types
- **Same Cell**: Two robots trying to enter the same cell
- **Swap**: Robots trying to exchange positions
- **Shear**: Perpendicular crossing conflict, one robot is leaving a cell as another perpendicularly enters
- **Cascade/Blocking**: Chain reaction when blocked robots block others

### Tips & Notes
- This is a sandbox for experimenting with multi-robot pathfinding
- Some collisions can be resolved by strategic obstacle placement or removal
- Not all collisions can be resolved with obstacle manipulation alone
- Red border = stuck robot (no path to goal)
- Orange border = collision-blocked robot
- Future releases will include teleoperation and collision resolution planners

## Tests

```bash
./run_tests.sh
```

---
