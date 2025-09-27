#!/usr/bin/env python3
"""
Test collision state management for partial pausing.

These tests ensure that:
1. Robot pause states are properly tracked
2. State transitions work correctly
3. Multiple pause reasons are handled
4. Collision pairs are tracked accurately
"""

import pytest
from multi_robot_d_star_lite.core.world import GridWorld
from multi_robot_d_star_lite.core.coordinator import MultiAgentCoordinator


class TestPauseStateInitialization:
    """Test initialization of pause states."""

    def test_robot_pause_state_initialization(self):
        """All robots should start in non-paused state."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(0, 5), goal=(5, 5))

        # Initially no robots should be paused
        assert hasattr(coordinator, 'paused_robots')
        assert len(coordinator.paused_robots) == 0

    def test_pause_state_attributes_exist(self):
        """Coordinator should have all pause-related attributes."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        assert hasattr(coordinator, 'paused_robots')
        assert hasattr(coordinator, 'collision_pairs')
        assert isinstance(coordinator.paused_robots, dict)
        assert isinstance(coordinator.collision_pairs, list)


class TestPauseStateTransitions:
    """Test state transitions for paused robots."""

    def test_pause_state_transitions(self):
        """Test transitions: moving -> paused -> moving."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(2, 0), goal=(0, 0))

        coordinator.recompute_paths()

        # Initially moving (not paused)
        assert "robot0" not in coordinator.paused_robots
        assert "robot1" not in coordinator.paused_robots

        # Step until collision
        for _ in range(3):
            should_continue, collision, stuck, paused = coordinator.step_simulation()
            if collision:
                break

        # Should transition to paused
        if collision:
            assert len(paused) > 0
            for robot_id in paused:
                assert robot_id in coordinator.paused_robots

    def test_pause_to_resume_transition(self):
        """Robot should properly transition from paused to resumed."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(2, 0), goal=(2, 2))  # Will move away

        coordinator.recompute_paths()

        # Create pause condition
        for _ in range(3):
            should_continue, collision, stuck, paused = coordinator.step_simulation()

        if "robot0" in coordinator.paused_robots:
            # Clear the pause condition
            coordinator.resume_robot("robot0")
            assert "robot0" not in coordinator.paused_robots

    def test_multiple_pause_reasons(self):
        """Robot can have multiple reasons for being paused."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))

        # Pause for collision
        coordinator.pause_robot("robot0", "collision")
        assert coordinator.paused_robots["robot0"] == "collision"

        # Add manual pause on top
        coordinator.pause_robot("robot0", "manual")
        # Should track the most recent or combine reasons
        assert "robot0" in coordinator.paused_robots

    def test_pause_state_persistence(self):
        """Pause state should persist across simulation steps."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(2, 0), goal=(0, 0))

        coordinator.recompute_paths()

        # Create collision
        for _ in range(3):
            should_continue, collision, stuck, paused = coordinator.step_simulation()
            if collision:
                break

        initial_paused = set(coordinator.paused_robots.keys())

        # Step again without resolving
        should_continue, collision, stuck, paused = coordinator.step_simulation()

        # Pause state should persist
        for robot_id in initial_paused:
            assert robot_id in coordinator.paused_robots


class TestPauseStateQueries:
    """Test querying pause states."""

    def test_is_robot_paused(self):
        """Should correctly report if robot is paused."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(0, 5), goal=(5, 5))

        # Initially not paused
        assert not coordinator.is_robot_paused("robot0")
        assert not coordinator.is_robot_paused("robot1")

        # Pause robot0
        coordinator.pause_robot("robot0", "test")

        assert coordinator.is_robot_paused("robot0")
        assert not coordinator.is_robot_paused("robot1")

    def test_get_paused_robots(self):
        """Should return list of all paused robots."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(0, 5), goal=(5, 5))
        coordinator.add_robot("robot2", start=(5, 0), goal=(0, 0))

        # Pause some robots
        coordinator.pause_robot("robot0", "collision")
        coordinator.pause_robot("robot2", "collision")

        paused = coordinator.get_paused_robots()
        assert len(paused) == 2
        assert "robot0" in paused
        assert "robot2" in paused
        assert "robot1" not in paused

    def test_get_pause_reason(self):
        """Should return the reason why robot is paused."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))

        # Pause with specific reason
        coordinator.pause_robot("robot0", "same_cell_collision")

        reason = coordinator.get_pause_reason("robot0")
        assert reason == "same_cell_collision"

        # Non-paused robot should return None
        coordinator.add_robot("robot1", start=(0, 5), goal=(5, 5))
        reason = coordinator.get_pause_reason("robot1")
        assert reason is None

    def test_collision_pair_tracking(self):
        """Should track which robots are in collision pairs."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(2, 0), goal=(0, 0))

        coordinator.recompute_paths()

        # Step until collision
        for _ in range(3):
            should_continue, collision, stuck, paused = coordinator.step_simulation()
            if collision:
                robot1, robot2, collision_type = collision
                # Should track collision pair
                assert len(coordinator.collision_pairs) > 0
                # Verify pair contains both robots
                pair_found = False
                for pair in coordinator.collision_pairs:
                    if robot1 in pair and robot2 in pair:
                        pair_found = True
                        break
                assert pair_found
                break


