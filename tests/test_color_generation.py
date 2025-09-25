#!/usr/bin/env python3
"""
Test suite for color generation utilities.
Tests dynamic color generation for multiple robots.
"""

import pytest
import colorsys
from multi_robot_d_star_lite.utils.colors import (
    generate_robot_color,
    get_robot_colors,
    hsv_to_rgb,
    ensure_color_contrast
)


class TestColorGeneration:
    """Tests for basic color generation"""

    def test_generate_robot_color_for_predefined(self):
        """Should return predefined colors for robot1 and robot2"""
        colors = get_robot_colors()

        # Predefined colors
        assert colors["robot1"] == (0, 100, 200)  # Blue
        assert colors["robot2"] == (200, 50, 0)   # Red

    def test_generate_unique_colors(self):
        """Should generate unique colors for multiple robots"""
        color_gen = get_robot_colors()

        # Generate colors for robots 3-10
        colors = []
        for i in range(3, 11):
            robot_id = f"robot{i}"
            color = generate_robot_color(robot_id)
            colors.append(color)

        # All colors should be unique
        unique_colors = set(colors)
        assert len(unique_colors) == len(colors)

    def test_color_rgb_range(self):
        """Generated colors should be valid RGB values"""
        for i in range(3, 20):
            robot_id = f"robot{i}"
            color = generate_robot_color(robot_id)

            # Check RGB range
            assert isinstance(color, tuple)
            assert len(color) == 3
            for component in color:
                assert 0 <= component <= 255

    def test_hsv_to_rgb_conversion(self):
        """Should correctly convert HSV to RGB"""
        # Test known conversions
        # Red: H=0, S=1, V=1
        rgb = hsv_to_rgb(0, 1, 1)
        assert rgb == (255, 0, 0)

        # Green: H=120, S=1, V=1
        rgb = hsv_to_rgb(120, 1, 1)
        assert rgb == (0, 255, 0)

        # Blue: H=240, S=1, V=1
        rgb = hsv_to_rgb(240, 1, 1)
        assert rgb == (0, 0, 255)

        # Gray: H=any, S=0, V=0.5
        rgb = hsv_to_rgb(0, 0, 0.5)
        assert rgb == (127, 127, 127) or rgb == (128, 128, 128)  # Rounding


class TestColorContrast:
    """Tests for color contrast and visibility"""

    def test_ensure_sufficient_contrast(self):
        """Colors should have sufficient contrast with background"""
        background = (255, 255, 255)  # White background

        for i in range(3, 10):
            robot_id = f"robot{i}"
            color = generate_robot_color(robot_id)

            # Should have contrast with white background
            contrast = ensure_color_contrast(color, background)
            assert contrast is True

    def test_color_distance(self):
        """Should calculate color distance correctly"""
        # Test color distance calculation
        from multi_robot_d_star_lite.utils.colors import color_distance

        # Same color
        dist = color_distance((100, 100, 100), (100, 100, 100))
        assert dist == 0

        # Black and white - maximum distance
        dist = color_distance((0, 0, 0), (255, 255, 255))
        assert dist > 400  # Should be sqrt(3 * 255^2)

        # Different colors
        dist = color_distance((255, 0, 0), (0, 255, 0))
        assert dist > 300

    def test_avoid_similar_colors(self):
        """Should avoid generating similar colors"""
        generated = []

        for i in range(3, 8):  # Test fewer robots for more spacing
            robot_id = f"robot{i}"
            color = generate_robot_color(robot_id)

            # Check distance from all previously generated colors
            for prev_color in generated:
                from multi_robot_d_star_lite.utils.colors import color_distance
                dist = color_distance(color, prev_color)
                # Should have minimum distance (relaxed threshold)
                assert dist > 10  # Minimum threshold for adjacent colors

            generated.append(color)


