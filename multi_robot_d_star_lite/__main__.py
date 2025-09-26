#!/usr/bin/env python3
"""
Main demonstration of Multi-Agent D* Lite pathfinding.
Two robots navigate a 10x10 grid, avoiding obstacles and each other.
This allows the package to be run as a module: python -m multi_robot_d_star_lite
"""

import pygame
import time
from .world import GridWorld
from .coordinator import MultiAgentCoordinator
from .visualizer import GridVisualizer
from .utils.export_grid import export_to_visual_format, copy_to_clipboard

def main():
    """
    Main function to run the multi-agent D* Lite demonstration.
    Creates a 10x10 grid with 2 robots navigating around obstacles.
    """

    # Create clean 10x10 world - no obstacles initially
    print("Initializing 10x10 grid world (clean slate)...")
    world = GridWorld(10, 10)

    # Create coordinator
    print("Initializing multi-agent coordinator...")
    coordinator = MultiAgentCoordinator(world)

    # Add only robot0 initially at top-left, goal at bottom-right
    # Users will add more robots and obstacles interactively
    coordinator.add_robot("robot0", start=(0, 0), goal=(9, 9))

    # Initial path computation
    print("Computing initial paths...")
    coordinator.recompute_paths()

    # Create visualizer
    visualizer = GridVisualizer(world)
    visualizer.control_panel.update_robot_count(len(coordinator.planners))
    visualizer.control_panel.set_paused(True)  # Start paused

    # Add initial messages to game log
    visualizer.add_log_message("Multi-Agent D* Lite Demo started", "success")
    visualizer.add_log_message("Grid: 10x10, Robot0 at (0,0) → (9,9)", "info")
    visualizer.add_log_message("Controls: SPACE=Pause, Click=Obstacles/Goals", "info")

    # Run simulation
    print("\n" + "="*50)
    print("MULTI-AGENT D* LITE DEMO")
    print("="*50)
    print("\nControls:")
    print("  SPACE - Pause/Resume")
    print("  C     - Copy current setup to clipboard (when paused)")
    print("  Click - Add/remove obstacle")
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
    info_text = "PAUSED - Press SPACE to start. Click to add obstacles or robots."
    selected_robot = None  # For goal setting

    while running:
        # Handle events
        events = visualizer.handle_events()

        if events['quit']:
            running = False

        elif events['space']:
            # Pause/unpause with SPACE key
            paused = not paused
            selected_robot = None  # Clear any selection when toggling pause
            visualizer.control_panel.set_paused(paused)  # Update control panel
            if paused:
                info_text = "PAUSED - Click robot to select, then click to set goal"
                visualizer.add_log_message("Simulation paused", "warning")
            else:
                info_text = "Running - Robots navigating using D* Lite"
                visualizer.add_log_message("Simulation resumed", "success")
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

        elif events.get('panel_event'):
            # Handle control panel events
            action = events['panel_event']

            if action == "Add Robot":
                # Find a free position for the new robot
                free_positions = []
                for x in range(world.width):
                    for y in range(world.height):
                        if world.is_free(x, y) and (x, y) not in coordinator.current_positions.values():
                            free_positions.append((x, y))

                if len(free_positions) >= 2:  # Need at least 2 free positions (start and goal)
                    import random
                    start_pos = random.choice(free_positions)
                    free_positions.remove(start_pos)
                    goal_pos = random.choice(free_positions)

                    robot_id = coordinator.get_next_robot_id()
                    if robot_id is None:
                        info_text = "Maximum of 10 robots reached"
                    else:
                        success = coordinator.add_robot(robot_id, start=start_pos, goal=goal_pos)
                        if success:
                            coordinator.recompute_paths()
                            info_text = f"Added {robot_id} at {start_pos} with goal {goal_pos}"
                            visualizer.add_log_message(f"Added {robot_id} at {start_pos} → {goal_pos}", "success")
                            visualizer.control_panel.update_robot_count(len(coordinator.planners))
                            # Disable Add Robot button if we've reached 10 robots
                            if len(coordinator.planners) >= 10:
                                visualizer.control_panel.buttons["Add Robot"].enabled = False
                        else:
                            info_text = f"Failed to add {robot_id}"
                            visualizer.add_log_message(f"Failed to add {robot_id}", "error")
                else:
                    info_text = "Not enough free space for a new robot"

            elif action == "Remove Robot":
                # Remove the selected robot, or the last one if none selected
                robot_to_remove = selected_robot
                if not robot_to_remove and len(coordinator.planners) > 0:
                    # Get the highest numbered robot
                    robots = list(coordinator.planners.keys())
                    robots.sort(key=lambda r: int(r[5:]) if r.startswith("robot") and r[5:].isdigit() else 0)
                    robot_to_remove = robots[-1] if robots else None

                if robot_to_remove and robot_to_remove != "robot0":  # Keep robot0
                    success = coordinator.remove_robot(robot_to_remove)
                    if success:
                        info_text = f"Removed {robot_to_remove}"
                        visualizer.add_log_message(f"Removed {robot_to_remove}", "info")
                        selected_robot = None
                        visualizer.control_panel.update_robot_count(len(coordinator.planners))
                        # Re-enable Add Robot button if we're below 10 robots
                        if len(coordinator.planners) < 10:
                            visualizer.control_panel.buttons["Add Robot"].enabled = True
                    else:
                        info_text = f"Failed to remove {robot_to_remove}"
                        visualizer.add_log_message(f"Failed to remove {robot_to_remove}", "error")
                else:
                    info_text = "Cannot remove robot0 (minimum 1 robot required)"

            elif action in ["10x10", "15x15", "20x20"]:
                # Resize the arena
                size = int(action.split('x')[0])
                coordinator.resize_world(size, size)

                # Recreate visualizer with new world size
                visualizer.cleanup()
                visualizer = GridVisualizer(world)
                visualizer.control_panel.update_robot_count(len(coordinator.planners))

                info_text = f"Resized arena to {action} - Clean slate with robot0"
                paused = True  # Pause after resize
                visualizer.control_panel.set_paused(paused)

            elif action == "Reset":
                # Reset - clear obstacles and reset robots, keep current size
                # Clear all obstacles
                world.static_obstacles.clear()
                world.grid.fill(0)

                # Clear all robots except robot0
                coordinator.clear_all_robots()

                # Add robot0 back at (0,0) with goal at bottom-right
                coordinator.add_robot("robot0",
                                     start=(0, 0),
                                     goal=(world.width - 1, world.height - 1))

                # Recompute paths
                coordinator.recompute_paths()

                # Update UI
                visualizer.control_panel.update_robot_count(len(coordinator.planners))
                visualizer.control_panel.buttons["Add Robot"].enabled = True  # Re-enable since we're back to 1 robot

                info_text = f"Reset grid - cleared obstacles and robots"
                paused = True
                visualizer.control_panel.set_paused(paused)

            elif action == "Speed-":
                visualizer.control_panel.decrease_speed()
                sim_speed = visualizer.control_panel.speed
                info_text = f"Speed: {sim_speed:.1f}/s"

            elif action == "Speed+":
                visualizer.control_panel.increase_speed()
                sim_speed = visualizer.control_panel.speed
                info_text = f"Speed: {sim_speed:.1f}/s"

            elif action == "Pause/Play":
                # Toggle pause state
                paused = not paused
                visualizer.control_panel.set_paused(paused)
                selected_robot = None  # Clear any selection when toggling pause
                if paused:
                    info_text = "PAUSED - Click robot to select, then click to set goal"
                else:
                    info_text = "Running - Robots navigating using D* Lite"
                print("PAUSED" if paused else "RESUMED")

        elif events['left_click']:
            x, y = events['left_click']

            if paused and selected_robot:
                # We're in goal-setting mode
                # Check if clicked position is valid for a goal
                if not ((x, y) in world.static_obstacles):
                    # Try to set new goal (coordinator will validate)
                    success = coordinator.set_new_goal(selected_robot, (x, y))
                    if success:
                        info_text = f"New goal set for {selected_robot} at ({x}, {y}) - Press SPACE to resume"
                        visualizer.add_log_message(f"{selected_robot} goal changed to ({x}, {y})", "info")
                        selected_robot = None  # Clear selection
                    else:
                        info_text = "Cannot place goal there (obstacle or another robot's goal)"
                        visualizer.add_log_message("Invalid goal location", "error")
                else:
                    info_text = "Cannot place goal on obstacle"

            elif paused:
                # Check if we clicked on a robot
                robot = coordinator.get_robot_at_position((x, y))
                if robot:
                    selected_robot = robot
                    algorithm = coordinator.robot_algorithms.get(robot, "Unknown")
                    info_text = f"Selected {robot} ({algorithm}) - Click to set new goal"
                else:
                    # Not on a robot, toggle obstacle
                    # Check if position is a goal or robot
                    is_goal_pos = any(goal == (x, y) for goal in coordinator.goals.values())
                    is_robot_pos = any(pos == (x, y) for pos in coordinator.current_positions.values())

                    if (x, y) in world.static_obstacles:
                        world.remove_obstacle(x, y)
                        info_text = f"Removed obstacle at ({x}, {y})"
                        # Pass the changed cell so D* Lite can update properly
                        coordinator.recompute_paths(changed_cells={(x, y)})
                    elif is_goal_pos:
                        info_text = "Cannot place obstacle on a goal"
                    elif is_robot_pos:
                        info_text = "Cannot place obstacle on a robot"
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

                if (x, y) in world.static_obstacles:
                    world.remove_obstacle(x, y)
                    info_text = f"Removed obstacle at ({x}, {y})"
                    visualizer.add_log_message(f"Removed obstacle at ({x}, {y})", "info")
                    # Pass the changed cell so D* Lite can update properly
                    coordinator.recompute_paths(changed_cells={(x, y)})
                elif is_robot_pos:
                    info_text = "Cannot place obstacle on a robot"
                elif is_goal_pos:
                    info_text = "Cannot place obstacle on a goal"
                else:
                    world.add_obstacle(x, y)
                    info_text = f"Added obstacle at ({x}, {y})"
                    visualizer.add_log_message(f"Added obstacle at ({x}, {y})", "info")
                    # Pass the changed cell so D* Lite can update properly
                    coordinator.recompute_paths(changed_cells={(x, y)})

        # Step simulation at controlled rate
        current_time = time.time()
        if not paused and current_time - last_step_time > 1.0 / sim_speed:
            # Move robots one step
            should_continue, collision, stuck_robots = coordinator.step_simulation()

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
                visualizer.add_log_message(f"COLLISION: {robot1} and {robot2} ({collision_type})", "collision")
                paused = True
                visualizer.control_panel.set_paused(paused)  # Sync UI state
            elif stuck_robots:
                # Some robots are stuck but simulation continues
                step_count += 1

                # Create informative message about stuck robots
                if len(stuck_robots) == 1:
                    info_text = f"{stuck_robots[0]} stuck - no path to goal"
                    visualizer.add_log_message(f"{stuck_robots[0]} stuck - no path to goal", "warning")
                else:
                    info_text = f"{len(stuck_robots)} robots stuck - no paths to goals"
                    visualizer.add_log_message(f"{len(stuck_robots)} robots stuck: {', '.join(stuck_robots)}", "warning")

                # Don't pause, just inform user
                print(f"⚠ Stuck robots: {', '.join(stuck_robots)}")
            elif should_continue:
                step_count += 1

                # Normal movement, no stuck robots
                info_text = "Running - Robots navigating using D* Lite"

                # Check if all robots reached their goals
                all_at_goal = all(
                    coordinator.current_positions[rid] == coordinator.goals[rid]
                    for rid in coordinator.planners.keys()
                )

                if all_at_goal:
                    info_text = "SUCCESS! All robots reached their goals!"
                    print(info_text)
                    visualizer.add_log_message("All robots reached their goals!", "success")
                    paused = True
                    visualizer.control_panel.set_paused(paused)  # Sync UI state
            else:
                # should_continue is False and no stuck robots means all at goal
                info_text = "All robots at goal positions"
                paused = True
                visualizer.control_panel.set_paused(paused)  # Sync UI state

            last_step_time = current_time

        # Render current state (pass stuck_robots if available)
        stuck_robots_to_display = stuck_robots if not paused and 'stuck_robots' in locals() else []
        visualizer.render(coordinator, coordinator.paths, step_count, info_text, selected_robot, paused, stuck_robots_to_display)
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