class TestPauseOperations:
    """Test pause and resume operations."""

    def test_pause_robot_operation(self):
        """pause_robot should correctly pause a robot."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))

        # Pause the robot
        coordinator.pause_robot("robot0", "manual")

        assert "robot0" in coordinator.paused_robots
        assert coordinator.paused_robots["robot0"] == "manual"

    def test_resume_robot_operation(self):
        """resume_robot should correctly resume a robot."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))

        # Pause then resume
        coordinator.pause_robot("robot0", "test")
        assert "robot0" in coordinator.paused_robots

        coordinator.resume_robot("robot0")
        assert "robot0" not in coordinator.paused_robots

    def test_pause_nonexistent_robot(self):
        """Pausing non-existent robot should handle gracefully."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Should not crash
        coordinator.pause_robot("robot99", "test")
        # Could either ignore or add to paused_robots
        # Behavior depends on implementation

    def test_resume_nonpaused_robot(self):
        """Resuming non-paused robot should handle gracefully."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))

        # Should not crash
        coordinator.resume_robot("robot0")
        assert "robot0" not in coordinator.paused_robots


class TestCollisionPairManagement:
    """Test management of collision pairs."""

    def test_add_collision_pair(self):
        """Should correctly add collision pair."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(5, 0), goal=(0, 0))

        # Add collision pair
        coordinator.add_collision_pair("robot0", "robot1", "swap")

        assert len(coordinator.collision_pairs) == 1
        pair = coordinator.collision_pairs[0]
        assert "robot0" in pair
        assert "robot1" in pair

    def test_remove_collision_pair(self):
        """Should correctly remove collision pair."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(5, 0), goal=(0, 0))

        # Add then remove
        coordinator.add_collision_pair("robot0", "robot1", "swap")
        assert len(coordinator.collision_pairs) == 1

        coordinator.remove_collision_pair("robot0", "robot1")
        assert len(coordinator.collision_pairs) == 0

    def test_get_collision_partner(self):
        """Should return collision partner for a robot."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(5, 0), goal=(0, 0))

        coordinator.add_collision_pair("robot0", "robot1", "swap")

        partner = coordinator.get_collision_partner("robot0")
        assert partner == "robot1"

        partner = coordinator.get_collision_partner("robot1")
        assert partner == "robot0"

    def test_clear_collision_pairs(self):
        """Should clear all collision pairs."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Add multiple pairs
        coordinator.add_collision_pair("robot0", "robot1", "swap")
        coordinator.add_collision_pair("robot2", "robot3", "same_cell")

        assert len(coordinator.collision_pairs) == 2

        coordinator.clear_collision_pairs()
        assert len(coordinator.collision_pairs) == 0


class TestPauseWithMovement:
    """Test pause state during movement."""

    def test_paused_robot_doesnt_move(self):
        """Paused robot should not move when simulation steps."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.recompute_paths()

        # Pause the robot
        coordinator.pause_robot("robot0", "manual")

        initial_pos = coordinator.current_positions["robot0"]

        # Step simulation
        coordinator.step_simulation()

        final_pos = coordinator.current_positions["robot0"]

        # Position should not change
        assert initial_pos == final_pos

    def test_only_unpaused_robots_move(self):
        """Only unpaused robots should move during simulation."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        coordinator.add_robot("robot0", start=(0, 0), goal=(5, 0))
        coordinator.add_robot("robot1", start=(0, 5), goal=(5, 5))

        coordinator.recompute_paths()

        # Pause robot0
        coordinator.pause_robot("robot0", "test")

        initial_pos_0 = coordinator.current_positions["robot0"]
        initial_pos_1 = coordinator.current_positions["robot1"]

        # Step simulation
        coordinator.step_simulation()

        final_pos_0 = coordinator.current_positions["robot0"]
        final_pos_1 = coordinator.current_positions["robot1"]

        # robot0 should not move, robot1 should move
        assert initial_pos_0 == final_pos_0
        assert initial_pos_1 != final_pos_1

    def test_pause_state_affects_path_planning(self):
        """Other robots should treat paused robots as obstacles."""
        world = GridWorld(10, 10)
        coordinator = MultiAgentCoordinator(world)

        # Robot0 will be paused in the middle
        coordinator.add_robot("robot0", start=(5, 0), goal=(5, 5))

        # Robot1 needs to go through robot0's position
        coordinator.add_robot("robot1", start=(0, 0), goal=(9, 0))

        # Move robot0 to middle and pause
        coordinator.recompute_paths()
        for _ in range(5):
            coordinator.step_simulation()

        coordinator.pause_robot("robot0", "manual")
        current_pos_0 = coordinator.current_positions["robot0"]

        # Recompute paths with robot0 paused
        coordinator.recompute_paths()

        # Robot1's path should avoid paused robot0
        path1 = coordinator.paths["robot1"]
        assert current_pos_0 not in path1  # Should route around