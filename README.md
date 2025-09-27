# Multi-Robot D* Lite Path Planning System

Multi-robot path planning system using D* Lite algorithm with collision detection.

## Requirements

- Python 3.8+
- Node.js 16+
- npm

## Installation

```bash
# Clone the repository
git clone https://github.com/jzender12/multi-robot-d-star-lite.git
cd multi-robot-d-star-lite
```

## Run

### Web Interface (default)
```bash
./run_dev.sh
```
Opens at http://localhost:5173

### Pygame Interface
```bash
./run_dev.sh pygame
```

## Tests

```bash
./run_tests.sh
```

---

**Note**: This project demonstrates multi-robot coordination without complex frameworks. The key insight: robots are dynamic obstacles, and D* Lite handles obstacles efficiently!