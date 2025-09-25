#!/usr/bin/env python3
"""
UI components for the control panel.
Provides Button and ControlPanel classes for interactive controls.
"""

import pygame
from typing import Callable, Optional, Dict, List, Tuple


class Button:
    """
    Interactive button UI component.
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, callback: Callable):
        """
        Create a button.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            text: Button label
            callback: Function to call when clicked
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.enabled = True
        self.hovered = False
        self.selected = False  # For toggle buttons

        # Colors
        self.normal_color = (200, 200, 200)
        self.hover_color = (220, 220, 220)
        self.disabled_color = (150, 150, 150)
        self.text_color = (50, 50, 50)
        self.disabled_text_color = (100, 100, 100)

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """
        Handle mouse click.

        Args:
            pos: Mouse position (x, y)

        Returns:
            True if button was clicked
        """
        if not self.enabled:
            return False

        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False

    def update_hover(self, pos: Tuple[int, int]):
        """
        Update hover state based on mouse position.

        Args:
            pos: Mouse position (x, y)
        """
        self.hovered = self.rect.collidepoint(pos)

    def draw(self, screen: pygame.Surface):
        """
        Draw the button.

        Args:
            screen: Pygame surface to draw on
        """
        # Choose color based on state
        if not self.enabled:
            color = self.disabled_color
            text_color = self.disabled_text_color
        elif self.hovered:
            color = self.hover_color
            text_color = self.text_color
        else:
            color = self.normal_color
            text_color = self.text_color

        # Draw button rectangle
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)  # Border

        # Draw text
        font = pygame.font.Font(None, 20)
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class ButtonGroup:
    """
    Group of buttons with exclusive selection.
    """

    def __init__(self):
        self.buttons: List[Button] = []

    def add(self, button: Button):
        """Add button to group."""
        self.buttons.append(button)

    def select(self, button: Button):
        """Select a button, deselecting others."""
        for b in self.buttons:
            b.selected = (b == button)


