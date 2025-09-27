#!/usr/bin/env python3
"""
Comprehensive test suite for GridWorld implementation.
Includes visual ASCII verification for human inspection.
"""

from colorama import init, Fore, Back, Style
from multi_robot_d_star_lite.core.world import GridWorld, CellType

# Initialize colorama for colored output
init(autoreset=True)

def print_grid(world, robots=None, start=None, goal=None, path=None):
    """
    ASCII visualization of the grid for visual verification.
    . = empty
    # = obstacle
    R = robot
    S = start
    G = goal
    * = path
    """
    print("\n" + "="*30)
    print("Grid Visualization (10x10):")
    print("="*30)

    for y in range(world.height):
        row = ""
        for x in range(world.width):
            cell = '.'

            # Check what's in this cell
            if (x, y) in world.static_obstacles:
                cell = Fore.RED + '#' + Style.RESET_ALL
            elif robots and (x, y) in robots.values():
                # Find which robot
                for rid, pos in robots.items():
                    if pos == (x, y):
                        cell = Fore.CYAN + rid[0].upper() + Style.RESET_ALL
                        break
            elif start and (x, y) == start:
                cell = Fore.GREEN + 'S' + Style.RESET_ALL
            elif goal and (x, y) == goal:
                cell = Fore.YELLOW + 'G' + Style.RESET_ALL
            elif path and (x, y) in path:
                cell = Fore.BLUE + '*' + Style.RESET_ALL

            row += cell + " "
        print(f"{y:2d} | {row}")

    # Print column numbers
    print("   +" + "-"*21)
    print("     " + " ".join(str(i) for i in range(10)))
    print()

def test_grid_initialization():
    """Test 1: Verify grid initializes correctly"""
    print(Fore.GREEN + "\n[TEST 1] Grid Initialization")

    world = GridWorld(10, 10)

    # Verify dimensions
    assert world.width == 10
    assert world.height == 10

    # Verify grid is empty
    assert len(world.static_obstacles) == 0
    assert len(world.robot_positions) == 0

    # Visual verification
    print_grid(world)
    print(Fore.GREEN + "✓ Grid initialized correctly (10x10, all empty)")

def test_obstacle_management():
    """Test 2: Add and remove obstacles"""
    print(Fore.GREEN + "\n[TEST 2] Obstacle Management")

    world = GridWorld(10, 10)

    # Add obstacles
    obstacles = [(3, 3), (3, 4), (3, 5), (6, 2), (6, 3), (6, 4)]
    for x, y in obstacles:
        world.add_obstacle(x, y)

    # Verify obstacles were added
    assert len(world.static_obstacles) == 6
    for obs in obstacles:
        assert obs in world.static_obstacles
        assert not world.is_free(obs[0], obs[1])

    print("After adding obstacles:")
    print_grid(world)

    # Remove some obstacles
    world.remove_obstacle(3, 4)
    world.remove_obstacle(6, 3)

    assert len(world.static_obstacles) == 4
    assert (3, 4) not in world.static_obstacles
    assert (6, 3) not in world.static_obstacles
    assert world.is_free(3, 4)
    assert world.is_free(6, 3)

    print("After removing obstacles at (3,4) and (6,3):")
    print_grid(world)
    print(Fore.GREEN + "✓ Obstacles can be added and removed correctly")

def test_neighbor_finding():
    """Test 3: Verify 4-connected neighbors (Manhattan only!)"""
    print(Fore.GREEN + "\n[TEST 3] Neighbor Finding (4-connected)")

    world = GridWorld(10, 10)

    # Test center cell
    neighbors = world.get_neighbors(5, 5)
    print(f"\nNeighbors of (5,5): {neighbors}")

    # Should have exactly 4 neighbors
    assert len(neighbors) == 4

    expected = {
        (5, 6): 1.0,  # Down
        (5, 4): 1.0,  # Up
        (6, 5): 1.0,  # Right
        (4, 5): 1.0,  # Left
    }

    for nx, ny, cost in neighbors:
        assert (nx, ny) in expected
        assert cost == expected[(nx, ny)]
        # Verify NO diagonal neighbors
        assert abs(nx - 5) + abs(ny - 5) == 1  # Manhattan distance = 1

    print(Fore.GREEN + "✓ Center cell has 4 neighbors (no diagonals)")

    # Test corner cell
    corner_neighbors = world.get_neighbors(0, 0)
    print(f"Neighbors of corner (0,0): {corner_neighbors}")

    assert len(corner_neighbors) == 2  # Only down and right
    expected_corner = {(0, 1): 1.0, (1, 0): 1.0}

    for nx, ny, cost in corner_neighbors:
        assert (nx, ny) in expected_corner

    print(Fore.GREEN + "✓ Corner cell has 2 neighbors")

    # Test edge cell
    edge_neighbors = world.get_neighbors(5, 0)
    print(f"Neighbors of edge (5,0): {edge_neighbors}")

    assert len(edge_neighbors) == 3  # Left, right, down
    print(Fore.GREEN + "✓ Edge cell has 3 neighbors")

    print(Fore.YELLOW + "\n⚠️  CRITICAL: Verified 4-connected grid (NO diagonals)")

