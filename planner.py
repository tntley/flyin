from collections import Counter
from graph import Graph
from parsing import Zone, Connection, ZoneType


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


