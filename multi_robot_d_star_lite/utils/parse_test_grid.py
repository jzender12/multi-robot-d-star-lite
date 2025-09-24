#!/usr/bin/env python3
"""
Parser for visual test case format.
Converts visual grid representations into GridWorld setups.
"""

from ..world import GridWorld
from ..coordinator import MultiAgentCoordinator
from typing import Dict, Tuple, List


def parse_visual_grid(grid_text: str) -> Tuple[GridWorld, Dict[str, Tuple[int, int]], Dict[str, Tuple[int, int]]]:
    """
    Parse visual grid into world setup.

    Returns:
        world: GridWorld with obstacles set up
        robot_starts: Dict of robot_id -> (x, y) start position
        robot_goals: Dict of robot_id -> (x, y) goal position
    """
    lines = grid_text.strip().split('\n')

    # First line is size (e.g., "5x5")
    size_parts = lines[0].split('x')
    width = int(size_parts[0])
    height = int(size_parts[1]) if len(size_parts) > 1 else width

    # Create world
    world = GridWorld(width, height)
    robot_starts = {}
    robot_goals = {}

    # Parse grid (remaining lines)
    for y in range(height):
        if y + 1 < len(lines):
            tokens = lines[y + 1].split()
            for x in range(width):
                if x < len(tokens):
                    token = tokens[x]

                    # Handle each token type
                    if 'X' in token:
                        world.add_obstacle(x, y)

                    if '1' in token:
                        robot_starts['robot1'] = (x, y)
                    if '2' in token:
                        robot_starts['robot2'] = (x, y)

                    if 'A' in token:
                        robot_goals['robot1'] = (x, y)
                    if 'B' in token:
                        robot_goals['robot2'] = (x, y)

    return world, robot_starts, robot_goals


def setup_from_visual(grid_text: str) -> Tuple[GridWorld, MultiAgentCoordinator]:
    """
    Create a complete test setup from visual grid.

    Returns:
        world: Configured GridWorld
        coordinator: MultiAgentCoordinator with robots added
    """
    world, robot_starts, robot_goals = parse_visual_grid(grid_text)

    # Create coordinator
    coordinator = MultiAgentCoordinator(world)

    # Add robots
    if 'robot1' in robot_starts and 'robot1' in robot_goals:
        coordinator.add_robot('robot1',
                            start=robot_starts['robot1'],
                            goal=robot_goals['robot1'])

    if 'robot2' in robot_starts and 'robot2' in robot_goals:
        coordinator.add_robot('robot2',
                            start=robot_starts['robot2'],
                            goal=robot_goals['robot2'])

    return world, coordinator


def load_test_cases(filename: str = 'tests/fixtures/test_cases.txt') -> List[Tuple[str, str]]:
    """
    Load all test cases from file.

    Returns:
        List of (test_name, grid_text) tuples
    """
    test_cases = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    current_test = None
    current_grid = []
    in_grid = False

    for line in lines:
        line = line.rstrip()

        # Skip comments and empty lines
        if line.startswith('#') or not line:
            continue

        # Test name marker
        if line.startswith('TEST_'):
            # Save previous test if any
            if current_test and current_grid:
                test_cases.append((current_test, '\n'.join(current_grid)))

            current_test = line
            current_grid = []
            in_grid = False

        # Size line (e.g., "5x5")
        elif 'x' in line and not in_grid:
            in_grid = True
            current_grid.append(line)

        # Grid lines
        elif in_grid:
            current_grid.append(line)

    # Save last test
    if current_test and current_grid:
        test_cases.append((current_test, '\n'.join(current_grid)))

    return test_cases


if __name__ == "__main__":
    # Test the parser
    from simple_visualizer import SimpleVisualizer

    test_cases = load_test_cases()

    for test_name, grid_text in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {test_name}")
        print(f"{'='*50}")
        print("Grid:")
        print(grid_text)

        world, coordinator = setup_from_visual(grid_text)

        print(f"\nRobots:")
        for robot_id, pos in coordinator.current_positions.items():
            goal = coordinator.goals.get(robot_id)
            print(f"  {robot_id}: {pos} → {goal}")

        print(f"\nObstacles: {len(world.static_obstacles)}")

        # Show visual
        SimpleVisualizer.print_path(world, [], None, None,
                                   robots=world.robot_positions,
                                   title=test_name)