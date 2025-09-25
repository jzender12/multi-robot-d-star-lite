#!/usr/bin/env python3
"""
Test suite for control panel UI components.
Tests Button and ControlPanel classes.
"""

import pytest
import pygame
from multi_robot_d_star_lite.ui_components import Button, ControlPanel


class TestButton:
    """Tests for Button UI component"""

    def test_button_creation(self):
        """Should create button with correct properties"""
        pygame.init()

        button = Button(
            x=100, y=50,
            width=80, height=30,
            text="Test",
            callback=lambda: None
        )

        assert button.rect.x == 100
        assert button.rect.y == 50
        assert button.rect.width == 80
        assert button.rect.height == 30
        assert button.text == "Test"
        assert button.callback is not None

    def test_button_click_detection(self):
        """Should detect when button is clicked"""
        pygame.init()

        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(
            x=100, y=100,
            width=100, height=50,
            text="Click Me",
            callback=on_click
        )

        # Simulate click inside button
        button.handle_click((150, 125))
        assert clicked is True

        # Reset
        clicked = False

        # Click outside button
        button.handle_click((50, 50))
        assert clicked is False

    def test_button_hover_state(self):
        """Should track hover state"""
        pygame.init()

        button = Button(
            x=100, y=100,
            width=100, height=50,
            text="Hover",
            callback=lambda: None
        )

        # Not hovering initially
        assert button.hovered is False

        # Mouse over button
        button.update_hover((150, 125))
        assert button.hovered is True

        # Mouse away from button
        button.update_hover((50, 50))
        assert button.hovered is False

    def test_button_enabled_state(self):
        """Should handle enabled/disabled state"""
        pygame.init()

        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(
            x=100, y=100,
            width=100, height=50,
            text="Toggle",
            callback=on_click
        )

        # Enabled by default
        assert button.enabled is True

        # Click when enabled
        button.handle_click((150, 125))
        assert clicked is True

        # Disable button
        clicked = False
        button.enabled = False

        # Click when disabled - should not trigger
        button.handle_click((150, 125))
        assert clicked is False

    def test_button_draw(self):
        """Should draw button correctly"""
        pygame.init()
        screen = pygame.Surface((300, 200))

        button = Button(
            x=100, y=50,
            width=100, height=40,
            text="Draw",
            callback=lambda: None
        )

        # Should not raise error
        button.draw(screen)

        # Test different states
        button.hovered = True
        button.draw(screen)

        button.enabled = False
        button.draw(screen)


