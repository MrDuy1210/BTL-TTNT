import heapq
from collections import defaultdict
import json
import os

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

class SokobanAStar:
    def __init__(self, level, player_pos):
        self.level = [row[:] for row in level]  # Copy level
        self.width = len(level[0])
        self.height = len(level)
        self.goals = [(x, y) for y in range(self.height) for x in range(self.width) if level[y][x] in [4, 5]]
        self.initial_player = player_pos
        self.initial_boxes = frozenset((x, y) for y in range(self.height) for x in range(self.width) if level[y][x] in [3, 5])

    def is_wall(self, x, y):
        return self.level[y][x] == 1

    def is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and not self.is_wall(x, y)

    def heuristic(self, boxes):
        cost = 0
        for box in boxes:
            min_dist = min(manhattan_distance(box, goal) for goal in self.goals)
            cost += min_dist
        return cost

    def get_neighbors(self, player, boxes):
        neighbors = []
        for dx, dy in DIRECTIONS:
            nx, ny = player[0] + dx, player[1] + dy
            if not self.is_valid(nx, ny):
                continue
            if (nx, ny) in boxes:  # Push box
                box_nx, box_ny = nx + dx, ny + dy
                if not self.is_valid(box_nx, box_ny) or (box_nx, box_ny) in boxes:
                    continue
                new_boxes = boxes - {(nx, ny)} | {(box_nx, box_ny)}
                neighbors.append(((nx, ny), new_boxes))
            else:  # Normal move
                neighbors.append(((nx, ny), boxes))
        return neighbors

    def solve(self):
        start_state = (self.initial_player, self.initial_boxes)
        open_set = []
        heapq.heappush(open_set, (0 + self.heuristic(self.initial_boxes), 0, start_state))
        
        came_from = {}
        g_score = defaultdict(lambda: float('inf'))
        g_score[start_state] = 0
        
        visited = set()
        
        while open_set:
            _, current_g, current = heapq.heappop(open_set)
            player, boxes = current
            
            if all(box in self.goals for box in boxes):
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_state)
                return path[::-1]
            
            visited.add(current)
            
            for neighbor in self.get_neighbors(player, boxes):
                tentative_g = current_g + 1
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor[1])
                    heapq.heappush(open_set, (f, tentative_g, neighbor))
        
        return None  # No solution found

def load_level(level_file):
    with open(level_file, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    level_files = [os.path.join('levels', f) for f in os.listdir('levels') if f.endswith('.json')]
    levels = [load_level(level_file) for level_file in level_files]
    
    player_pos = (1, 1)  # Example starting position
    solver = SokobanAStar(levels[0], player_pos)  # Load the first level for demonstration
    solution = solver.solve()
    
    if solution:
        print("Solution found! Steps:", len(solution) - 1)
        for state in solution:
            print("Player:", state[0], "Boxes:", state[1])
    else:
        print("No solution found.")
