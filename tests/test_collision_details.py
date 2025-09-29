#!/usr/bin/env python3
"""
Test collision detail tracking for accurate logging.
Ensures collision pairs and positions are correctly preserved.
"""

import pytest
from multi_robot_playground.core.world import GridWorld
from multi_robot_playground.core.coordinator import MultiAgentCoordinator


class TestCollisionDetailTracking:
    """Test that collision details are accurately tracked."""

    def test_collision_details_stored(self):
        """Test that collision details are stored with pairs and positions."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Set up multiple same-cell collisions at different positions
        # Collision 1: robotA and robotB both trying to enter (5,3)
        coordinator.add_robot("robotA", start=(4, 3), goal=(6, 3))
        coordinator.add_robot("robotB", start=(6, 3), goal=(4, 3))

        # Collision 2: robotC and robotD both trying to enter (5,5)
        coordinator.add_robot("robotC", start=(4, 5), goal=(6, 5))
        coordinator.add_robot("robotD", start=(6, 5), goal=(4, 5))

        coordinator.recompute_paths()

        # Calculate collisions
        collisions = coordinator.calculate_collisions()

        # Check that collision_details attribute exists
        assert hasattr(coordinator, 'collision_details'), "Coordinator should have collision_details"

        # Should have 2 collision groups
        details = coordinator.collision_details
        assert len(details) == 2, f"Should have 2 collision groups, got {len(details)}"

        # Check first collision
        collision1 = next((d for d in details if set(d['robots']) == {'robotA', 'robotB'}), None)
        assert collision1 is not None, "Should find collision between robotA and robotB"
        assert collision1['type'] == 'same_cell'
        assert collision1['position'] == (5, 3)

        # Check second collision
        collision2 = next((d for d in details if set(d['robots']) == {'robotC', 'robotD'}), None)
        assert collision2 is not None, "Should find collision between robotC and robotD"
        assert collision2['type'] == 'same_cell'
        assert collision2['position'] == (5, 5)

        print("✓ Collision details correctly track pairs and positions")

    def test_multiple_robots_same_cell(self):
        """Test 3+ robots trying to enter the same cell."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Three robots all trying to enter (5,5)
        coordinator.add_robot("robot1", start=(4, 5), goal=(6, 5))
        coordinator.add_robot("robot2", start=(5, 4), goal=(5, 6))
        coordinator.add_robot("robot3", start=(6, 5), goal=(4, 5))

        coordinator.recompute_paths()

        # Calculate collisions
        collisions = coordinator.calculate_collisions()

        details = coordinator.collision_details

        # Should find collisions between all pairs trying to enter (5,5)
        # We expect multiple same_cell collision entries for the pairs
        same_cell_at_5_5 = [d for d in details if d['type'] == 'same_cell' and d['position'] == (5, 5)]

        # Should have detected the collision at (5,5)
        assert len(same_cell_at_5_5) > 0, "Should detect same-cell collision at (5,5)"

        # Collect all robots involved in collision at (5,5)
        robots_at_5_5 = set()
        for detail in same_cell_at_5_5:
            robots_at_5_5.update(detail['robots'])

        # All three robots should be involved
        assert robots_at_5_5 == {'robot1', 'robot2', 'robot3'}, f"All three robots should collide at (5,5), got {robots_at_5_5}"

        print("✓ Multiple robots at same cell tracked correctly")

    def test_swap_collision_details(self):
        """Test swap collision details are tracked."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Two robots swapping positions
        coordinator.add_robot("robotX", start=(3, 3), goal=(4, 3))
        coordinator.add_robot("robotY", start=(4, 3), goal=(3, 3))

        coordinator.recompute_paths()

        collisions = coordinator.calculate_collisions()
        details = coordinator.collision_details

        # Should have one swap collision
        assert len(details) == 1, f"Should have 1 collision, got {len(details)}"
        assert details[0]['type'] == 'swap'
        assert set(details[0]['robots']) == {'robotX', 'robotY'}
        assert set(details[0]['positions']) == {(3, 3), (4, 3)}

        print("✓ Swap collision details tracked correctly")

    def test_blocked_robot_details(self):
        """Test blocked robot collision details - same as test_single_blocked_robot_collision."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # A and B will swap (get blocked)
        coordinator.add_robot("robotA", start=(3, 3), goal=(4, 3))
        coordinator.add_robot("robotB", start=(4, 3), goal=(3, 3))

        # C tries to move through A's position
        coordinator.add_robot("robotC", start=(2, 3), goal=(5, 3))

        coordinator.recompute_paths()

        collisions = coordinator.calculate_collisions()
        details = coordinator.collision_details

        # Should have swap collision between A&B and same_cell collision between B&C
        swap_detail = next((d for d in details if d['type'] == 'swap'), None)
        same_cell_detail = next((d for d in details if d['type'] == 'same_cell'), None)

        assert swap_detail is not None, "Should have swap collision"
        assert set(swap_detail['robots']) == {'robotA', 'robotB'}

        assert same_cell_detail is not None, "Should have same_cell collision"
        assert 'robotB' in same_cell_detail['robots'] and 'robotC' in same_cell_detail['robots'], \
            f"Should have B and C in same_cell collision, got {same_cell_detail}"

        print("✓ Collision details tracked correctly (swap + same_cell)")

    def test_cascade_blocked_details(self):
        """Test cascade of blocked robots - same as test_cascade_chain."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # A and B will collide (swap)
        coordinator.add_robot("robotA", start=(5, 5), goal=(6, 5))
        coordinator.add_robot("robotB", start=(6, 5), goal=(5, 5))

        # C tries to go through A, D through C, E through D
        coordinator.add_robot("robotC", start=(4, 5), goal=(7, 5))  # Through A at (5,5)
        coordinator.add_robot("robotD", start=(3, 5), goal=(7, 5))  # Through C at (4,5)
        coordinator.add_robot("robotE", start=(2, 5), goal=(7, 5))  # Through D at (3,5)

        coordinator.recompute_paths()

        collisions = coordinator.calculate_collisions()
        details = coordinator.collision_details

        # Should have: swap(A,B), same_cell(B,C), blocked(D by C), blocked(E by D)
        swap_detail = next((d for d in details if d['type'] == 'swap'), None)
        same_cell_detail = next((d for d in details if d['type'] == 'same_cell'), None)

        assert swap_detail is not None, "Should have swap collision"
        assert set(swap_detail['robots']) == {'robotA', 'robotB'}

        assert same_cell_detail is not None, "Should have same_cell collision"
        assert set(same_cell_detail['robots']) == {'robotB', 'robotC'}

        # Find blocked robot details
        blocked_details = [d for d in details if d['type'] == 'blocked_robot']

        # D blocked by C, E blocked by D
        d_blocked = next((d for d in blocked_details if 'robotD' in d['robots']), None)
        e_blocked = next((d for d in blocked_details if 'robotE' in d['robots']), None)

        assert d_blocked is not None, "robotD should be blocked"
        assert d_blocked['blocked_by'] == 'robotC', f"robotD should be blocked by robotC, got {d_blocked.get('blocked_by')}"

        assert e_blocked is not None, "robotE should be blocked"
        assert e_blocked['blocked_by'] == 'robotD', f"robotE should be blocked by robotD, got {e_blocked.get('blocked_by')}"

        print("✓ Cascade blocked robot details tracked correctly")


if __name__ == "__main__":
    test = TestCollisionDetailTracking()
    test.test_collision_details_stored()
    test.test_multiple_robots_same_cell()
    test.test_swap_collision_details()
    test.test_blocked_robot_details()
    test.test_cascade_blocked_details()
    print("\nAll collision detail tests passed!")