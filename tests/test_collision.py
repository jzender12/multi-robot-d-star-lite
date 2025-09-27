#!/usr/bin/env python3
"""
Unified test runner for all D* Lite and collision detection tests.
Loads test cases from test_cases.txt and runs appropriate test logic.
"""

from colorama import init, Fore, Style
from multi_robot_d_star_lite.utils.parse_test_grid import load_test_cases, setup_from_visual
from multi_robot_d_star_lite.pygame.simple_visualizer import SimpleVisualizer
from multi_robot_d_star_lite.path_planners.dstar_lite_planner import DStarLitePlanner
import sys

# Initialize colorama
init(autoreset=True)


def verify_manhattan_path(path):
    """
    Verify that path only uses Manhattan movement (no diagonals).
    """
    for i in range(1, len(path)):
        prev = path[i-1]
        curr = path[i]
        dx = abs(curr[0] - prev[0])
        dy = abs(curr[1] - prev[1])

        # Manhattan movement means exactly one of dx or dy is 1, the other is 0
        if not ((dx == 1 and dy == 0) or (dx == 0 and dy == 1)):
            return False, f"Non-Manhattan move from {prev} to {curr}"
    return True, "Path is Manhattan-only"


def run_single_robot_test(test_name, grid_text):
    """
    Run a single robot D* Lite pathfinding test.
    """
    print(Fore.CYAN + f"\nRunning: {test_name}")
    print(Fore.CYAN + "="*50)

    # Setup world and get robot info
    world, coordinator = setup_from_visual(grid_text)

    if 'robot1' not in coordinator.current_positions:
        print(Fore.RED + "✗ No robot1 found in test case")
        return False

    start = coordinator.current_positions['robot1']
    goal = coordinator.goals.get('robot1')

    if not goal:
        print(Fore.RED + "✗ No goal found for robot1")
        return False

    print(f"Robot1: {start} → {goal}")
    print(f"Obstacles: {len(world.static_obstacles)}")

    # Create D* Lite planner
    planner = DStarLitePlanner(world, "robot1")
    planner.initialize(start, goal)

    # Special handling for dynamic test
    if "DYNAMIC" in test_name:
        # Compute initial path
        success = planner.compute_shortest_path()
        if not success:
            print(Fore.RED + "✗ Failed to find initial path")
            return False

        initial_path = planner.get_path()
        print(f"Initial path length: {len(initial_path)}")

        # Add dynamic obstacle
        obstacle_pos = (4, 1)
        print(Fore.YELLOW + f"→ Adding obstacle at {obstacle_pos}")
        world.add_obstacle(obstacle_pos[0], obstacle_pos[1])

        # Update planner
        planner.update_edge_costs({obstacle_pos})

        # Recompute
        success = planner.compute_shortest_path()
        if not success:
            print(Fore.RED + "✗ Failed to find path after obstacle")
            return False

        new_path = planner.get_path()
        print(f"New path length: {len(new_path)}")

        # Verify obstacle avoidance
        if obstacle_pos in new_path:
            print(Fore.RED + "✗ Path goes through obstacle!")
            return False

        print(Fore.GREEN + f"✓ Successfully replanned: {len(initial_path)} → {len(new_path)} steps")

        # Visualize final path
        SimpleVisualizer.print_path(world, new_path, start, goal, title=test_name)

    else:
        # Normal pathfinding test
        success = planner.compute_shortest_path()

        if "NO_PATH" in test_name:
            # This test expects no path
            path = planner.get_path()
            if path:
                print(Fore.RED + f"✗ Path found when none expected: {len(path)} steps")
                return False
            else:
                print(Fore.GREEN + "✓ Correctly identified no path exists")
                return True
        else:
            if not success:
                print(Fore.RED + "✗ Failed to find path")
                return False

            path = planner.get_path()
            if not path:
                print(Fore.RED + "✗ Empty path returned")
                return False

            # Verify path properties
            if path[0] != start:
                print(Fore.RED + f"✗ Path doesn't start at {start}")
                return False

            if path[-1] != goal:
                print(Fore.RED + f"✗ Path doesn't end at {goal}")
                return False

            # Verify Manhattan movement
            is_manhattan, msg = verify_manhattan_path(path)
            if not is_manhattan:
                print(Fore.RED + f"✗ {msg}")
                return False

            # Verify no obstacles in path
            for x, y in path:
                if not world.is_free(x, y):
                    print(Fore.RED + f"✗ Path goes through obstacle at ({x}, {y})")
                    return False

            print(Fore.GREEN + f"✓ Valid path found: {len(path)} steps")

            # Visualize
            SimpleVisualizer.print_path(world, path, start, goal, title=test_name)

    return True


