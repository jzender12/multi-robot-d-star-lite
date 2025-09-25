import pygame
from typing import Dict, Tuple, List
from .ui_components import ControlPanel
from .utils.colors import generate_robot_color

class GridVisualizer:
    """
    Simple pygame visualization for the multi-agent pathfinding demo.
    Shows grid, obstacles, robots, goals, and planned paths.
    """

    def __init__(self, world, cell_size: int = 50):
        self.world = world
        self.cell_size = cell_size
        self.width = world.width * cell_size
        self.height = world.height * cell_size

        # Add space for control panel (200 pixels wide on the right)
        self.panel_width = 200
        self.total_width = self.width + self.panel_width

        pygame.init()
        self.screen = pygame.display.set_mode((self.total_width, self.height + 50))  # Extra space for info
        pygame.display.set_caption("Multi-Agent D* Lite Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Create control panel
        self.control_panel = ControlPanel(self.width, 0, self.panel_width, self.height + 50)

        # Colors (RGB values)
        self.colors = {
            'background': (255, 255, 255),
            'grid': (200, 200, 200),
            'obstacle': (50, 50, 50),
            'robot1': (0, 100, 200),  # Blue
            'robot2': (200, 50, 0),   # Red
            'goal1': (100, 150, 250),  # Light blue
            'goal2': (250, 150, 100),  # Light red
            'path1': (150, 200, 255),  # Very light blue
            'path2': (255, 200, 150),  # Very light red
            'dynamic_obstacle': (100, 100, 100),  # Gray for dynamic obstacles
        }

    def draw_grid(self):
        """Draw grid lines"""
        for x in range(0, self.width, self.cell_size):
            pygame.draw.line(self.screen, self.colors['grid'],
                           (x, 0), (x, self.height), 1)
        for y in range(0, self.height, self.cell_size):
            pygame.draw.line(self.screen, self.colors['grid'],
                           (0, y), (self.width, y), 1)

    def draw_cell(self, x: int, y: int, color_name: str, filled: bool = True):
        """Draw a single cell"""
        pixel_x = x * self.cell_size
        pixel_y = y * self.cell_size
        color = self.colors.get(color_name, (100, 100, 100))

        if filled:
            pygame.draw.rect(self.screen, color,
                           (pixel_x + 2, pixel_y + 2,
                            self.cell_size - 4, self.cell_size - 4))
        else:
            pygame.draw.rect(self.screen, color,
                           (pixel_x + 2, pixel_y + 2,
                            self.cell_size - 4, self.cell_size - 4), 2)

    def draw_circle(self, x: int, y: int, color_name: str, radius_factor: float = 0.3):
        """Draw a circle in a cell (for robots)"""
        pixel_x = x * self.cell_size + self.cell_size // 2
        pixel_y = y * self.cell_size + self.cell_size // 2
        radius = int(self.cell_size * radius_factor)
        color = self.colors.get(color_name, (100, 100, 100))

        pygame.draw.circle(self.screen, color, (pixel_x, pixel_y), radius)

        # Add white border for visibility
        pygame.draw.circle(self.screen, (255, 255, 255), (pixel_x, pixel_y), radius, 2)

    def draw_path(self, path: List[Tuple[int, int]], color_name: str):
        """Draw a path as connected lines"""
        if len(path) < 2:
            return

        color = self.colors.get(color_name, (100, 100, 100))
        points = [(x * self.cell_size + self.cell_size // 2,
                  y * self.cell_size + self.cell_size // 2)
                 for x, y in path]

        pygame.draw.lines(self.screen, color, False, points, 3)

        # Draw dots at each waypoint
        for point in points[1:-1]:  # Skip start and end
            pygame.draw.circle(self.screen, color, point, 4)

    def render(self, coordinator=None, paths=None, step_count=0, info_text="", selected_robot=None, paused=False):
        """
        Main rendering function.
        Shows current state of the world and robot paths.
        """
        # Clear screen
        self.screen.fill(self.colors['background'])

        # Draw grid
        self.draw_grid()

        # Draw obstacles
        for x, y in self.world.static_obstacles:
            self.draw_cell(x, y, 'obstacle')

        # Draw paths if provided
        if paths:
            for robot_id, path in paths.items():
                if path and len(path) > 1:
                    # Use even lighter version of robot color for path
                    color = generate_robot_color(robot_id)
                    r, g, b = color
                    path_color_rgb = (min(255, r + 100), min(255, g + 100), min(255, b + 100))
                    path_color_key = f"path_{robot_id}"
                    if path_color_key not in self.colors:
                        self.colors[path_color_key] = path_color_rgb
                    path_color = path_color_key

                    self.draw_path(path, path_color)

        # Draw goals
        if coordinator:
            for robot_id, goal_pos in coordinator.goals.items():
                # Use lighter version of robot color for goal
                color = generate_robot_color(robot_id)
                r, g, b = color
                goal_color_rgb = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
                goal_color_key = f"goal_{robot_id}"
                if goal_color_key not in self.colors:
                    self.colors[goal_color_key] = goal_color_rgb
                goal_color = goal_color_key

                self.draw_cell(goal_pos[0], goal_pos[1], goal_color, filled=False)

                # Draw 'G' label with robot number (G0-G9)
                if robot_id.startswith("robot") and len(robot_id) > 5:
                    goal_num = robot_id[5:]  # Get the number part
                else:
                    goal_num = "?"
                label = self.font.render(f'G{goal_num}', True, self.colors[goal_color])
                label_x = goal_pos[0] * self.cell_size + self.cell_size // 4
                label_y = goal_pos[1] * self.cell_size + self.cell_size // 4
                self.screen.blit(label, (label_x, label_y))

        # Draw robots
        for robot_id, pos in self.world.robot_positions.items():
            # Get color dynamically for all robots
            color = generate_robot_color(robot_id)
            if robot_id not in self.colors:
                self.colors[robot_id] = color
            robot_color = robot_id

            # If this robot is selected, draw a highlight
            if selected_robot == robot_id:
                # Draw selection highlight (yellow border)
                pygame.draw.rect(self.screen, (255, 255, 0),
                               (pos[0] * self.cell_size, pos[1] * self.cell_size,
                                self.cell_size, self.cell_size), 3)

            self.draw_circle(pos[0], pos[1], robot_color)

            # Draw robot ID - extract the digit (0-9) from robotN
            if robot_id.startswith("robot") and len(robot_id) > 5:
                label_text = robot_id[5:]  # Get the number part
            else:
                label_text = '?'
            label = self.font.render(label_text, True, (255, 255, 255))
            label_rect = label.get_rect(center=(
                pos[0] * self.cell_size + self.cell_size // 2,
                pos[1] * self.cell_size + self.cell_size // 2
            ))
            self.screen.blit(label, label_rect)

        # No pause overlay - keep grid visible when paused

        # Draw info bar at bottom (extend across full width)
        info_surface = pygame.Surface((self.total_width, 50))
        info_surface.fill((240, 240, 240))

        # Step counter
        step_text = self.font.render(f"Step: {step_count}", True, (0, 0, 0))
        info_surface.blit(step_text, (10, 10))

        # Info text
        if info_text:
            info = self.small_font.render(info_text, True, (100, 100, 100))
            info_surface.blit(info, (150, 15))

        # Controls hint
        controls = self.small_font.render("SPACE: Pause | When paused: Click robot → Click to set goal | Q: Quit",
                                         True, (100, 100, 100))
        info_surface.blit(controls, (10, 30))

        self.screen.blit(info_surface, (0, self.height))

        # Draw control panel
        self.control_panel.draw(self.screen)

        pygame.display.flip()

    def handle_events(self) -> Dict:
        """
        Handle pygame events.
        Returns dict with event info.
        """
        events = {
            'quit': False,
            'space': False,
            'c': False,
            'mouse_click': None,
            'left_click': None,
            'right_click': None,
            'panel_event': None,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events['quit'] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    events['space'] = True
                elif event.key == pygame.K_c:
                    events['c'] = True
                elif event.key == pygame.K_q:
                    events['quit'] = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Get grid coordinates from mouse position
                mx, my = event.pos

                # Check if click is in control panel area
                if mx >= self.width:  # Click is in panel area
                    # Handle control panel clicks
                    panel_event = self.control_panel.handle_event(event)
                    if panel_event:
                        events['panel_event'] = panel_event
                elif my < self.height:  # Only if clicking in grid area
                    grid_x = mx // self.cell_size
                    grid_y = my // self.cell_size
                    if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
                        if event.button == 1:  # Left click
                            events['left_click'] = (grid_x, grid_y)
                            events['mouse_click'] = (grid_x, grid_y)  # Keep for compatibility
                        elif event.button == 3:  # Right click
                            events['right_click'] = (grid_x, grid_y)

        return events

    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()