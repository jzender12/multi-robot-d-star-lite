import pygame
from typing import Dict, Tuple, List

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

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height + 50))  # Extra space for info
        pygame.display.set_caption("Multi-Agent D* Lite Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

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
                    path_color = f"path{robot_id[-1]}"  # Extract number from robot ID
                    self.draw_path(path, path_color)

        # Draw goals
        if coordinator:
            for robot_id, goal_pos in coordinator.goals.items():
                goal_color = f"goal{robot_id[-1]}"
                self.draw_cell(goal_pos[0], goal_pos[1], goal_color, filled=False)

                # Draw 'G' label
                label = self.font.render(f'G{robot_id[-1]}', True, self.colors[goal_color])
                label_x = goal_pos[0] * self.cell_size + self.cell_size // 4
                label_y = goal_pos[1] * self.cell_size + self.cell_size // 4
                self.screen.blit(label, (label_x, label_y))

        # Draw robots
        for robot_id, pos in self.world.robot_positions.items():
            robot_color = f"robot{robot_id[-1]}"

            # If this robot is selected, draw a highlight
            if selected_robot == robot_id:
                # Draw selection highlight (yellow border)
                pygame.draw.rect(self.screen, (255, 255, 0),
                               (pos[0] * self.cell_size, pos[1] * self.cell_size,
                                self.cell_size, self.cell_size), 3)

            self.draw_circle(pos[0], pos[1], robot_color)

            # Draw robot ID
            label = self.font.render(robot_id[-1], True, (255, 255, 255))
            label_rect = label.get_rect(center=(
                pos[0] * self.cell_size + self.cell_size // 2,
                pos[1] * self.cell_size + self.cell_size // 2
            ))
            self.screen.blit(label, label_rect)

        # Draw pause overlay
        if paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(50)  # Transparency
            overlay.fill((100, 100, 100))
            self.screen.blit(overlay, (0, 0))

            # Large PAUSED text in center
            big_font = pygame.font.Font(None, 72)
            paused_label = big_font.render("PAUSED", True, (255, 255, 0))
            paused_rect = paused_label.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(paused_label, paused_rect)

        # Draw info bar at bottom
        info_surface = pygame.Surface((self.width, 50))
        info_surface.fill((240, 240, 240))

        # Step counter
        step_text = self.font.render(f"Step: {step_count}", True, (0, 0, 0))
        info_surface.blit(step_text, (10, 10))

        # Show PAUSED prominently if paused
        if paused:
            paused_text = self.font.render("PAUSED", True, (255, 0, 0))
            info_surface.blit(paused_text, (self.width - 100, 10))

        # Info text
        if info_text:
            info = self.small_font.render(info_text, True, (100, 100, 100))
            info_surface.blit(info, (150, 15))

        # Controls hint
        controls = self.small_font.render("P: Pause | When paused: Click robot → Click to set goal | Q: Quit",
                                         True, (100, 100, 100))
        info_surface.blit(controls, (10, 30))

        self.screen.blit(info_surface, (0, self.height))

        pygame.display.flip()

    def handle_events(self) -> Dict:
        """
        Handle pygame events.
        Returns dict with event info.
        """
        events = {
            'quit': False,
            'space': False,
            'r': False,
            'p': False,
            'c': False,
            'mouse_click': None,
            'left_click': None,
            'right_click': None,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events['quit'] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    events['space'] = True
                elif event.key == pygame.K_r:
                    events['r'] = True
                elif event.key == pygame.K_p:
                    events['p'] = True
                elif event.key == pygame.K_c:
                    events['c'] = True
                elif event.key == pygame.K_q:
                    events['quit'] = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Get grid coordinates from mouse position
                mx, my = event.pos
                if my < self.height:  # Only if clicking in grid area
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