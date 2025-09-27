# Multi-Robot D* Lite Path Planning System

A real-time multi-robot path planning system featuring both **web** and **pygame** interfaces. Watch multiple robots navigate dynamic environments using the D* Lite algorithm with intelligent collision detection and avoidance.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite

# Launch the web interface (recommended)
./run_dev.sh
# Opens at http://localhost:5173

# Or launch the pygame interface
./run_dev.sh pygame
```

That's it! The `run_dev.sh` script handles all setup automatically.

## ✨ Features

- **Dual Interfaces**: Modern web UI and classic pygame visualization
- **Real-time Path Planning**: D* Lite algorithm with dynamic replanning
- **Intelligent Collision Detection**: Detects and handles three types of collisions
- **Partial Pausing System**: Only colliding robots pause while others continue
- **Dynamic Environment**: Add/remove obstacles and robots during simulation
- **Multiple Arena Sizes**: 5x5 up to 20x20 grids
- **Visual Feedback**: Color-coded robots, paths, and collision indicators

## 🎮 Controls

### Web Interface
- **Mouse Click**: Add/remove obstacles, select robots, set goals
- **Control Panel**: Start/pause, add robots, change speed, resize arena
- **Real-time Updates**: Watch robots adapt to changes instantly

### Pygame Interface
- **SPACE**: Pause/Resume simulation
- **O**: Toggle obstacle mode (Place/Draw)
- **Click Robot**: Select robot (when paused)
- **Click Empty**: Set new goal for selected robot
- **C**: Copy grid state to clipboard (when paused)
- **Q**: Quit

## 🏗️ Architecture

The system uses a **unified package architecture** with shared core logic:

```
multi_robot_d_star_lite/
├── core/              # Shared pathfinding algorithms
│   ├── world.py       # Grid environment management
│   ├── coordinator.py # Multi-robot coordination
│   └── path_planners/ # D* Lite and other algorithms
├── pygame/            # Pygame visualization
├── web/               # FastAPI backend + React frontend
└── utils/             # Shared utilities
```

## 🤖 How It Works

1. **Independent Planning**: Each robot plans its path using D* Lite
2. **Collision Detection**: System monitors for potential collisions:
   - **Same-cell**: Two robots entering the same cell
   - **Swap**: Robots exchanging positions
   - **Shear**: Perpendicular crossing conflicts
3. **Smart Resolution**: Only involved robots pause, others continue
4. **Dynamic Replanning**: Robots adapt to obstacle changes in real-time

## 🧪 Testing

The project follows Test-Driven Development with 187+ tests:

```bash
# Run all tests
./run_tests.sh

# Run specific test suites
./run_dev.sh pytest tests/web/        # Web interface tests
./run_dev.sh pytest tests/test_world.py  # Specific test file
```

## 🔧 Development

### Requirements
- Python 3.8+
- Node.js 16+ (for web interface)
- Virtual environment support

### Installation for Development
```bash
# Install development dependencies
./run_dev.sh pip install -e .

# Run with custom Python scripts
./run_dev.sh python3 your_script.py
```

### Adding Custom Path Planners

Implement the `PathPlanner` interface to add your own algorithm:

```python
from multi_robot_d_star_lite.core.path_planners import PathPlanner

class MyPlanner(PathPlanner):
    def initialize(self, start, goal):
        # Your initialization
        pass

    def compute_shortest_path(self):
        # Your path computation
        return success, reason

    def get_path(self):
        # Return path as list of (x,y) tuples
        return path
```

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)**: Detailed technical documentation
- **[Frontend README](frontend/README.md)**: React application details
- **[API Documentation](http://localhost:8000/docs)**: FastAPI interactive docs (when running)

## 🤝 Contributing

Contributions are welcome! Please:
1. Write tests first (TDD approach)
2. Ensure all tests pass: `./run_tests.sh`
3. Update documentation as needed
4. Follow existing code patterns

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- D* Lite algorithm by Sven Koenig and Maxim Likhachev
- React + TypeScript community
- FastAPI for excellent WebSocket support

---

**Note**: This project demonstrates multi-robot coordination without complex frameworks. The key insight: robots are dynamic obstacles, and D* Lite handles obstacles efficiently!