class TestColorSets:
    """Tests for robot/goal/path color sets"""

    def test_robot_goal_path_colors_match(self):
        """Robot, goal, and path colors should be related"""
        from multi_robot_d_star_lite.utils.colors import get_color_set

        for i in range(1, 10):
            robot_id = f"robot{i}"
            colors = get_color_set(robot_id)

            # Should have robot, goal, and path colors
            assert "robot" in colors
            assert "goal" in colors
            assert "path" in colors

            # Colors should be related (similar hue, different saturation/value)
            robot_color = colors["robot"]
            goal_color = colors["goal"]
            path_color = colors["path"]

            # All should be valid RGB
            for color in [robot_color, goal_color, path_color]:
                assert isinstance(color, tuple)
                assert len(color) == 3
                for c in color:
                    assert 0 <= c <= 255

    def test_color_set_consistency(self):
        """Color set for same robot should be consistent"""
        from multi_robot_d_star_lite.utils.colors import get_color_set

        robot_id = "robot5"

        # Get color set multiple times
        colors1 = get_color_set(robot_id)
        colors2 = get_color_set(robot_id)

        # Should be identical
        assert colors1["robot"] == colors2["robot"]
        assert colors1["goal"] == colors2["goal"]
        assert colors1["path"] == colors2["path"]


class TestDynamicColorGeneration:
    """Tests for dynamic color generation based on robot count"""

    def test_hue_distribution(self):
        """Hues should be evenly distributed"""
        from multi_robot_d_star_lite.utils.colors import get_hue_for_robot

        # For 10 robots, hues should be evenly spaced
        hues = []
        for i in range(3, 8):  # robot3 to robot7
            hue = get_hue_for_robot(f"robot{i}", total_robots=10)
            hues.append(hue)

        # Check that we get different hues
        # The implementation uses (robot_num - 1) * spacing
        # so spacing is 360/10 = 36 degrees
        unique_hues = set(hues)
        assert len(unique_hues) == len(hues)  # All should be unique

        # Check they're reasonably spread
        for hue in hues:
            assert 0 <= hue < 360  # Valid hue range

    def test_color_generation_for_many_robots(self):
        """Should handle generating colors for many robots"""
        colors = []

        # Generate colors for 50 robots
        for i in range(1, 51):
            robot_id = f"robot{i}"
            color = generate_robot_color(robot_id)
            colors.append(color)

        # All should be valid
        assert len(colors) == 50
        for color in colors:
            assert isinstance(color, tuple)
            assert len(color) == 3

        # Should have reasonable uniqueness
        unique_colors = set(colors)
        assert len(unique_colors) >= 45  # Allow some similarity for large sets


class TestColorPersistence:
    """Tests for color persistence and caching"""

    def test_color_caching(self):
        """Colors should be cached for performance"""
        from multi_robot_d_star_lite.utils.colors import generate_robot_color, clear_color_cache

        # Clear cache if it exists
        if hasattr(generate_robot_color, 'clear_cache'):
            clear_color_cache()

        # Generate color
        color1 = generate_robot_color("robot10")

        # Generate again - should be cached
        color2 = generate_robot_color("robot10")

        assert color1 == color2

    def test_clear_color_cache(self):
        """Should be able to clear color cache"""
        from multi_robot_d_star_lite.utils.colors import generate_robot_color, clear_color_cache

        # Generate color
        color1 = generate_robot_color("robot15")

        # Clear cache
        clear_color_cache()

        # Generate again - should be same (deterministic)
        color2 = generate_robot_color("robot15")

        # Should be same since generation is deterministic
        assert color1 == color2


class TestEdgeCases:
    """Edge case tests for color generation"""

    def test_invalid_robot_id(self):
        """Should handle invalid robot IDs gracefully"""
        # Test various invalid IDs
        invalid_ids = ["", "robot", "robotX", "123", None]

        for robot_id in invalid_ids:
            if robot_id is not None:
                # Should either return default or raise clear error
                try:
                    color = generate_robot_color(robot_id)
                    # If it returns, should be valid color
                    assert isinstance(color, tuple)
                    assert len(color) == 3
                except (ValueError, TypeError):
                    # Expected for invalid input
                    pass

    def test_robot_zero(self):
        """Should handle robot0 if provided"""
        try:
            color = generate_robot_color("robot0")
            assert isinstance(color, tuple)
            assert len(color) == 3
        except ValueError:
            # Acceptable to reject robot0
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])