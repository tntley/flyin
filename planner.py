from collections import Counter
from graph import Graph
from parsing import Zone, Connection


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