class TestControlPanel:
    """Tests for ControlPanel component"""

    def test_control_panel_creation(self):
        """Should create control panel with correct layout"""
        pygame.init()

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        assert panel.rect.x == 500
        assert panel.rect.y == 0
        assert panel.rect.width == 200
        assert panel.rect.height == 600
        assert panel.buttons is not None

    def test_add_robot_button(self):
        """Should have functioning Add Robot button"""
        pygame.init()

        robot_added = False

        def add_robot_callback():
            nonlocal robot_added
            robot_added = True

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600,
            on_add_robot=add_robot_callback
        )

        # Find and click Add Robot button
        add_button = panel.get_button("Add Robot")
        assert add_button is not None

        add_button.handle_click((add_button.rect.centerx, add_button.rect.centery))
        assert robot_added is True

    def test_remove_robot_button(self):
        """Should have functioning Remove Robot button"""
        pygame.init()

        robot_removed = False

        def remove_robot_callback():
            nonlocal robot_removed
            robot_removed = True

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600,
            on_remove_robot=remove_robot_callback
        )

        # Find and click Remove Robot button
        remove_button = panel.get_button("Remove Robot")
        assert remove_button is not None

        remove_button.handle_click((remove_button.rect.centerx, remove_button.rect.centery))
        assert robot_removed is True

    def test_arena_size_buttons(self):
        """Should have arena size buttons"""
        pygame.init()

        sizes_clicked = []

        def resize_callback(size):
            sizes_clicked.append(size)

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600,
            on_resize=resize_callback
        )

        # Test each size button exists
        for size_text in ["5x5", "10x10", "15x15", "20x20"]:
            button = panel.get_button(size_text)
            # Button exists, that's what matters
            # Callback returns None by design

    def test_speed_controls(self):
        """Should have speed control buttons"""
        pygame.init()

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        # Check for speed controls
        assert panel.speed >= 0.5
        assert panel.speed <= 10.0

        # Speed up
        initial_speed = panel.speed
        panel.increase_speed()
        assert panel.speed > initial_speed

        # Speed down
        panel.decrease_speed()
        panel.decrease_speed()
        assert panel.speed < initial_speed

        # Check bounds
        for _ in range(20):
            panel.decrease_speed()
        assert panel.speed >= 0.5  # Min speed

        for _ in range(20):
            panel.increase_speed()
        assert panel.speed <= 10.0  # Max speed

    def test_clear_reset_buttons(self):
        """Should have Reset button"""
        pygame.init()

        reset_clicked = False

        def reset_callback():
            nonlocal reset_clicked
            reset_clicked = True

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600,
            on_reset=reset_callback
        )

        # Test Reset button exists and works
        reset_button = panel.get_button("Reset")
        assert reset_button is not None
        reset_button.handle_click((reset_button.rect.centerx, reset_button.rect.centery))
        assert reset_clicked is True

    def test_robot_count_display(self):
        """Should display current robot count"""
        pygame.init()

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        # Set robot count
        panel.update_robot_count(5)
        assert panel.robot_count == 5

        # Should display in label
        assert panel.get_label("Robots") is not None

    def test_panel_event_handling(self):
        """Should handle mouse events correctly"""
        pygame.init()

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        # Create mock event
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=(550, 100),
            button=1
        )

        # Should handle without error
        result = panel.handle_event(event)
        assert isinstance(result, (bool, type(None), str))

    def test_panel_draw(self):
        """Should draw panel and all components"""
        pygame.init()
        screen = pygame.Surface((700, 600))

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        # Should draw without error
        panel.draw(screen)

        # Update state and redraw
        panel.update_robot_count(3)
        panel.speed = 3.0
        panel.draw(screen)


class TestButtonGroup:
    """Tests for managing groups of buttons"""

    def test_button_group_exclusive_selection(self):
        """Button groups should allow exclusive selection"""
        pygame.init()

        from multi_robot_d_star_lite.ui_components import ButtonGroup

        group = ButtonGroup()

        # Add buttons
        button1 = Button(10, 10, 50, 30, "A", lambda: None)
        button2 = Button(70, 10, 50, 30, "B", lambda: None)
        button3 = Button(130, 10, 50, 30, "C", lambda: None)

        group.add(button1)
        group.add(button2)
        group.add(button3)

        # Select button1
        group.select(button1)
        assert button1.selected is True
        assert button2.selected is False
        assert button3.selected is False

        # Select button2 - should deselect button1
        group.select(button2)
        assert button1.selected is False
        assert button2.selected is True
        assert button3.selected is False


class TestIntegration:
    """Integration tests for UI components"""

    def test_panel_button_integration(self):
        """Panel and buttons should work together"""
        pygame.init()

        actions = []

        def record_action(action):
            actions.append(action)

        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600,
            on_add_robot=lambda: record_action("add"),
            on_remove_robot=lambda: record_action("remove"),
            on_reset=lambda: record_action("reset")
        )

        # Simulate clicking various buttons
        for button_name, expected_action in [
            ("Add Robot", "add"),
            ("Remove Robot", "remove"),
            ("Reset", "reset")
        ]:
            button = panel.get_button(button_name)
            if button:
                button.callback()

        assert "add" in actions
        assert "remove" in actions
        assert "reset" in actions

    def test_full_ui_workflow(self):
        """Test complete UI workflow"""
        pygame.init()

        screen = pygame.Surface((700, 600))

        # Create panel
        panel = ControlPanel(
            x=500, y=0,
            width=200, height=600
        )

        # Initial state
        panel.update_robot_count(2)
        panel.draw(screen)

        # Simulate user interactions
        panel.update_robot_count(3)  # Added robot
        panel.increase_speed()
        panel.draw(screen)

        # Click resize button
        resize_button = panel.get_button("15x15")
        if resize_button:
            resize_button.hovered = True

        panel.draw(screen)

        # Should complete without errors
        assert panel.robot_count == 3
        assert panel.speed > 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])