#!/usr/bin/env python3
"""
Test the iterative collision detection system.
This replaces the pair-based system with a cleaner approach:
1. Detect path collisions (same_cell, swap, shear)
2. Iteratively detect blocked robot collisions
3. Continue until no new collisions found
"""

import pytest
from multi_robot_d_star_lite.core.world import GridWorld
from multi_robot_d_star_lite.core.coordinator import MultiAgentCoordinator


class TestBasicPathCollisions:
    """Test basic path-to-path collision detection."""

    def test_same_cell_collision(self):
        """Two robots trying to enter the same cell."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Both robots will try to enter (4,3)
        coordinator.add_robot("robotA", start=(3, 3), goal=(5, 3))
        coordinator.add_robot("robotB", start=(5, 3), goal=(3, 3))

        coordinator.recompute_paths()

        # Step - should detect same_cell collision
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 2, "Both robots should be blocked"
        assert "robotA" in blocked
        assert "robotB" in blocked
        print("✓ Same-cell collision: both robots blocked")

    def test_swap_collision(self):
        """Two robots exchanging positions."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Robots will swap positions
        coordinator.add_robot("robotA", start=(3, 3), goal=(4, 3))
        coordinator.add_robot("robotB", start=(4, 3), goal=(3, 3))

        coordinator.recompute_paths()

        # Step - should detect swap collision
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 2, "Both robots should be blocked"
        assert "robotA" in blocked
        assert "robotB" in blocked
        print("✓ Swap collision: both robots blocked")

    def test_shear_collision(self):
        """Perpendicular crossing collision."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # robotA moves right through (4,3), robotB moves down from (4,3)
        coordinator.add_robot("robotA", start=(3, 3), goal=(5, 3))
        coordinator.add_robot("robotB", start=(4, 3), goal=(4, 5))

        coordinator.recompute_paths()

        # Step - should detect shear collision
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 2, "Both robots should be blocked"
        assert "robotA" in blocked
        assert "robotB" in blocked
        print("✓ Shear collision: both robots blocked")


class TestBlockedRobotCollisions:
    """Test collision with blocked robots (cascade via iteration)."""

    def test_single_blocked_robot_collision(self):
        """Robot tries to move through a blocked robot's position."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # A and B will swap (get blocked)
        coordinator.add_robot("robotA", start=(3, 3), goal=(4, 3))
        coordinator.add_robot("robotB", start=(4, 3), goal=(3, 3))

        # C tries to move through A's position
        coordinator.add_robot("robotC", start=(2, 3), goal=(5, 3))

        coordinator.recompute_paths()

        # Step - should block all three
        # Iteration 1: A↔B swap detected
        # Iteration 2: C→A blocked robot collision detected
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 3, f"All three robots should be blocked, got {len(blocked)}"
        assert "robotA" in blocked
        assert "robotB" in blocked
        assert "robotC" in blocked
        print("✓ Blocked robot collision: C blocked by A's position")

    def test_cascade_chain(self):
        """Multiple robots cascade-blocked in sequence."""
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

        # Step - should cascade block all five
        # Iteration 1: A↔B
        # Iteration 2: C blocked by A
        # Iteration 3: D blocked by C
        # Iteration 4: E blocked by D
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 5, f"All five robots should be blocked, got {len(blocked)}"
        for robot in ["robotA", "robotB", "robotC", "robotD", "robotE"]:
            assert robot in blocked, f"{robot} should be blocked"
        print("✓ Cascade chain: All 5 robots blocked through iterations")


class TestMultipleSimultaneousCollisions:
    """Test multiple collision groups happening simultaneously."""

    def test_two_collision_pairs(self):
        """Two separate collision pairs."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # First swap collision
        coordinator.add_robot("robotA", start=(2, 2), goal=(3, 2))
        coordinator.add_robot("robotB", start=(3, 2), goal=(2, 2))

        # Second swap collision (independent)
        coordinator.add_robot("robotC", start=(6, 6), goal=(7, 6))
        coordinator.add_robot("robotD", start=(7, 6), goal=(6, 6))

        coordinator.recompute_paths()

        # Step - should detect both collisions
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 4, "All four robots should be blocked"
        for robot in ["robotA", "robotB", "robotC", "robotD"]:
            assert robot in blocked
        print("✓ Two simultaneous swaps: 4 robots blocked")

    def test_multiple_collisions_with_cascade(self):
        """Multiple initial collisions plus cascade effects."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # First collision pair (swap)
        coordinator.add_robot("robotA", start=(3, 3), goal=(4, 3))
        coordinator.add_robot("robotB", start=(4, 3), goal=(3, 3))

        # Second collision pair (same_cell at 6,6)
        coordinator.add_robot("robotC", start=(5, 6), goal=(7, 6))
        coordinator.add_robot("robotD", start=(7, 6), goal=(5, 6))

        # Cascade robots
        coordinator.add_robot("robotE", start=(2, 3), goal=(5, 3))  # Hits A
        coordinator.add_robot("robotF", start=(6, 5), goal=(6, 7))  # Hits collision at (6,6)

        coordinator.recompute_paths()

        # Step - should block all six
        _, collision, _, blocked = coordinator.step_simulation()

        assert len(blocked) == 6, f"All six robots should be blocked, got {len(blocked)}"
        for robot in ["robotA", "robotB", "robotC", "robotD", "robotE", "robotF"]:
            assert robot in blocked, f"{robot} should be blocked"
        print("✓ Multiple collisions with cascade: 6 robots blocked")


class TestCollisionRecovery:
    """Test robots recovering when collisions are resolved."""

    def test_recovery_via_obstacle(self):
        """Placing an obstacle resolves collision."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Create a swap collision
        coordinator.add_robot("robotA", start=(3, 3), goal=(5, 3))
        coordinator.add_robot("robotB", start=(5, 3), goal=(3, 3))

        coordinator.recompute_paths()

        # Create collision
        _, collision, _, blocked = coordinator.step_simulation()
        assert len(blocked) == 2

        # Place obstacle to force alternate paths
        coordinator.add_dynamic_obstacle(4, 3)

        # Check if collision resolved
        _, collision, _, blocked = coordinator.step_simulation()

        # Robots should find alternate paths
        assert len(blocked) < 2, "Some or all robots should be unblocked with new paths"
        print(f"✓ Obstacle placement: {2 - len(blocked)} robots recovered")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ITERATIVE COLLISION SYSTEM")
    print("=" * 60)

    # Basic path collisions
    print("\n1. Basic Path Collisions")
    print("-" * 30)
    basic = TestBasicPathCollisions()
    basic.test_same_cell_collision()
    basic.test_swap_collision()
    basic.test_shear_collision()

    # Blocked robot collisions
    print("\n2. Blocked Robot Collisions")
    print("-" * 30)
    blocked = TestBlockedRobotCollisions()
    blocked.test_single_blocked_robot_collision()
    blocked.test_cascade_chain()

    # Multiple simultaneous
    print("\n3. Multiple Simultaneous Collisions")
    print("-" * 30)
    multi = TestMultipleSimultaneousCollisions()
    multi.test_two_collision_pairs()
    multi.test_multiple_collisions_with_cascade()

    # Recovery
    print("\n4. Collision Recovery")
    print("-" * 30)
    recovery = TestCollisionRecovery()
    recovery.test_recovery_via_obstacle()

    print("\n" + "=" * 60)
    print("ALL ITERATIVE COLLISION TESTS COMPLETE ✓")
    print("=" * 60)