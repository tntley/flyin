from parsing import Zone, Connection, ZoneType
from collections.abc import Sequence
import heapq


class Graph:

    def __init__(
            self,
            zones: dict[str, Zone],
            connections: list[Connection],
            start: Zone,
            end: Zone,
            nb_drones: int
    ) -> None:
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end
        self.nb_drones = nb_drones
        self._adjacent: dict[str, list[Connection]] = {
            name: [] for name in zones
        }
        for connection in connections:
            self._adjacent[connection.zone_a.name].append(connection)
            self._adjacent[connection.zone_b.name].append(connection)

    def connections_of(self, zone: Zone) -> Sequence[Connection]:
        return self._adjacent[zone.name]

    def can_enter(self, zone: Zone) -> bool:
        return zone.type is not ZoneType.BLOCKED

    def zone_capacity(self, zone: Zone) -> int:
        if zone is self.start or zone is self.end:
            return self.nb_drones
        return zone.capacity

    def connection_between(self, zone_a: Zone, zone_b: Zone) -> Connection:
        for connection in self.connections_of(zone_a):
            if connection.other_zone(zone_a) is zone_b:
                return connection
        raise ValueError(f"{zone_a.name} and {zone_b.name} are not connected")


class PathFinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_path(self) -> list[Zone] | None:
        start = (0, 0, self.graph.start.name)
        heap: list[tuple[int, int, str]] = [start]
        done: set[str] = set()
        best_cost: dict[str, tuple[int, int]] = {}
        came_from: dict[str, str] = {}

        while heap:
            current = heapq.heappop(heap)
            current_turns, priority, current_name = current
            if current_name in done:
                continue
            done.add(current_name)
            current_zone = self.graph.zones[current_name]
            if current_zone is self.graph.end:
                break
            link = self.graph.connections_of(
                current_zone
            )
            for connection in link:
                other_end = connection.other_zone(current_zone)
                neighbor_name = other_end.name
                if neighbor_name in done or not self.graph.can_enter(other_end):
                    continue
                turns = current_turns + other_end.entry_cost
                new_priority = priority - (1 if other_end.is_priority else 0)
                cost = (turns, new_priority)
                if neighbor_name not in best_cost or best_cost[neighbor_name] > cost:
                    best_cost[neighbor_name] = cost
                    heapq.heappush(heap, (turns, new_priority, neighbor_name))
                    came_from[neighbor_name] = current_name
        if self.graph.end.name not in came_from:
            return None
        return self._final_path(came_from)

    def _final_path(self, came_from: dict[str, str]) -> list[Zone]:
        path: list[Zone] = []
        name = self.graph.end.name
        while name != self.graph.start.name:
            path.append(self.graph.zones[name])
            name = came_from[name]
        path.append(self.graph.start)
        path.reverse()
        # print([zone.name for zone in path])
        return path





