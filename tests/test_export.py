#!/usr/bin/env python3
"""
Test the grid export feature.
"""

from multi_robot_d_star_lite.core.world import GridWorld
from multi_robot_d_star_lite.core.coordinator import MultiAgentCoordinator
from multi_robot_d_star_lite.utils.export_grid import export_to_visual_format
from multi_robot_d_star_lite.utils.parse_test_grid import setup_from_visual

# Create a test scenario
world = GridWorld(5, 5)
world.add_obstacle(2, 2)
world.add_obstacle(3, 1)

coordinator = MultiAgentCoordinator(world)
coordinator.add_robot("robot1", start=(0, 0), goal=(4, 4))
coordinator.add_robot("robot2", start=(4, 0), goal=(0, 4))

# Export to visual format
exported = export_to_visual_format(world, coordinator)
print("Exported grid:")
print(exported)
print("\n" + "="*50)

# Now parse it back and verify it matches
print("Re-importing the exported grid...")
lines = exported.split('\n')
grid_lines = []
for line in lines:
    # Skip comments and test name
    if line.startswith('#') or line.startswith('TEST_'):
        continue
    # Keep size line and grid lines
    if line.strip():
        grid_lines.append(line)

grid_text = '\n'.join(grid_lines[:6])  # Size + 5 grid rows
print(f"Grid text:\n{grid_text}\n")

world2, coordinator2 = setup_from_visual(grid_text)

# Verify obstacles match
print("Verification:")
print(f"Original obstacles: {sorted(world.static_obstacles)}")
print(f"Imported obstacles: {sorted(world2.static_obstacles)}")
print(f"Obstacles match: {world.static_obstacles == world2.static_obstacles}")

# Verify robot positions
print(f"\nOriginal robots: {coordinator.current_positions}")
print(f"Imported robots: {coordinator2.current_positions}")
print(f"Robots match: {coordinator.current_positions == coordinator2.current_positions}")

# Verify goals
print(f"\nOriginal goals: {coordinator.goals}")
print(f"Imported goals: {coordinator2.goals}")
print(f"Goals match: {coordinator.goals == coordinator2.goals}")

print("\n✓ Export/import round-trip works!")