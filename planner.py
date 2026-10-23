"""Plan the moves turn by turn by complying to all rules."""

from collections import Counter
from graph import Graph
from parsing import Zone, Connection, ZoneType
import heapq


class PlanningError(Exception):
    """Error raised when the planning couldn't deliver a drone."""

    def __init__(
            self,
            message: str
    ) -> None:
        super().__init__(f"Error during planning: {message}")


class ReservationTable:
    """Record which zones and connections are occupied, and when.

    A zone booked at time t holds the drone after t turns; a connection
    booked at time t is used during turn t.

    Parameters
    ----------
    graph : Graph
        The map to plan upon.
    """

    def __init__(self, graph: Graph) -> None:
        """Create a clean ReservationTable object with no booking anywhere."""
        self.graph = graph
        self._zones: Counter[tuple[str, int]] = Counter()
        self._connections: Counter[tuple[str, int]] = Counter()

    def is_zone_free(
            self,
            zone: Zone,
            t: int
    ) -> bool:
        """Check whether one more drone can fit in the zone at time t.

        Parameters
        ----------
        zone : Zone
            The zone to check.
        t : int
            The turn after which to check the capacity.

        Returns
        -------
        bool
            True if the drone can fit in the zone at time t.
        """
        occupancy = self._zones[(zone.name, t)]
        capacity = self.graph.zone_capacity(zone)
        return occupancy < capacity

    def is_connection_free(
            self,
            link: Connection,
            t: int
    ) -> bool:
        """Check whether one more drone can pass a connection at time t.

        Parameters
        ----------
        link : Connection
            The connection to check.
        t : int
            The turn after which to check the capacity.

        Returns
        -------
        bool
            True if the drone can pass that connection at time t.
        """
        occupancy = self._connections[(link.name, t)]
        capacity = link.capacity
        return occupancy < capacity

    def book_zone(
            self,
            zone: Zone,
            t: int
    ) -> None:
        """Reserve one place in the zone at time t."""
        self._zones[(zone.name, t)] += 1

    def book_connection(
            self,
            link: Connection,
            t: int
    ) -> None:
        """Reserve one place on the connection during turn t."""
        self._connections[(link.name, t)] += 1


class Planner:
    """Plan the drones movement turn by turn, one by one.

    Each drone's moves for each turn are planned around the earlier drones'
    reservation. If its preferred destination is booked at time t, it can
    wait or take another route.

    Parameters
    ----------
    graph : Graph
        The map to plan upon.
    """

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
        """List every legal next state for a drone in `zone` at time t.

        Parameters
        ----------
        zone : Zone
            The drone's current location.
        t : int
            The current time.
        table : ReservationTable
            The bookings made by earlier drones to plan around.

        Returns
        -------
        list[tuple[int, Zone, Connection | None]]
            (arrival time, zone, connection used) for each option;
            the connection is None for waiting.
        """
        options: list[tuple[int, Zone, Connection | None]] = []
        if table.is_zone_free(zone, t + 1):
            options.append((t + 1, zone, None))
        for link in self.graph.connections_of(zone):
            destination = link.other_zone(zone)
            if not self.graph.can_enter(destination):
                continue
            if destination.type is ZoneType.RESTRICTED:
                if (
                    table.is_zone_free(destination, t + 2)
                    and table.is_connection_free(link, t + 1)
                ):
                    options.append((t + 2, destination, link))
            else:
                if (
                    table.is_zone_free(destination, t+1)
                    and table.is_connection_free(link, t+1)
                ):
                    options.append((t + 1, destination, link))
        return options

    def _find_route(
            self,
            table: ReservationTable,
            max_time: int
    ) -> list[tuple[int, Zone, int, Connection | None]] | None:
        """Find the earliest route to goal based on the bookings.

        Parameters
        ----------
        table : ReservationTable
            The bookings made by earlier drones.
        max_time : int
            Supposed max turns for a drone to reach the goal. States after
            this are not considered anymore.

        Returns
        -------
        list[tuple[int, Zone, int, Connection | None]] or None
            The route's steps as (start time, zone, end time, connection),
            or None if no route ends within max_time.
        """
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
            came_from: dict[
                tuple[int, str],
                tuple[tuple[int, str], Connection | None]
            ]
    ) -> list[tuple[int, Zone, int, Connection | None]]:
        """Rebuild a route by followind previous zones back to the start.

        Parameters
        ----------
        end_state : tuple[int, str]
            The (time, zone name) state mathing the end.
        came_from : dict[tuple[int, str], tuple[tuple[int, str], Connection |
        None]]
            Maps each state to its previous state with the used link.

        Returns
        -------
        list[tuple[int, Zone, int, Connection | None]]
            The route's steps as (start time, zone, end time, connection)
        """
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

    def plan(
            self,
            max_time: int
    ) -> list[dict[int, Connection]]:
        """Plan the moves per turn for each drone and return them.

        Parameters
        ----------
        max_time : int
            Time limit for each drone to secure a valid route.

        Returns
        -------
        list[dict[int, Connection]]
            One move dictionnary per turn, will be passed to Simulation.run.
        """
        schedule: list[dict[int, Connection]] = []
        table = ReservationTable(self.graph)
        for drone_id in range(1, self.graph.nb_drones + 1):
            route = self._find_route(table, max_time)
            if route is None:
                raise PlanningError(f"Drone no.{drone_id}"
                                    " couldn't secure a route")
            for previous_t, final_z, final_t, link in route:
                table.book_zone(final_z, final_t)
                if link is not None:
                    table.book_connection(link, previous_t + 1)
                    while len(schedule) <= previous_t:
                        schedule.append({})
                    schedule[previous_t][drone_id] = link
        return schedule
