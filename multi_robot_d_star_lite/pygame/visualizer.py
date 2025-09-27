import pygame
from typing import Dict, Tuple, List
from .ui_components import ControlPanel
from ..utils.colors import generate_robot_color
from .game_log import GameLog

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

        # Add space for log panel (200 pixels wide on the left) and control panel (200 pixels wide on the right)
        self.log_panel_width = 200
        self.panel_width = 200
        self.total_width = self.log_panel_width + self.width + self.panel_width

        # Grid offset due to log panel
        self.grid_offset_x = self.log_panel_width

        # Mouse drag tracking for draw mode
        self.mouse_dragging = False
        self.last_drag_cell = None

        pygame.init()
        self.screen = pygame.display.set_mode((self.total_width, self.height))  # No extra space for info bar
        pygame.display.set_caption("Multi-Agent D* Lite Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Create game log panel (left side)
        self.game_log = GameLog(0, 0, self.log_panel_width, self.height)

        # Create control panel (right side, offset by log + grid width)
        self.control_panel = ControlPanel(self.log_panel_width + self.width, 0, self.panel_width, self.height)

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
                           (x + self.grid_offset_x, 0), (x + self.grid_offset_x, self.height), 1)
        for y in range(0, self.height, self.cell_size):
            pygame.draw.line(self.screen, self.colors['grid'],
                           (self.grid_offset_x, y), (self.grid_offset_x + self.width, y), 1)

    def draw_cell(self, x: int, y: int, color_name: str, filled: bool = True):
        """Draw a single cell"""
        pixel_x = x * self.cell_size + self.grid_offset_x
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
        pixel_x = x * self.cell_size + self.cell_size // 2 + self.grid_offset_x
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
        points = [(x * self.cell_size + self.cell_size // 2 + self.grid_offset_x,
                  y * self.cell_size + self.cell_size // 2)
                 for x, y in path]

        pygame.draw.lines(self.screen, color, False, points, 3)

        # Draw dots at each waypoint
        for point in points[1:-1]:  # Skip start and end
            pygame.draw.circle(self.screen, color, point, 4)

    def render(self, coordinator=None, paths=None, step_count=0, info_text="", selected_robot=None, paused=False, stuck_robots=None, paused_robots=None):
        """
        Main rendering function.
        Shows current state of the world and robot paths.

        Args:
            paused_robots: Dict of robot_id -> pause_reason for partially paused robots
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
                label_x = goal_pos[0] * self.cell_size + self.cell_size // 4 + self.grid_offset_x
                label_y = goal_pos[1] * self.cell_size + self.cell_size // 4
                self.screen.blit(label, (label_x, label_y))

        # Draw robots
        if stuck_robots is None:
            stuck_robots = []
        if paused_robots is None:
            paused_robots = {}

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
                               (pos[0] * self.cell_size + self.grid_offset_x, pos[1] * self.cell_size,
                                self.cell_size, self.cell_size), 3)
            # If this robot is paused (collision), draw orange/amber border
            elif robot_id in paused_robots:
                # Draw paused indicator (orange/amber border)
                pygame.draw.rect(self.screen, (255, 165, 0),  # Orange color
                               (pos[0] * self.cell_size + self.grid_offset_x, pos[1] * self.cell_size,
                                self.cell_size, self.cell_size), 3)
            # If this robot is stuck, draw red border
            elif robot_id in stuck_robots:
                # Draw stuck indicator (red border)
                pygame.draw.rect(self.screen, (255, 0, 0),
                               (pos[0] * self.cell_size + self.grid_offset_x, pos[1] * self.cell_size,
                                self.cell_size, self.cell_size), 3)

            self.draw_circle(pos[0], pos[1], robot_color)

            # Draw robot ID - extract the digit (0-9) from robotN
            if robot_id.startswith("robot") and len(robot_id) > 5:
                label_text = robot_id[5:]  # Get the number part
            else:
                label_text = '?'
            label = self.font.render(label_text, True, (255, 255, 255))
            label_rect = label.get_rect(center=(
                pos[0] * self.cell_size + self.cell_size // 2 + self.grid_offset_x,
                pos[1] * self.cell_size + self.cell_size // 2
            ))
            self.screen.blit(label, label_rect)

        # No pause overlay - keep grid visible when paused

        # Add step count and current status to game log title or as periodic updates
        # (info_text is now only used for immediate status, logged separately)

        # Draw game log panel
        self.game_log.render(self.screen)

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
            'o': False,  # Obstacle mode toggle
            'mouse_click': None,
            'left_click': None,
            'right_click': None,
            'panel_event': None,
            'mouse_down': None,
            'mouse_up': False,
            'mouse_motion': None,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events['quit'] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    events['space'] = True
                elif event.key == pygame.K_c:
                    events['c'] = True
                elif event.key == pygame.K_o:
                    events['o'] = True
                elif event.key == pygame.K_q:
                    events['quit'] = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle scroll events for game log
                if self.game_log.handle_event(event):
                    continue  # Event was handled by game log

                # Get grid coordinates from mouse position
                mx, my = event.pos

                # Check if click is in control panel area
                if mx >= self.log_panel_width + self.width:  # Click is in control panel area
                    # Handle control panel clicks
                    panel_event = self.control_panel.handle_event(event)
                    if panel_event:
                        events['panel_event'] = panel_event
                elif mx >= self.log_panel_width and mx < self.log_panel_width + self.width and my < self.height:  # Click in grid area
                    # Adjust mouse position for grid offset
                    grid_x = (mx - self.grid_offset_x) // self.cell_size
                    grid_y = my // self.cell_size
                    if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
                        if event.button == 1:  # Left click
                            events['left_click'] = (grid_x, grid_y)
                            events['mouse_click'] = (grid_x, grid_y)  # Keep for compatibility
                            events['mouse_down'] = (grid_x, grid_y)
                            self.mouse_dragging = True
                            self.last_drag_cell = (grid_x, grid_y)
                        elif event.button == 3:  # Right click
                            events['right_click'] = (grid_x, grid_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left button release
                    events['mouse_up'] = True
                    self.mouse_dragging = False
                    self.last_drag_cell = None

            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    mx, my = event.pos
                    if mx >= self.log_panel_width and mx < self.log_panel_width + self.width and my < self.height:
                        grid_x = (mx - self.grid_offset_x) // self.cell_size
                        grid_y = my // self.cell_size
                        if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
                            # Only report motion if we moved to a different cell
                            if (grid_x, grid_y) != self.last_drag_cell:
                                events['mouse_motion'] = (grid_x, grid_y)
                                self.last_drag_cell = (grid_x, grid_y)

        return events

    def add_log_message(self, text: str, msg_type: str = 'info'):
        """Add a message to the game log."""
        self.game_log.add_message(text, msg_type)

    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()