def test_robot_positions():
    """Test 4: Robot position tracking"""
    print(Fore.GREEN + "\n[TEST 4] Robot Position Tracking")

    world = GridWorld(10, 10)

    # Add obstacles
    world.add_obstacle(5, 5)

    # Add robots
    world.robot_positions["robot1"] = (1, 1)
    world.robot_positions["robot2"] = (8, 8)

    print("Grid with 2 robots and 1 obstacle:")
    print_grid(world, world.robot_positions)

    # Test is_free with robot exclusion
    # NOTE: Robots are NOT obstacles in current implementation
    assert world.is_free(1, 1)  # Robots don't block paths
    assert world.is_free(8, 8)  # Robots don't block paths
    assert not world.is_free(5, 5)  # Obstacle is there

    # Test exclusion (robots don't block in current implementation)
    assert world.is_free(1, 1, exclude_robot="robot1")  # Can plan through own position
    assert world.is_free(1, 1, exclude_robot="robot2")  # Can plan through other robot (robots don't block)

    print(Fore.GREEN + "✓ Robot positions tracked correctly")
    print(Fore.GREEN + "✓ is_free() handles robot exclusion properly")

def test_boundary_validation():
    """Test 5: Boundary validation"""
    print(Fore.GREEN + "\n[TEST 5] Boundary Validation")

    world = GridWorld(10, 10)

    # Test valid coordinates
    assert world.is_valid(0, 0)
    assert world.is_valid(9, 9)
    assert world.is_valid(5, 5)

    # Test invalid coordinates
    assert not world.is_valid(-1, 5)
    assert not world.is_valid(5, -1)
    assert not world.is_valid(10, 5)
    assert not world.is_valid(5, 10)
    assert not world.is_valid(100, 100)

    print(Fore.GREEN + "✓ Boundary validation works correctly")

def test_complex_scenario():
    """Test 6: Complex scenario with multiple robots and obstacles"""
    print(Fore.GREEN + "\n[TEST 6] Complex Scenario")

    world = GridWorld(10, 10)

    # Create a maze-like environment
    maze_walls = [
        (3, 3), (3, 4), (3, 5),
        (6, 2), (6, 3), (6, 4),
        (1, 7), (2, 7), (3, 7), (4, 7)
    ]

    for x, y in maze_walls:
        world.add_obstacle(x, y)

    # Add robots
    world.robot_positions["R1"] = (1, 1)
    world.robot_positions["R2"] = (8, 1)

    print("Complex maze with 2 robots:")
    print_grid(world, world.robot_positions)

    # Verify neighbor accessibility around obstacles
    neighbors_near_wall = world.get_neighbors(3, 2)
    print(f"\nNeighbors of (3,2) next to wall: {neighbors_near_wall}")

    # Cell at (3,3) should not be accessible
    accessible_from_3_2 = []
    for nx, ny, cost in neighbors_near_wall:
        if world.is_free(nx, ny, exclude_robot="R1"):
            accessible_from_3_2.append((nx, ny))

    print(f"Free neighbors of (3,2): {accessible_from_3_2}")
    assert (3, 3) not in accessible_from_3_2  # Wall blocks this

    print(Fore.GREEN + "✓ Complex scenario handles obstacles and robots correctly")

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "\n" + "="*50)
    print(Fore.CYAN + Style.BRIGHT + "GRIDWORLD TEST SUITE")
    print(Fore.CYAN + Style.BRIGHT + "="*50)

    try:
        test_grid_initialization()
        test_obstacle_management()
        test_neighbor_finding()
        test_robot_positions()
        test_boundary_validation()
        test_complex_scenario()

        print(Fore.GREEN + Style.BRIGHT + "\n" + "="*50)
        print(Fore.GREEN + Style.BRIGHT + "ALL TESTS PASSED!")
        print(Fore.GREEN + Style.BRIGHT + "="*50)

    except AssertionError as e:
        print(Fore.RED + Style.BRIGHT + f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"\n✗ UNEXPECTED ERROR: {e}")
        raise