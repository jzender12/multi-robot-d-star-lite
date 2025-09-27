#!/usr/bin/env python3
"""
Game log panel for displaying simulation events.

This module provides a scrollable log panel that displays timestamped
messages with color coding based on message type.
"""

import pygame
from datetime import datetime
from typing import List, Tuple, Optional


class GameLog:
    """
    A scrollable game log panel for displaying simulation events.

    Attributes:
        rect: pygame.Rect defining the panel's position and size
        messages: List of (timestamp, type, text) tuples
        max_messages: Maximum number of messages to keep
        scroll_offset: Current scroll position
        should_auto_scroll: Whether to auto-scroll to latest message
        colors: Dictionary of message type to RGB color
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize the game log panel.

        Args:
            x: X position of the panel
            y: Y position of the panel
            width: Width of the panel
            height: Height of the panel
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.messages: List[Tuple[str, str, str]] = []
        self.max_messages = 100
        self.scroll_offset = 0
        self.should_auto_scroll = True
        self.line_height = 18

        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 14)
        self.timestamp_font = pygame.font.Font(None, 12)

        # Message type colors
        self.colors = {
            'info': (60, 60, 60),
            'warning': (200, 150, 0),
            'error': (200, 0, 0),
            'success': (0, 150, 0),
            'collision': (255, 0, 0)
        }

        # Panel colors
        self.bg_color = (245, 245, 245)
        self.border_color = (200, 200, 200)
        self.timestamp_color = (150, 150, 150)

        # Scrollbar properties
        self.scrollbar_width = 10
        self.scrollbar_color = (180, 180, 180)
        self.scrollbar_hover_color = (150, 150, 150)

    def add_message(self, text: str, msg_type: str = 'info'):
        """
        Add a message to the log.

        Args:
            text: The message text
            msg_type: Type of message (info, warning, error, success, collision)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, msg_type, text))

        # Trim to max messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        # Auto-scroll to latest if enabled
        if self.should_auto_scroll:
            self.scroll_to_bottom()

    def clear(self):
        """Clear all messages from the log."""
        self.messages = []
        self.scroll_offset = 0

    def scroll_up(self):
        """Scroll the log up by one line."""
        self.scroll_offset = max(0, self.scroll_offset - 1)
        self.should_auto_scroll = False

    def scroll_down(self):
        """Scroll the log down by one line."""
        max_offset = max(0, len(self.messages) - self.get_visible_lines())
        self.scroll_offset = min(max_offset, self.scroll_offset + 1)

        # Re-enable auto-scroll if at bottom
        if self.scroll_offset >= max_offset:
            self.should_auto_scroll = True

    def scroll_to_bottom(self):
        """Scroll to show the latest messages."""
        visible_lines = self.get_visible_lines()
        self.scroll_offset = max(0, len(self.messages) - visible_lines)

    def get_visible_lines(self) -> int:
        """Calculate how many lines can be displayed."""
        # Account for padding and header
        available_height = self.rect.height - 40  # Header and padding
        return available_height // self.line_height

    def get_visible_messages(self) -> List[Tuple[str, str, str]]:
        """Get the currently visible messages based on scroll position."""
        visible_lines = self.get_visible_lines()
        start = self.scroll_offset
        end = min(len(self.messages), start + visible_lines)
        return self.messages[start:end]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events for scrolling.

        Args:
            event: pygame event to handle

        Returns:
            True if event was handled, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if mouse is over the log panel
            if self.rect.collidepoint(event.pos):
                # Mouse wheel up
                if event.button == 4:
                    self.scroll_up()
                    return True
                # Mouse wheel down
                elif event.button == 5:
                    self.scroll_down()
                    return True

        return False

    def render(self, screen: pygame.Surface):
        """
        Render the game log panel.

        Args:
            screen: pygame surface to render on
        """
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        # Draw header
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 30)
        pygame.draw.rect(screen, self.border_color, header_rect)
        pygame.draw.rect(screen, self.border_color, header_rect, 2)

        # Draw title
        title_text = self.font.render("Game Log", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(
            self.rect.x + self.rect.width // 2,
            self.rect.y + 15
        ))
        screen.blit(title_text, title_rect)

        # Create clipping area for messages
        message_area = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 35,
            self.rect.width - 15,  # Leave room for scrollbar
            self.rect.height - 40
        )

        # Draw messages
        visible_messages = self.get_visible_messages()
        y_offset = message_area.y

        for timestamp, msg_type, text in visible_messages:
            # Draw timestamp
            timestamp_surface = self.timestamp_font.render(
                timestamp, True, self.timestamp_color
            )
            screen.blit(timestamp_surface, (message_area.x, y_offset))

            # Draw message text (with color based on type)
            color = self.colors.get(msg_type, self.colors['info'])

            # Word wrap if necessary
            wrapped_lines = self._wrap_text(text, message_area.width - 60)

            for line in wrapped_lines:
                text_surface = self.font.render(line, True, color)
                screen.blit(text_surface, (message_area.x + 55, y_offset))
                y_offset += self.line_height

                # Stop if we've filled the visible area
                if y_offset > message_area.y + message_area.height:
                    break

            # Break if we've filled the visible area
            if y_offset > message_area.y + message_area.height:
                break

        # Draw scrollbar if needed
        if len(self.messages) > self.get_visible_lines():
            self._draw_scrollbar(screen)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within the given width.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels

        Returns:
            List of wrapped text lines
        """
        # Simple word wrapping - could be improved
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width = self.font.size(test_line)[0]

            if text_width > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def _draw_scrollbar(self, screen: pygame.Surface):
        """
        Draw a scrollbar on the right side of the panel.

        Args:
            screen: pygame surface to render on
        """
        scrollbar_x = self.rect.x + self.rect.width - self.scrollbar_width - 2
        scrollbar_y = self.rect.y + 35
        scrollbar_height = self.rect.height - 40

        # Draw scrollbar track
        track_rect = pygame.Rect(
            scrollbar_x, scrollbar_y,
            self.scrollbar_width, scrollbar_height
        )
        pygame.draw.rect(screen, (220, 220, 220), track_rect)

        # Calculate thumb size and position
        total_messages = len(self.messages)
        visible_lines = self.get_visible_lines()

        if total_messages > 0:
            # Thumb size proportional to visible content
            thumb_height = max(20, (visible_lines / total_messages) * scrollbar_height)

            # Thumb position based on scroll offset
            max_offset = max(1, total_messages - visible_lines)
            thumb_y = scrollbar_y + (self.scroll_offset / max_offset) * (scrollbar_height - thumb_height)

            # Draw thumb
            thumb_rect = pygame.Rect(
                scrollbar_x, int(thumb_y),
                self.scrollbar_width, int(thumb_height)
            )
            pygame.draw.rect(screen, self.scrollbar_color, thumb_rect)