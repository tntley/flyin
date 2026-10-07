from parsing import Zone, Connection, ZoneType
from collections.abc import Sequence


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

