#!/usr/bin/env python3
"""
Export current grid state to visual test case format.
"""

from ..world import GridWorld
from ..coordinator import MultiAgentCoordinator
from typing import Tuple


def export_to_visual_format(world: GridWorld, coordinator: MultiAgentCoordinator) -> str:
    """
    Export current grid state to visual test case format.

    Returns:
        String representation of grid in visual format
    """
    width = world.width
    height = world.height

    # Build grid representation
    lines = []
    lines.append(f"# Exported grid state")
    lines.append(f"TEST_EXPORTED")
    lines.append(f"{width}x{height}")

    # Create grid with all elements
    for y in range(height):
        row = []
        for x in range(width):
            cell = "."  # Default empty

            # Check for obstacles
            if (x, y) in world.static_obstacles:
                cell = "X"

            # Check for robots and goals
            for robot_id, pos in coordinator.current_positions.items():
                if pos == (x, y):
                    if robot_id == "robot1":
                        cell = "1" if cell == "." else cell + "1"
                    elif robot_id == "robot2":
                        cell = "2" if cell == "." else cell + "2"

            for robot_id, goal in coordinator.goals.items():
                if goal == (x, y):
                    if robot_id == "robot1":
                        cell = "A" if cell == "." else cell + "A"
                    elif robot_id == "robot2":
                        cell = "B" if cell == "." else cell + "B"

            row.append(cell)

        lines.append(" ".join(row))

    # Add robot info as comments
    lines.append("")
    lines.append("# Robot positions and goals:")
    for robot_id in sorted(coordinator.current_positions.keys()):
        pos = coordinator.current_positions[robot_id]
        goal = coordinator.goals.get(robot_id, "None")
        lines.append(f"# {robot_id}: {pos} -> {goal}")

    return "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Try using pyperclip if available
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass

    # Try using tkinter
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except:
        pass

    # Try using xclip on Linux
    try:
        import subprocess
        process = subprocess.Popen(['xclip', '-selection', 'clipboard'],
                                 stdin=subprocess.PIPE, close_fds=True)
        process.communicate(input=text.encode('utf-8'))
        return True
    except:
        pass

    # Try using pbcopy on Mac
    try:
        import subprocess
        process = subprocess.Popen(['pbcopy'],
                                 stdin=subprocess.PIPE, close_fds=True)
        process.communicate(input=text.encode('utf-8'))
        return True
    except:
        pass

    # Try using clip on Windows
    try:
        import subprocess
        process = subprocess.Popen(['clip'],
                                 stdin=subprocess.PIPE, close_fds=True)
        process.communicate(input=text.encode('utf-8'))
        return True
    except:
        pass

    return False


if __name__ == "__main__":
    # Test export
    from parse_test_grid import setup_from_visual

    test_grid = """5x5
1 . . . A
. . . . .
. . X . .
. . . . .
B . . . 2"""

    world, coordinator = setup_from_visual(test_grid)

    exported = export_to_visual_format(world, coordinator)
    print(exported)

    if copy_to_clipboard(exported):
        print("\n✓ Copied to clipboard!")
    else:
        print("\n✗ Could not copy to clipboard")