def run_multi_robot_test(test_name, grid_text):
    """
    Run a multi-robot collision detection test.
    """
    print(Fore.CYAN + f"\nRunning: {test_name}")
    print(Fore.CYAN + "="*50)

    # Setup world and coordinator
    world, coordinator = setup_from_visual(grid_text)

    # Show initial setup
    print("\nInitial setup:")
    for robot_id, pos in coordinator.current_positions.items():
        goal = coordinator.goals.get(robot_id)
        print(f"  {robot_id}: {pos} → {goal}")

    # Compute initial paths
    print("\nComputing paths...")
    coordinator.recompute_paths()

    # Show paths
    for robot_id, path in coordinator.paths.items():
        if path:
            print(f"  {robot_id} path: {path[:5]}{'...' if len(path) > 5 else ''}")
        else:
            print(f"  {robot_id}: No path found")

    # Visualize initial state
    SimpleVisualizer.print_path(world, [], None, None,
                               robots=world.robot_positions,
                               title=f"{test_name} - Initial")

    # Special handling for dynamic multi-robot test
    if "MULTI_DYNAMIC" in test_name:
        # Test dynamic obstacle addition
        obstacle_pos = (2, 2)
        print(Fore.YELLOW + f"\n→ Adding obstacle at {obstacle_pos}")
        coordinator.add_dynamic_obstacle(obstacle_pos[0], obstacle_pos[1])

        # Check if paths updated
        success = True
        for robot_id, path in coordinator.paths.items():
            if obstacle_pos in path:
                print(Fore.RED + f"✗ {robot_id} path still goes through obstacle")
                success = False

        if success:
            print(Fore.GREEN + "✓ All robots replanned around obstacle")
        return success

    # Try to step and check for collision
    print("\nChecking for collisions...")

    # Collision type descriptions for better logging
    collision_descriptions = {
        'same_cell': "Both robots trying to enter same cell",
        'swap': "Robots exchanging positions",
        'shear': "Robot entering cell that another is leaving perpendicularly"
    }

    # Determine if this test expects a collision
    expects_collision = any(x in test_name for x in ['SAME_CELL', 'SWAP', 'SHEAR'])
    expects_no_collision = any(x in test_name for x in ['PARALLEL', 'SERIES', 'OPEN_CROSSING'])

    # Test up to 10 steps
    for step in range(10):
        # Store positions before this specific step
        positions_before_step = dict(coordinator.current_positions)

        should_continue, collision = coordinator.step_simulation()

        if collision:
            robot1, robot2, collision_type = collision
            print(Fore.GREEN + f"✓ COLLISION DETECTED at step {step + 1}")
            print(Fore.YELLOW + f"  Type: {collision_type.upper()}")
            print(Fore.CYAN + f"  Description: {collision_descriptions.get(collision_type, 'Unknown collision type')}")
            print(Fore.GREEN + f"  Robots involved: {robot1} and {robot2}")

            # POSITION VERIFICATION - Critical for catching the bug
            print(Fore.CYAN + "\n  Position Verification:")
            position_check_passed = True
            for robot_id in coordinator.current_positions:
                pos_before = positions_before_step[robot_id]
                pos_after = coordinator.current_positions[robot_id]

                if pos_before == pos_after:
                    print(Fore.GREEN + f"    ✓ {robot_id}: stayed at {pos_before}")
                else:
                    print(Fore.RED + f"    ✗ {robot_id}: MOVED from {pos_before} to {pos_after}")
                    print(Fore.RED + f"      ERROR: Robot moved despite collision detection!")
                    position_check_passed = False

            if not position_check_passed:
                print(Fore.RED + "\n✗ POSITION CHECK FAILED - Robots moved after collision!")
                return False

            print(Fore.GREEN + "\n  Simulation paused (as expected)")

            # TEST: Try stepping again after collision (simulating resume)
            if collision_type in ['swap', 'same_cell', 'shear']:
                print(Fore.YELLOW + f"\n  Testing resume after {collision_type.upper()} collision:")
                positions_before_resume = dict(coordinator.current_positions)

                # Try stepping again (this simulates pressing 'P' to resume)
                should_continue2, collision2 = coordinator.step_simulation()

                # Check if robots moved on resume
                for robot_id in coordinator.current_positions:
                    pos_before = positions_before_resume[robot_id]
                    pos_after = coordinator.current_positions[robot_id]

                    if pos_before != pos_after:
                        print(Fore.RED + f"    ✗ BUG FOUND: {robot_id} moved from {pos_before} to {pos_after} after resume!")
                        print(Fore.RED + "    This explains the phasing through issue!")
                    else:
                        print(Fore.GREEN + f"    ✓ {robot_id} stayed at {pos_before} after resume")

                if collision2:
                    print(Fore.CYAN + f"    Collision still detected after resume: {collision2[2]}")
                else:
                    print(Fore.YELLOW + "    No collision detected after resume")

            # Check if we expected this type of collision
            if expects_collision:
                if 'SHEAR' in test_name and collision_type == 'shear':
                    return True
                elif 'SWAP' in test_name and collision_type == 'swap':
                    return True
                elif 'SAME_CELL' in test_name and collision_type == 'same_cell':
                    return True
                else:
                    print(Fore.RED + f"✗ Wrong collision type! Expected type based on test name")
                    return False
            elif expects_no_collision:
                print(Fore.RED + "✗ Collision detected when none expected!")
                return False
            return True

        if not should_continue:
            print(Fore.YELLOW + f"⚠ Robots reached goals at step {step + 1}")
            if expects_collision:
                print(Fore.RED + "✗ Expected collision but robots reached goals")
                return False
            elif expects_no_collision:
                print(Fore.GREEN + "✓ NO COLLISION - Robots successfully reached goals")
                if 'PARALLEL' in test_name:
                    print(Fore.CYAN + "  Movement type: Parallel (side-by-side)")
                elif 'SERIES' in test_name:
                    print(Fore.CYAN + "  Movement type: Series (convoy)")
                return True
            return True

    # No collision detected in 10 steps
    if expects_collision:
        print(Fore.RED + "✗ No collision detected within 10 steps (expected collision)")
        return False
    elif expects_no_collision:
        print(Fore.GREEN + "✓ No collisions detected (robots navigating safely)")
        return True

    print(Fore.GREEN + "✓ Test completed without issues")
    return True


