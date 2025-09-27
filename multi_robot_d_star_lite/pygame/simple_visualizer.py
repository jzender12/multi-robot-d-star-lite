#!/usr/bin/env python3
"""
Simple text-based visualizer for debugging pathfinding algorithms.
Provides ASCII visualization of grids, paths, and robot movements.
"""

from colorama import init, Fore, Back, Style
from typing import List, Tuple, Dict, Optional

# Initialize colorama
init(autoreset=True)

class SimpleVisualizer:
    """
    Text-based visualizer for debugging pathfinding.
    """

    @staticmethod
    def print_path(world, path: List[Tuple[int, int]],
                   start: Tuple[int, int] = None,
                   goal: Tuple[int, int] = None,
                   robots: Dict[str, Tuple[int, int]] = None,
                   title: str = "Path Visualization"):
        """
        Print grid with path, start, goal, and robots marked.

        Legend:
        . = empty
        # = obstacle
        S = start
        G = goal
        * = path (not including start/goal)
        R = robot
        1,2 = specific robots
        """
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*40}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{title}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}{Style.RESET_ALL}")

        # Convert path to set for quick lookup
        path_set = set(path) if path else set()

        for y in range(world.height):
            row = ""
            for x in range(world.width):
                cell = '.'
                color = ""

                # Determine what to display in this cell
                if (x, y) in world.static_obstacles:
                    cell = '#'
                    color = Fore.RED
                elif start and (x, y) == start:
                    cell = 'S'
                    color = Fore.GREEN + Style.BRIGHT
                elif goal and (x, y) == goal:
                    cell = 'G'
                    color = Fore.YELLOW + Style.BRIGHT
                elif robots:
                    # Check if any robot is at this position
                    for rid, pos in robots.items():
                        if pos == (x, y):
                            # Use last character of robot ID or 'R'
                            cell = rid[-1] if rid else 'R'
                            color = Fore.CYAN + Style.BRIGHT
                            break
                elif (x, y) in path_set:
                    cell = '*'
                    color = Fore.BLUE

                row += color + cell + Style.RESET_ALL + " "

            print(f"{y:2d} | {row}")

        # Print column numbers
        print("   +" + "-" * (world.width * 2 - 1))
        print("     " + " ".join(str(i) for i in range(world.width)))

        # Print legend
        print(f"\n{Fore.WHITE}Legend:")
        print(f"  {Fore.GREEN + Style.BRIGHT}S{Style.RESET_ALL} = Start")
        print(f"  {Fore.YELLOW + Style.BRIGHT}G{Style.RESET_ALL} = Goal")
        print(f"  {Fore.BLUE}*{Style.RESET_ALL} = Path")
        print(f"  {Fore.RED}#{Style.RESET_ALL} = Obstacle")
        print(f"  {Fore.CYAN + Style.BRIGHT}R/1/2{Style.RESET_ALL} = Robot")

        if path:
            print(f"\n{Fore.WHITE}Path length: {len(path)} cells")
            print(f"Manhattan distance: {abs(start[0]-goal[0]) + abs(start[1]-goal[1])}")

    @staticmethod
    def print_dual_paths(world,
                        path1: List[Tuple[int, int]],
                        path2: List[Tuple[int, int]],
                        robot1_pos: Tuple[int, int],
                        robot2_pos: Tuple[int, int],
                        goal1: Tuple[int, int],
                        goal2: Tuple[int, int],
                        title: str = "Multi-Agent Paths"):
        """
        Print grid with two robot paths for multi-agent scenarios.

        Legend:
        # = obstacle
        1 = robot1 current position
        2 = robot2 current position
        a = path1 only
        b = path2 only
        X = path intersection/conflict
        A = goal1
        B = goal2
        """
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*40}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{title}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}{Style.RESET_ALL}")

        # Convert paths to sets
        path1_set = set(path1) if path1 else set()
        path2_set = set(path2) if path2 else set()
        conflicts = path1_set & path2_set  # Intersection

        for y in range(world.height):
            row = ""
            for x in range(world.width):
                cell = '.'
                color = ""

                # Determine what to display
                if (x, y) in world.static_obstacles:
                    cell = '#'
                    color = Fore.RED
                elif (x, y) == robot1_pos:
                    cell = '1'
                    color = Fore.BLUE + Style.BRIGHT
                elif (x, y) == robot2_pos:
                    cell = '2'
                    color = Fore.MAGENTA + Style.BRIGHT
                elif (x, y) == goal1:
                    cell = 'A'
                    color = Fore.BLUE
                elif (x, y) == goal2:
                    cell = 'B'
                    color = Fore.MAGENTA
                elif (x, y) in conflicts:
                    cell = 'X'
                    color = Fore.YELLOW + Back.RED + Style.BRIGHT
                elif (x, y) in path1_set:
                    cell = 'a'
                    color = Fore.BLUE
                elif (x, y) in path2_set:
                    cell = 'b'
                    color = Fore.MAGENTA

                row += color + cell + Style.RESET_ALL + " "

            print(f"{y:2d} | {row}")

        # Print column numbers
        print("   +" + "-" * (world.width * 2 - 1))
        print("     " + " ".join(str(i) for i in range(world.width)))

        # Print legend
        print(f"\n{Fore.WHITE}Legend:")
        print(f"  {Fore.BLUE + Style.BRIGHT}1{Style.RESET_ALL} = Robot 1 (current)")
        print(f"  {Fore.MAGENTA + Style.BRIGHT}2{Style.RESET_ALL} = Robot 2 (current)")
        print(f"  {Fore.BLUE}A{Style.RESET_ALL} = Goal 1")
        print(f"  {Fore.MAGENTA}B{Style.RESET_ALL} = Goal 2")
        print(f"  {Fore.BLUE}a{Style.RESET_ALL} = Path 1")
        print(f"  {Fore.MAGENTA}b{Style.RESET_ALL} = Path 2")
        print(f"  {Fore.YELLOW + Back.RED + Style.BRIGHT}X{Style.RESET_ALL} = Conflict!")
        print(f"  {Fore.RED}#{Style.RESET_ALL} = Obstacle")

        if path1:
            print(f"\n{Fore.BLUE}Robot 1 path length: {len(path1)}")
        if path2:
            print(f"{Fore.MAGENTA}Robot 2 path length: {len(path2)}")

        if conflicts:
            print(f"\n{Fore.YELLOW + Back.RED}WARNING: {len(conflicts)} conflicts detected!{Style.RESET_ALL}")
            print(f"Conflict positions: {sorted(list(conflicts))}")

    @staticmethod
    def animate_path(world, path: List[Tuple[int, int]],
                    start: Tuple[int, int],
                    goal: Tuple[int, int],
                    delay: float = 0.5):
        """
        Animate a robot moving along a path (requires manual stepping).
        """
        import time
        import os

        print(f"\n{Fore.GREEN}Press Enter to step through path animation...{Style.RESET_ALL}")

        for i, pos in enumerate(path):
            # Clear screen (works on Unix/Linux/Mac)
            os.system('clear' if os.name == 'posix' else 'cls')

            print(f"{Fore.CYAN}Step {i}/{len(path)-1}{Style.RESET_ALL}")

            # Print grid with robot at current position
            SimpleVisualizer.print_path(
                world,
                path[:i+1],  # Show path traveled so far
                start=start,
                goal=goal,
                robots={'robot': pos},
                title=f"Path Animation - Step {i}"
            )

            if i < len(path) - 1:
                input(f"\n{Fore.GREEN}Press Enter for next step...{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.GREEN + Style.BRIGHT}Goal reached!{Style.RESET_ALL}")

    @staticmethod
    def print_comparison(world, algorithms: Dict[str, List[Tuple[int, int]]],
                        start: Tuple[int, int],
                        goal: Tuple[int, int]):
        """
        Compare paths from different algorithms side by side.
        """
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*40}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Algorithm Comparison")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}{Style.RESET_ALL}")

        for name, path in algorithms.items():
            print(f"\n{Fore.YELLOW}{name}:{Style.RESET_ALL}")
            if path:
                print(f"  Path length: {len(path)}")
                print(f"  Path: {path[:3]}...{path[-2:] if len(path) > 5 else path[3:]}")
            else:
                print(f"  {Fore.RED}No path found{Style.RESET_ALL}")

        # Show all paths on one grid with different markers
        print(f"\n{Fore.WHITE}Combined visualization:")
        markers = ['1', '2', '3', '4', '5']
        colors = [Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.GREEN, Fore.YELLOW]

        for y in range(world.height):
            row = ""
            for x in range(world.width):
                cell = '.'
                color = ""

                if (x, y) in world.static_obstacles:
                    cell = '#'
                    color = Fore.RED
                elif (x, y) == start:
                    cell = 'S'
                    color = Fore.GREEN + Style.BRIGHT
                elif (x, y) == goal:
                    cell = 'G'
                    color = Fore.YELLOW + Style.BRIGHT
                else:
                    # Check which algorithms' paths include this cell
                    for i, (name, path) in enumerate(algorithms.items()):
                        if path and (x, y) in path:
                            cell = markers[i % len(markers)]
                            color = colors[i % len(colors)]
                            break

                row += color + cell + Style.RESET_ALL + " "

            print(f"{y:2d} | {row}")

        print("   +" + "-" * (world.width * 2 - 1))
        print("     " + " ".join(str(i) for i in range(world.width)))

        # Legend for algorithms
        print(f"\n{Fore.WHITE}Algorithm markers:")
        for i, name in enumerate(algorithms.keys()):
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            print(f"  {color}{marker}{Style.RESET_ALL} = {name}")


def demo():
    """
    Demo of the simple visualizer capabilities.
    """
    from world import GridWorld

    print(f"{Fore.CYAN}{Style.BRIGHT}Simple Visualizer Demo{Style.RESET_ALL}")

    # Create a world with obstacles
    world = GridWorld(10, 10)

    # Add some obstacles
    for x, y in [(3, 3), (3, 4), (3, 5), (6, 2), (6, 3), (6, 4)]:
        world.add_obstacle(x, y)

    # Demo single path
    demo_path = [(1, 1), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
                 (3, 6), (4, 6), (5, 6), (6, 6), (7, 6), (8, 7), (8, 8)]

    SimpleVisualizer.print_path(
        world, demo_path,
        start=(1, 1),
        goal=(8, 8),
        title="Single Robot Path Demo"
    )

    # Demo multi-agent paths
    path1 = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1)]
    path2 = [(8, 1), (7, 1), (6, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1)]

    SimpleVisualizer.print_dual_paths(
        world,
        path1, path2,
        robot1_pos=(1, 1),
        robot2_pos=(8, 1),
        goal1=(8, 1),
        goal2=(1, 1),
        title="Multi-Agent Conflict Demo"
    )


if __name__ == "__main__":
    demo()