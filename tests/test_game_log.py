#!/usr/bin/env python3
"""
Tests for the GameLog component.

These tests ensure that:
1. GameLog properly initializes with correct dimensions
2. Messages are added with timestamps and types
3. Message limit is enforced
4. Auto-scrolling works correctly
5. Different message types have different colors
6. Messages render correctly
"""

import pytest
import pygame
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from multi_robot_d_star_lite.pygame.game_log import GameLog


class TestGameLogCreation:
    """Test GameLog initialization and setup."""

    def test_game_log_creation(self):
        """GameLog should initialize with correct dimensions."""
        pygame.init()
        log = GameLog(10, 20, 200, 400)

        assert log.rect.x == 10
        assert log.rect.y == 20
        assert log.rect.width == 200
        assert log.rect.height == 400
        assert log.messages == []
        assert log.max_messages == 100
        pygame.quit()

    def test_default_colors(self):
        """GameLog should have default colors for message types."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        assert 'info' in log.colors
        assert 'warning' in log.colors
        assert 'error' in log.colors
        assert 'success' in log.colors
        assert 'collision' in log.colors

        # Verify colors are RGB tuples
        for color in log.colors.values():
            assert isinstance(color, tuple)
            assert len(color) == 3
        pygame.quit()


class TestMessageHandling:
    """Test adding and managing messages."""

    def test_add_message(self):
        """Should add messages with timestamps."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        log.add_message("Test message", "info")

        assert len(log.messages) == 1
        timestamp, msg_type, text = log.messages[0]
        assert isinstance(timestamp, str)
        assert msg_type == "info"
        assert text == "Test message"
        pygame.quit()

    def test_message_types(self):
        """Different message types should be stored correctly."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        log.add_message("Info message", "info")
        log.add_message("Warning message", "warning")
        log.add_message("Error message", "error")
        log.add_message("Success message", "success")
        log.add_message("Collision message", "collision")

        assert len(log.messages) == 5

        types = [msg[1] for msg in log.messages]
        assert types == ["info", "warning", "error", "success", "collision"]
        pygame.quit()

    def test_default_message_type(self):
        """Messages without type should default to 'info'."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        log.add_message("Default message")

        assert log.messages[0][1] == "info"
        pygame.quit()

    def test_max_messages(self):
        """Should limit messages to max_messages count."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)
        log.max_messages = 5  # Set small limit for testing

        # Add more than max messages
        for i in range(10):
            log.add_message(f"Message {i}")

        assert len(log.messages) == 5
        # Should keep latest messages
        assert log.messages[0][2] == "Message 5"
        assert log.messages[-1][2] == "Message 9"
        pygame.quit()

    def test_clear_log(self):
        """Should be able to clear all messages."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        log.add_message("Message 1")
        log.add_message("Message 2")
        log.add_message("Message 3")

        log.clear()

        assert len(log.messages) == 0
        pygame.quit()


class TestScrolling:
    """Test scrolling functionality."""

    def test_auto_scroll(self):
        """Should auto-scroll to show latest message."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        # Add many messages
        for i in range(50):
            log.add_message(f"Message {i}")

        # Should be scrolled to bottom (latest messages visible)
        # scroll_offset should be adjusted
        assert log.should_auto_scroll == True
        pygame.quit()

    def test_manual_scroll(self):
        """Should support manual scrolling."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        # Add many messages
        for i in range(50):
            log.add_message(f"Message {i}")

        # Scroll up
        log.scroll_up()
        assert log.should_auto_scroll == False  # Disable auto-scroll when manually scrolling

        # Scroll down
        log.scroll_down()
        pygame.quit()

    def test_scroll_limits(self):
        """Scrolling should be limited to valid range."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        # Add a few messages
        for i in range(5):
            log.add_message(f"Message {i}")

        # Try to scroll beyond limits
        for _ in range(10):
            log.scroll_up()
        assert log.scroll_offset >= 0

        for _ in range(10):
            log.scroll_down()
        # scroll_offset should not exceed message count
        pygame.quit()


class TestRendering:
    """Test rendering functionality."""

    @patch('pygame.draw.rect')
    def test_render_messages(self, mock_rect):
        """Should render messages on screen."""
        pygame.init()
        mock_screen = MagicMock()

        log = GameLog(0, 0, 200, 400)
        log.add_message("Test message", "info")

        # Replace font with mock for testing
        mock_font = MagicMock()
        mock_font.size.return_value = (100, 20)
        mock_font.render.return_value = MagicMock()
        log.font = mock_font
        log.timestamp_font = mock_font

        log.render(mock_screen)

        # Should draw background
        mock_rect.assert_called()

        # Should render text (through font.render calls)
        assert mock_font.render.called
        pygame.quit()

    @patch('pygame.draw.rect')
    def test_message_colors(self, mock_rect):
        """Different message types should use different colors."""
        pygame.init()
        mock_screen = MagicMock()

        log = GameLog(0, 0, 200, 400)

        # Add different types of messages
        log.add_message("Info", "info")
        log.add_message("Warning", "warning")
        log.add_message("Error", "error")

        # Replace font with mock
        mock_font = MagicMock()
        mock_font.size.return_value = (100, 20)
        mock_font.render.return_value = MagicMock()
        log.font = mock_font
        log.timestamp_font = mock_font

        log.render(mock_screen)

        # Check that different message types have different colors
        assert log.colors['info'] != log.colors['warning']
        assert log.colors['warning'] != log.colors['error']
        assert log.colors['error'] != log.colors['info']
        pygame.quit()

    def test_timestamp_format(self):
        """Timestamps should be formatted correctly."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        with patch('multi_robot_d_star_lite.game_log.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "12:34:56"
            log.add_message("Test")

            assert log.messages[0][0] == "12:34:56"
        pygame.quit()


class TestMessageFormatting:
    """Test message formatting and word wrap."""

    def test_long_message_wrap(self):
        """Long messages should be wrapped to fit width."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        long_message = "This is a very long message that should be wrapped to fit within the log panel width"
        log.add_message(long_message)

        # Message should be stored intact
        assert log.messages[0][2] == long_message

        # When rendering, it should be wrapped (this would be tested with actual rendering)
        pygame.quit()

    def test_multiline_message(self):
        """Should handle messages with newlines."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        multiline = "Line 1\nLine 2\nLine 3"
        log.add_message(multiline)

        assert log.messages[0][2] == multiline
        pygame.quit()


class TestIntegration:
    """Test integration with other components."""

    def test_handle_events(self):
        """Should handle pygame events for scrolling."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)

        # Add messages
        for i in range(20):
            log.add_message(f"Message {i}")

        # Create scroll up event
        event_up = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 4, 'pos': (100, 100)})
        handled = log.handle_event(event_up)

        # Create scroll down event
        event_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 5, 'pos': (100, 100)})
        handled = log.handle_event(event_down)

        pygame.quit()

    def test_get_visible_messages(self):
        """Should return only visible messages based on scroll position."""
        pygame.init()
        log = GameLog(0, 0, 200, 400)
        log.line_height = 20  # Each line is 20 pixels

        # Add many messages
        for i in range(30):
            log.add_message(f"Message {i}")

        # With 400px height and 20px per line, should show 20 messages
        visible = log.get_visible_messages()
        assert len(visible) <= 20
        pygame.quit()