class ControlPanel:
    """
    Control panel with buttons for robot and arena management.
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 on_add_robot: Optional[Callable] = None,
                 on_remove_robot: Optional[Callable] = None,
                 on_resize: Optional[Callable] = None,
                 on_reset: Optional[Callable] = None,
                 on_pause_play: Optional[Callable] = None):
        """
        Create control panel.

        Args:
            x: Panel X position
            y: Panel Y position
            width: Panel width
            height: Panel height
            on_add_robot: Callback for Add Robot button
            on_remove_robot: Callback for Remove Robot button
            on_resize: Callback for resize buttons (receives size tuple)
            on_reset: Callback for Reset button
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.buttons: Dict[str, Button] = {}
        self.labels: Dict[str, str] = {}

        # State
        self.robot_count = 0
        self.speed = 2.0  # Steps per second
        self.paused = True  # Start paused

        # Background color
        self.bg_color = (240, 240, 240)

        # Create buttons
        button_y = y + 20
        button_x = x + 20
        button_width = width - 40
        button_height = 30
        spacing = 40

        # Robot management buttons
        self.buttons["Add Robot"] = Button(
            button_x, button_y, button_width, button_height,
            "Add Robot",
            on_add_robot or (lambda: None)
        )
        button_y += spacing

        self.buttons["Remove Robot"] = Button(
            button_x, button_y, button_width, button_height,
            "Remove Robot",
            on_remove_robot or (lambda: None)
        )
        button_y += spacing * 2  # Extra space

        # Arena size buttons (removed 5x5 as it's too small)
        size_button_width = (button_width - 20) // 3
        for i, size in enumerate(["10x10", "15x15", "20x20"]):
            bx = button_x + i * (size_button_width + 10)
            by = button_y

            dims = int(size.split('x')[0])
            self.buttons[size] = Button(
                bx, int(by), size_button_width, button_height,
                size,
                (lambda d=dims: on_resize((d, d))) if on_resize else (lambda: None)
            )

        button_y += spacing * 1.5

        # Labels section - Initialize both labels
        self.labels["Robots"] = f"Robots: {self.robot_count}"
        self.labels["Speed"] = f"Speed: {self.speed:.1f}/s"
        button_y += spacing

        # Speed up/down buttons
        speed_button_width = (button_width - 10) // 2
        # Store the y position of speed buttons for label placement
        self.speed_buttons_y = button_y
        self.buttons["Speed-"] = Button(
            button_x, int(button_y), speed_button_width, button_height,
            "Speed -",
            lambda: self.decrease_speed()
        )
        self.buttons["Speed+"] = Button(
            button_x + speed_button_width + 10, int(button_y), speed_button_width, button_height,
            "Speed +",
            lambda: self.increase_speed()
        )
        button_y += spacing

        # Reset button
        button_y += spacing
        self.buttons["Reset"] = Button(
            button_x, int(button_y), button_width, button_height,
            "Reset",
            on_reset or (lambda: None)
        )
        button_y += spacing

        # Pause/Play button
        self.pause_button_y = button_y
        self.buttons["Pause/Play"] = Button(
            button_x, int(button_y), button_width, button_height,
            "⏸ Pause" if not self.paused else "▶ Play",
            on_pause_play or (lambda: None)
        )

    def get_button(self, name: str) -> Optional[Button]:
        """Get button by name."""
        return self.buttons.get(name)

    def get_label(self, name: str) -> Optional[str]:
        """Get label by name."""
        return self.labels.get(name)

    def update_robot_count(self, count: int):
        """Update displayed robot count."""
        self.robot_count = count
        self.labels["Robots"] = f"Robots: {count}"

    def increase_speed(self):
        """Increase simulation speed."""
        self.speed = min(10.0, self.speed + 0.5)
        self.labels["Speed"] = f"Speed: {self.speed:.1f}/s"

    def decrease_speed(self):
        """Decrease simulation speed."""
        self.speed = max(0.5, self.speed - 0.5)
        self.labels["Speed"] = f"Speed: {self.speed:.1f}/s"

    def set_paused(self, paused: bool):
        """Update pause state and button text."""
        self.paused = paused
        if "Pause/Play" in self.buttons:
            self.buttons["Pause/Play"].text = "⏸ Pause" if not paused else "▶ Play"

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle pygame event.

        Args:
            event: Pygame event

        Returns:
            Action string or None
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                for name, button in self.buttons.items():
                    if button.handle_click(event.pos):
                        return name

        elif event.type == pygame.MOUSEMOTION:
            for button in self.buttons.values():
                button.update_hover(event.pos)

        return None

    def draw(self, screen: pygame.Surface):
        """
        Draw the control panel.

        Args:
            screen: Pygame surface to draw on
        """
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)  # Border

        # Draw title
        font = pygame.font.Font(None, 24)
        title = font.render("Control Panel", True, (50, 50, 50))
        title_rect = title.get_rect(centerx=self.rect.centerx, y=self.rect.y + 5)
        screen.blit(title, title_rect)

        # Draw buttons
        for button in self.buttons.values():
            button.draw(screen)

        # Draw labels at specific positions
        label_font = pygame.font.Font(None, 20)

        # Draw robot count below Remove Robot button (around y+110)
        if "Robots" in self.labels:
            robots_text = label_font.render(self.labels["Robots"], True, (50, 50, 50))
            robots_rect = robots_text.get_rect(centerx=self.rect.centerx, y=self.rect.y + 110)
            screen.blit(robots_text, robots_rect)

        # Draw speed label above speed buttons (20 pixels above the buttons)
        if "Speed" in self.labels and hasattr(self, 'speed_buttons_y'):
            speed_text = label_font.render(self.labels["Speed"], True, (50, 50, 50))
            speed_rect = speed_text.get_rect(centerx=self.rect.centerx, y=int(self.speed_buttons_y - 25))
            screen.blit(speed_text, speed_rect)

        # Draw pause status below Pause/Play button
        if hasattr(self, 'pause_button_y'):
            status_font = pygame.font.Font(None, 24)
            if self.paused:
                status_text = status_font.render("PAUSED", True, (255, 0, 0))
            else:
                status_text = status_font.render("RUNNING", True, (0, 150, 0))
            status_rect = status_text.get_rect(centerx=self.rect.centerx, y=int(self.pause_button_y + 35))
            screen.blit(status_text, status_rect)