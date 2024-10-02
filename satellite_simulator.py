from typing import List, Tuple
import heapq

class Satellite:
    def __init__(self, x: int, y: int, satellite_type: str, direction: str, compute_capacity: int):
        self.x = x
        self.y = y
        self.satellite_type = satellite_type
        self.direction = direction
        self.compute_capacity = compute_capacity

class SatelliteNetwork:
    def __init__(self):
        self.satellites = {}

    def add_satellite(self, satellite: Satellite):
        self.satellites[(satellite.x, satellite.y)] = satellite

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            new_x, new_y = x + dx, y + dy
            if (new_x, new_y) in self.satellites:
                neighbors.append((new_x, new_y))
        return neighbors

    def shortest_path(self, source: Tuple[int, int], target: Tuple[int, int]) -> List[Tuple[int, int]]:
        queue = [(0, source, [])]
        visited = set()

        while queue:
            (cost, current, path) = heapq.heappop(queue)

            if current == target:
                return path + [current]

            if current in visited:
                continue

            visited.add(current)

            for neighbor in self.get_neighbors(*current):
                if neighbor not in visited:
                    new_cost = cost + (1 if current[1] == neighbor[1] else 2)  # Intra-orbital: 1, Inter-orbital: 2
                    heapq.heappush(queue, (new_cost, neighbor, path + [current]))

        return []  # No path found

    def closest_compute_satellite(self, source: Tuple[int, int]) -> Tuple[int, int]:
        queue = [(0, source)]
        visited = set()

        while queue:
            (cost, current) = heapq.heappop(queue)

            if current in visited:
                continue

            visited.add(current)

            if self.satellites[current].satellite_type == "CS":
                return current

            for neighbor in self.get_neighbors(*current):
                if neighbor not in visited:
                    new_cost = cost + (1 if current[1] == neighbor[1] else 2)  # Intra-orbital: 1, Inter-orbital: 2
                    heapq.heappush(queue, (new_cost, neighbor))

        return None  # No Compute Satellite found

def read_input_file(filename: str) -> Tuple[SatelliteNetwork, List[Tuple[int, int, int, int]]]:
    network = SatelliteNetwork()
    queries = []
    
    with open(filename, 'r') as f:
        num_satellites = int(f.readline().strip())
        
        for _ in range(num_satellites):
            x, y, sat_type, direction, capacity = f.readline().strip().split()
            satellite = Satellite(int(x), int(y), sat_type, direction, int(capacity))
            network.add_satellite(satellite)
        
        num_queries = int(f.readline().strip())
        for _ in range(num_queries):
            query_type, *coords = map(int, f.readline().strip().split())
            queries.append((query_type, *coords))
    
    return network, queries

def main():
    input_file = "sample_input.txt"
    network, queries = read_input_file(input_file)

    for query in queries:
        if query[0] == 1:  # Shortest path query
            source = (query[1], query[2])
            target = (query[3], query[4])
            path = network.shortest_path(source, target)
            if path:
                print(f"Shortest path from {source} to {target}:", " -> ".join(f"({x},{y})" for x, y in path))
            else:
                print(f"No path found between {source} and {target}.")
        elif query[0] == 2:  # Closest Compute Satellite query
            source = (query[1], query[2])
            closest_cs = network.closest_compute_satellite(source)
            if closest_cs:
                print(f"Closest Compute Satellite to {source}: {closest_cs}")
            else:
                print(f"No Compute Satellite found for {source}.")

if __name__ == "__main__":
    main()