def main():
    """
    Main test runner.
    """
    print(Fore.YELLOW + Style.BRIGHT + "\n" + "="*60)
    print(Fore.YELLOW + Style.BRIGHT + "UNIFIED TEST SUITE")
    print(Fore.YELLOW + Style.BRIGHT + "Running all D* Lite and collision detection tests")
    print(Fore.YELLOW + Style.BRIGHT + "="*60)

    # Load test cases
    test_cases = load_test_cases()

    if not test_cases:
        print(Fore.RED + "No test cases found!")
        return 1

    results = []
    single_robot_tests = []
    multi_robot_tests = []

    # Categorize tests
    for test_name, grid_text in test_cases:
        if '2' in grid_text:  # Has robot2
            multi_robot_tests.append((test_name, grid_text))
        else:
            single_robot_tests.append((test_name, grid_text))

    # Run single robot tests
    if single_robot_tests:
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + "SINGLE ROBOT D* LITE TESTS")
        print(Fore.CYAN + "="*60)

        for test_name, grid_text in single_robot_tests:
            try:
                passed = run_single_robot_test(test_name, grid_text)
                results.append((test_name, passed))
            except Exception as e:
                print(Fore.RED + f"✗ Test crashed: {e}")
                results.append((test_name, False))

    # Run multi-robot tests
    if multi_robot_tests:
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + "MULTI-ROBOT COLLISION TESTS")
        print(Fore.CYAN + "="*60)

        for test_name, grid_text in multi_robot_tests:
            try:
                passed = run_multi_robot_test(test_name, grid_text)
                results.append((test_name, passed))
            except Exception as e:
                print(Fore.RED + f"✗ Test crashed: {e}")
                results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS:")
    passed_count = 0
    failed_count = 0

    for test_name, passed in results:
        status = Fore.GREEN + "✓ PASS" if passed else Fore.RED + "✗ FAIL"
        print(f"  {test_name}: {status}")
        if passed:
            passed_count += 1
        else:
            failed_count += 1

    print("\n" + "="*60)
    print(f"Total: {passed_count} passed, {failed_count} failed")

    if failed_count == 0:
        print(Fore.GREEN + Style.BRIGHT + "✓ ALL TESTS PASSED!")
        return 0
    else:
        print(Fore.RED + Style.BRIGHT + f"✗ {failed_count} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())