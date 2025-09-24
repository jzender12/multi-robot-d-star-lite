#!/usr/bin/env python3
"""
Main demonstration of Multi-Agent D* Lite pathfinding.
Two robots navigate a 10x10 grid, avoiding obstacles and each other.
This allows the package to be run as a module: python -m multi_robot_d_star_lite
"""

import pygame
import time
from .world import GridWorld
from .dstar_lite import DStarLite
from .coordinator import MultiAgentCoordinator
from .visualizer import GridVisualizer
from .utils.export_grid import export_to_visual_format, copy_to_clipboard

def main():
    """
    Main function to run the multi-agent D* Lite demonstration.
    Creates a 10x10 grid with 2 robots navigating around obstacles.
    """

    # Create the world
    print("Initializing 10x10 grid world...")
    world = GridWorld(10, 10)

    # Add some initial obstacles to make it interesting
    # Create a small maze-like environment
    obstacles = [
        (3, 3), (3, 4), (3, 5),  # Vertical wall
        (6, 2), (6, 3), (6, 4),  # Another vertical wall
        (1, 7), (2, 7), (3, 7), (4, 7),  # Horizontal wall
    ]

    for x, y in obstacles:
        world.add_obstacle(x, y)

    # Create coordinator
    print("Initializing multi-agent coordinator...")
    coordinator = MultiAgentCoordinator(world)

    # Add two robots with different start/goal positions
    # Robot 1: Top-left to bottom-right
    coordinator.add_robot("robot1", start=(1, 1), goal=(8, 8))

    # Robot 2: Top-right to bottom-left
    coordinator.add_robot("robot2", start=(8, 1), goal=(1, 8))

    # Initial path computation
    print("Computing initial paths...")
    coordinator.recompute_paths()

    # Create visualizer
    visualizer = GridVisualizer(world)

    # Run simulation
    print("\n" + "="*50)
    print("MULTI-AGENT D* LITE DEMO")
    print("="*50)
    print("\nControls:")
    print("  SPACE - Add dynamic obstacle at (5,5)")
    print("  R     - Remove obstacle at (5,5)")
    print("  P     - Pause/Resume")
    print("  C     - Copy current setup to clipboard (when paused)")
    print("  Click - Add/remove obstacle (when running)")
    print("  When paused:")
    print("    - Click robot to select it")
    print("    - Click again to set new goal")
    print("  Q     - Quit")
    print("\n" + "="*50)

    running = True
    step_count = 0
    sim_speed = 2  # Steps per second
    last_step_time = time.time()
    paused = True  # Start paused
    dynamic_obstacle_added = False
    info_text = "PAUSED - Press P to start, or click a robot to set new goal"
    selected_robot = None  # For goal setting

    while running:
        # Handle events
        events = visualizer.handle_events()

        if events['quit']:
            running = False

        elif events['space'] and not dynamic_obstacle_added:
            # Add dynamic obstacle
            print("Adding dynamic obstacle at (5, 5)...")
            coordinator.add_dynamic_obstacle(5, 5)
            dynamic_obstacle_added = True
            info_text = "Dynamic obstacle added - robots replanning"

        elif events['r'] and dynamic_obstacle_added:
            # Remove dynamic obstacle
            print("Removing obstacle at (5, 5)...")
            world.remove_obstacle(5, 5)

            # Just recompute paths - the obstacle is gone from the world
            coordinator.recompute_paths()
            dynamic_obstacle_added = False
            info_text = "Obstacle removed - paths updated"

        elif events['p']:
            # Pause/unpause
            paused = not paused
            selected_robot = None  # Clear any selection when toggling pause
            if paused:
                info_text = "PAUSED - Click robot to select, then click to set goal"
            else:
                info_text = "Running - Robots navigating using D* Lite"
            print("PAUSED" if paused else "RESUMED")

        elif events.get('c', False) and paused:
            # Copy current setup to clipboard when paused
            grid_export = export_to_visual_format(world, coordinator)
            if copy_to_clipboard(grid_export):
                info_text = "Grid copied to clipboard! Paste it as a test case"
                print("Grid state copied to clipboard:")
                print(grid_export)
            else:
                info_text = "Failed to copy to clipboard - see console output"
                print("Could not copy to clipboard. Here's the grid state:")
                print(grid_export)

        elif events['left_click']:
            x, y = events['left_click']

            if paused and selected_robot:
                # We're in goal-setting mode
                # Check if clicked position is valid for a goal
                if not ((x, y) in world.static_obstacles):
                    # Set new goal for selected robot
                    coordinator.set_new_goal(selected_robot, (x, y))
                    info_text = f"New goal set for {selected_robot} at ({x}, {y}) - Press P to resume"
                    selected_robot = None  # Clear selection
                else:
                    info_text = "Cannot place goal on obstacle"

            elif paused:
                # Check if we clicked on a robot
                robot = coordinator.get_robot_at_position((x, y))
                if robot:
                    selected_robot = robot
                    info_text = f"Selected {robot} - Click to set new goal"
                else:
                    # Not on a robot, toggle obstacle
                    if (x, y) in world.static_obstacles:
                        world.remove_obstacle(x, y)
                        info_text = f"Removed obstacle at ({x}, {y})"
                    else:
                        world.add_obstacle(x, y)
                        info_text = f"Added obstacle at ({x}, {y})"
                    # Pass the changed cell so D* Lite can update properly
                    coordinator.recompute_paths(changed_cells={(x, y)})

            else:
                # Not paused - just add/remove obstacles
                # Don't allow placing obstacles on robots or goals
                is_robot_pos = any(pos == (x, y) for pos in coordinator.current_positions.values())
                is_goal_pos = any(goal == (x, y) for goal in coordinator.goals.values())

                if not is_robot_pos and not is_goal_pos:
                    if (x, y) in world.static_obstacles:
                        world.remove_obstacle(x, y)
                        info_text = f"Removed obstacle at ({x}, {y})"
                    else:
                        world.add_obstacle(x, y)
                        info_text = f"Added obstacle at ({x}, {y})"
                    # Pass the changed cell so D* Lite can update properly
                    coordinator.recompute_paths(changed_cells={(x, y)})

        # Step simulation at controlled rate
        current_time = time.time()
        if not paused and current_time - last_step_time > 1.0 / sim_speed:
            # Move robots one step
            should_continue, collision = coordinator.step_simulation()

            if collision:
                # Collision detected - pause and show warning
                robot1, robot2, collision_type = collision

                # Create descriptive messages for each collision type
                collision_messages = {
                    'same_cell': f"SAME-CELL COLLISION! {robot1} and {robot2} trying to enter same cell - PAUSED",
                    'swap': f"SWAP COLLISION! {robot1} and {robot2} exchanging positions - PAUSED",
                    'shear': f"SHEAR COLLISION! {robot1} entering cell as {robot2} exits perpendicularly - PAUSED"
                }

                info_text = collision_messages.get(collision_type, f"COLLISION ({collision_type})! {robot1} and {robot2} - PAUSED")
                print(f"⚠ Collision detected: {collision_type.upper()}")
                print(f"  {info_text}")
                paused = True
            elif should_continue:
                step_count += 1

                # Check if both robots reached goals
                all_at_goal = all(
                    coordinator.current_positions[rid] == coordinator.goals[rid]
                    for rid in coordinator.planners.keys()
                )

                if all_at_goal:
                    info_text = "SUCCESS! All robots reached their goals!"
                    print(info_text)
                    paused = True
            else:
                info_text = "All robots at goal positions"
                paused = True

            last_step_time = current_time

        # Render current state
        visualizer.render(coordinator, coordinator.paths, step_count, info_text, selected_robot, paused)
        visualizer.clock.tick(60)  # 60 FPS

    visualizer.cleanup()
    print("\nSimulation ended")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        pygame.quit()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()