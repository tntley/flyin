from collections import Counter
from graph import Graph
from parsing import Zone, Connection, ZoneType
import heapq


class ReservationTable:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self._zones: Counter[tuple[str, int]] = Counter()
        self._connections: Counter[tuple[str, int]] = Counter()

    def is_zone_free(
            self,
            zone: Zone,
            t: int
    ) -> bool:
        occupancy = self._zones[(zone.name, t)]
        capacity = self.graph.zone_capacity(zone)
        return occupancy < capacity

    def is_connection_free(
            self,
            link: Connection,
            t: int
    ) -> bool:
        occupancy = self._connections[(link.name, t)]
        capacity = link.capacity
        return occupancy < capacity

    def book_zone(
            self,
            zone: Zone,
            t: int
    ) -> None:
        self._zones[(zone.name, t)] += 1

    def book_connection(
            self,
            link: Connection,
            t: int
    ) -> None:
        self._connections[(link.name, t)] += 1


class Planner:
    def __init__(
            self,
            graph: Graph,
    ) -> None:
        self.graph = graph

    def _next_state(
            self,
            zone: Zone,
            t: int,
            table: ReservationTable
    ) -> list[tuple[int, Zone, Connection | None]]:
        options: list[tuple[int, Zone, Connection | None]] = []
        if table.is_zone_free(zone, t + 1):
            options.append((t + 1, zone, None))
        for link in self.graph.connections_of(zone):
            destination = link.other_zone(zone)
            if not self.graph.can_enter(destination):
                continue
            if destination.type is ZoneType.RESTRICTED:
                if table.is_zone_free(destination, t + 2) and table.is_connection_free(link, t + 1):
                    options.append((t + 2, destination, link))
            else:
                if table.is_zone_free(destination, t+1) and table.is_connection_free(link, t+1):
                    options.append((t + 1, destination, link))
        return options

    def _find_route(
            self,
            table: ReservationTable,
            max_time: int
    ) -> list[tuple[int, Zone, int, Connection | None]]:
        start = (0, 0, self.graph.start.name)
        heap: list[tuple[int, int, str]] = [start]
        done: set[tuple[int, str]] = set()
        best_cost: dict[tuple[int, str], tuple[int, int]] = {}
        came_from: dict[
            tuple[int, str], tuple[tuple[int, str], Connection | None]] = {}
        end_state: tuple[int, str] | None = None

        while heap:
            current = heapq.heappop(heap)
            time, priority, current_name = current
            current_state = (time, current_name)
            if current_state in done:
                continue
            done.add(current_state)
            current_zone = self.graph.zones[current_name]
            if current_zone is self.graph.end:
                end_state = (time, current_zone.name)
                break
            next_states = self._next_state(
                current_zone,
                time,
                table
            )
            for next_time, next_zone, link in next_states:
                neighbor_name = next_zone.name
                new_priority = priority - (1 if next_zone.is_priority else 0)
                next_state = (next_time, neighbor_name)
                cost = (next_time, new_priority)
                if next_state in done or next_time > max_time:
                    continue
                if next_state not in best_cost or best_cost[next_state] > cost:
                    best_cost[next_state] = cost
                    heapq.heappush(
                        heap,
                        (next_time, new_priority, neighbor_name)
                    )
                    came_from[next_state] = ((time, current_zone.name), link)
        if end_state is None:
            return None
        return self._reconstruct_path(end_state, came_from)

    def _reconstruct_path(
            self,
            end_state: tuple[int, str],
            came_from: dict[tuple[int, str], tuple[tuple[int, str], Connection | None]]
    ) -> list[tuple[int, Zone, int, Connection | None]]:
        result: list[tuple[int, Zone, int, Connection | None]] = []
        start_state = (0, self.graph.start.name)
        current_state = end_state

        while current_state != start_state:
            final_time, final_zone_name = current_state
            previous_state, link = came_from[current_state]
            previous_time, _ = previous_state
            final_zone = self.graph.zones[final_zone_name]
            result.append((previous_time, final_zone, final_time, link))
            current_state = previous_state
        result.reverse()
        return result

        for state in came_from:
            if start_state in came_from[state]:
                break
            final_time, final_zone_name = state
            previous_time, previous_zone_name = came_from[state]
            link = came_from[state][1]
            final_zone = self.graph.zones[final_zone_name]
            result.append((final_time, final_zone, previous_time, link))
        result.reverse()
        return result
