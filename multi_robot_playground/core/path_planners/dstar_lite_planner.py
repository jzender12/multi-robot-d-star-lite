import heapq
from typing import Tuple, List, Set, Optional, Dict
from collections import defaultdict
from .base_planner import PathPlanner


class DStarLitePlanner(PathPlanner):
    """
    D* Lite pathfinder for a single robot.

    The algorithm maintains two values per cell:
    - g(s): current shortest path estimate from goal
    - rhs(s): one-step lookahead value

    When g(s) != rhs(s), the cell is inconsistent and needs processing.
    Uses Manhattan distance heuristic for 4-connected grid.
    """

    def __init__(self, world, robot_id: str):
        super().__init__(world, robot_id)

        # Algorithm state
        self.g = defaultdict(lambda: float('inf'))
        self.rhs = defaultdict(lambda: float('inf'))
        self.km = 0  # Key modifier for maintaining priority queue consistency
        self.open_list = []  # Priority queue
        self.open_set = set()  # For quick membership testing
        self.last_start = None

    def calculate_key(self, s: Tuple[int, int]) -> Tuple[float, float]:
        """
        Calculate priority key for vertex s.
        Returns (k1, k2) for lexicographic ordering.

        The km value accumulates heuristic changes as robot moves,
        preventing expensive priority queue reorganization.
        """
        min_val = min(self.g[s], self.rhs[s])
        return (min_val + self.heuristic(self.start, s) + self.km, min_val)

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Manhattan distance heuristic for 4-connected grid.
        Returns |x1-x2| + |y1-y2|
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def update_vertex(self, s: Tuple[int, int]):
        """
        Update vertex in priority queue based on consistency.
        This is called whenever a vertex's rhs value changes.
        """
        if s != self.goal:
            # Recalculate rhs as minimum cost from successors
            self.rhs[s] = float('inf')
            for nx, ny, cost in self.world.get_neighbors(s[0], s[1]):
                neighbor = (nx, ny)
                if self.world.is_free(nx, ny, self.robot_id):
                    self.rhs[s] = min(self.rhs[s], cost + self.g[neighbor])

        # Remove from queue if present
        if s in self.open_set:
            self.open_set.remove(s)
            # Mark heap for cleanup (we'll ignore removed items when popping)

        # Add back if inconsistent
        if self.g[s] != self.rhs[s]:
            key = self.calculate_key(s)
            heapq.heappush(self.open_list, (key, s))
            self.open_set.add(s)

    def compute_shortest_path(self):
        """
        Main D* Lite search loop.
        Processes inconsistent vertices until start is consistent and optimal.
        Returns: (success: bool, reason: str)
        """
        iterations = 0
        max_iterations = self.world.width * self.world.height * 100

        while self.open_list:
            # Prevent infinite loops in pathological cases
            iterations += 1
            if iterations > max_iterations:
                return False, f"max_iterations_exceeded ({max_iterations})"

            # Get vertex with minimum key
            while self.open_list:
                key, u = heapq.heappop(self.open_list)
                if u in self.open_set:
                    self.open_set.remove(u)
                    break
            else:
                break  # Open list is empty

            # Check if we're done
            if (key >= self.calculate_key(self.start) and
                self.rhs[self.start] == self.g[self.start]):
                return True, "path_found"

            k_old = key
            k_new = self.calculate_key(u)

            if k_old < k_new:
                # Key increased, re-insert with new key
                heapq.heappush(self.open_list, (k_new, u))
                self.open_set.add(u)
            elif self.g[u] > self.rhs[u]:
                # Overconsistent - lower g value
                self.g[u] = self.rhs[u]

                # Update all predecessors
                for nx, ny, cost in self.world.get_neighbors(u[0], u[1]):
                    neighbor = (nx, ny)
                    if self.world.is_free(nx, ny, self.robot_id):
                        self.update_vertex(neighbor)
            else:
                # Underconsistent - raise g value
                g_old = self.g[u]
                self.g[u] = float('inf')

                # Update u and predecessors that depended on old g value
                predecessors = [u]
                for nx, ny, cost in self.world.get_neighbors(u[0], u[1]):
                    neighbor = (nx, ny)
                    if self.world.is_free(nx, ny, self.robot_id):
                        predecessors.append(neighbor)

                for s in predecessors:
                    # Check if this predecessor was using the old path through u
                    # Need to recalculate cost from this predecessor to u
                    for nnx, nny, ncost in self.world.get_neighbors(s[0], s[1]):
                        if (nnx, nny) == u and self.world.is_free(nnx, nny, self.robot_id):
                            if abs(self.rhs[s] - (ncost + g_old)) < 1e-9:  # Floating point comparison
                                if s != self.goal:
                                    # Recalculate rhs
                                    self.rhs[s] = float('inf')
                                    for nnnx, nnny, nncost in self.world.get_neighbors(s[0], s[1]):
                                        nn = (nnnx, nnny)
                                        if self.world.is_free(nnnx, nnny, self.robot_id):
                                            self.rhs[s] = min(self.rhs[s], nncost + self.g[nn])
                                break
                    self.update_vertex(s)

        # Check final state
        if self.g[self.start] == float('inf'):
            return False, "no_path_exists (goal unreachable)"
        elif self.rhs[self.start] != self.g[self.start]:
            return False, "inconsistent_state (g != rhs at start)"
        else:
            return True, "path_found"

    def initialize(self, start: Tuple[int, int], goal: Tuple[int, int]):
        """
        Initialize algorithm for new planning problem.
        Called once at the beginning.
        """
        self.start = start
        self.goal = goal
        self.last_start = start
        self.km = 0

        # Clear previous search
        self.g.clear()
        self.rhs.clear()
        self.open_list = []
        self.open_set = set()

        # Set goal vertex
        self.rhs[goal] = 0
        key = self.calculate_key(goal)
        heapq.heappush(self.open_list, (key, goal))
        self.open_set.add(goal)

    def update_edge_costs(self, changed_cells: Set[Tuple[int, int]]):
        """
        Update algorithm when obstacles change.
        This is where D* Lite's incremental nature shines.
        """
        if not changed_cells:
            return

        # Update km for robot movement (CRITICAL for correctness)
        if self.last_start != self.start:
            self.km += self.heuristic(self.last_start, self.start)
            self.last_start = self.start

        # Update vertices affected by changes
        for cell in changed_cells:
            # Update cell itself
            self.update_vertex(cell)

            # Update neighbors that might use paths through this cell
            for nx, ny, _ in self.world.get_neighbors(cell[0], cell[1]):
                neighbor = (nx, ny)
                self.update_vertex(neighbor)

    def get_path(self) -> List[Tuple[int, int]]:
        """
        Extract path from start to goal using gradient descent on g-values.
        Returns empty list if no path exists.
        """
        if self.g[self.start] == float('inf'):
            return []  # No path exists

        path = [self.start]
        current = self.start

        max_steps = self.world.width * self.world.height
        steps = 0

        while current != self.goal:
            steps += 1
            if steps > max_steps:
                print(f"Warning: Path extraction exceeded max steps for robot {self.robot_id}")
                return []

            # Find neighbor with minimum g-value
            best_neighbor = None
            best_cost = float('inf')

            for nx, ny, cost in self.world.get_neighbors(current[0], current[1]):
                neighbor = (nx, ny)
                if self.world.is_free(nx, ny, self.robot_id):
                    total_cost = cost + self.g[neighbor]
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_neighbor = neighbor

            if best_neighbor is None or best_neighbor == current:
                print(f"Warning: No progress in path extraction for robot {self.robot_id}")
                return path  # Return partial path

            path.append(best_neighbor)
            current = best_neighbor

        return path
    def get_algorithm_name(self) -> str:
        """Return the name of this algorithm."""
        return "D* Lite"
