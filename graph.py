"""Create the Graph and the PathFinder objects for one drone.

The Graph object describes the structure of the whole network, while the
PathFinder object checks if a single drone can actually reache the end
of the network.
"""

from parsing import Zone, Connection, ZoneType
from collections.abc import Sequence
import heapq


class Graph:
    """The network of zones and connections as a whole.

    Attributes
    ----------
    zones : dict[str, Zone]
        Zone names paired to their actual object.
    connections : list[Connection]
        All the Connection objects present in the map.
    start : Zone
        The starting zone of the map.
    end : Zone
        The ending zone of the map.
    nb_drones : int
        Number of drones in play.
    _adjacent : dict[str, list[Connection]]
        Pair the zone name to its connections.
    """

    def __init__(
            self,
            zones: dict[str, Zone],
            connections: list[Connection],
            start: Zone,
            end: Zone,
            nb_drones: int
    ) -> None:
        """Instantiate the Graph object with all its describing components.

        Parameters
        ----------
        zones : dict[str, Zone]
            Zone names paired to their actual object.
        connections : list[Connection]
            All the Connection objects present in the map.
        start : Zone
            The starting zone of the map.
        end : Zone
            The ending zone of the map.
        nb_drones : int
            Number of drones in play.
        """
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
        """Display all connections linked to a zone.

        Parameters
        ----------
        zone : Zone
            The zone whose connections are to be listed.

        Returns
        -------
        Sequence[Connection]
            Iterable of all connection objects having the specified zone as
            one of its end.
        """
        return self._adjacent[zone.name]

    def can_enter(self, zone: Zone) -> bool:
        """Check whether the zone is blocked or not."""
        return zone.type is not ZoneType.BLOCKED

    def zone_capacity(self, zone: Zone) -> int:
        """Display the capacity of the zone.

        Starting and ending zones's capacities match the number of drones in
        play.

        Parameters
        ----------
        zone : Zone
            The zone whose connections are to be listed.

        Returns
        -------
        int
            Max number of drones the zone can hold simultaneously.
        """
        if zone is self.start or zone is self.end:
            return self.nb_drones
        return zone.capacity

    def connection_between(self, zone_a: Zone, zone_b: Zone) -> Connection:
        """Return the actual connection between two zones if it exists.

        Parameters
        ----------
        zone_a : Zone
            Zone at one end of the connection.
        zone_b : Zone
            Zone at the other end of the connection.

        Returns
        -------
        Connection
            The actual Connection object between the two zones.
        """
        for connection in self.connections_of(zone_a):
            if connection.other_zone(zone_a) is zone_b:
                return connection
        raise ValueError(f"{zone_a.name} and {zone_b.name} are not connected")


class PathFinder:
    """Shortest route for a single drone, ignoring all others.

    This uses Dijkstra's algorithm, where each moves costs the entry cost
    of the destination zone. Among routes with the same number of turns, the
    one that passes through a priority zone is preferred. Blocked zones are
    never an option.

    The result is used prior the planning, to make sure the ending zone is
    reachable. The length of the route will be used as a reference for the
    maximum number of turns by the Planner later.

    Attributes
    ----------
    graph : Graph
        The map to search.
    """

    def __init__(self, graph: Graph) -> None:
        """Create the PathFinder object."""
        self.graph = graph

    def find_path(self) -> list[Zone] | None:
        """Find the route with the least significant number of turns.

        Returns
        -------
        list[Zone] | None
            The route it found as a list of the passed zones, None if the end
            is not reached.
        """
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
                if (
                    neighbor_name in done
                    or not self.graph.can_enter(other_end)
                ):
                    continue
                turns = current_turns + other_end.entry_cost
                new_priority = priority - (1 if other_end.is_priority else 0)
                cost = (turns, new_priority)
                if (
                    neighbor_name not in best_cost
                    or best_cost[neighbor_name] > cost
                ):
                    best_cost[neighbor_name] = cost
                    heapq.heappush(heap, (turns, new_priority, neighbor_name))
                    came_from[neighbor_name] = current_name
        if self.graph.end.name not in came_from:
            return None
        return self._final_path(came_from)

    def _final_path(self, came_from: dict[str, str]) -> list[Zone]:
        """Reconstruct the route from start to end.

        Parameters
        ----------
        came_from : dict[str, str]
            Pair a zone name to the zone name before it in the route.

        Returns
        -------
        list[Zone]
            The actual route from the start to the end zone.
        """
        path: list[Zone] = []
        name = self.graph.end.name
        while name != self.graph.start.name:
            path.append(self.graph.zones[name])
            name = came_from[name]
        path.append(self.graph.start)
        path.reverse()
        # print([zone.name for zone in path])
        return path
