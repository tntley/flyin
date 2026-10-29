"""Turn by turn simulation that checks a plan of moves and produce output."""


from drones import Drone, Transit
from parsing import Zone, Connection, ZoneType
from graph import Graph
from collections import Counter
from collections.abc import Callable
import sys


class SimulationError(Exception):
    """Error raised if the simulation crashes."""

    def __init__(
            self,
            message: str
    ) -> None:
        super().__init__(f"Error during simulation: {message}")


class Simulation:
    """Replay a plan turn by turn, rejecting moves that break the rules.

    Parameters
    ----------
    graph : Graph
        The map the drones move on.
    """

    def __init__(
            self,
            graph: Graph
    ) -> None:
        """Create the Simulation object."""
        self.turn: int = 0
        self.graph = graph
        self.drones: dict[int, Drone] = {
            i: Drone(i, self.graph.start, self.graph.end)
            for i in range(1, self.graph.nb_drones + 1)
        }
        self.route: dict[int, list[str]] = {
            id: [self.graph.start.name] for id in self.drones.keys()
        }

    @property
    def all_delivered(self) -> bool:
        """Check whether all drones in play have reached the goal."""
        return all(drone.is_delivered for drone in self.drones.values())

    def _check_moves(
            self,
            moves: dict[int, Connection]
    ) -> list[tuple[Drone, Connection, Zone]]:
        """Make sure a move follows the rules on one turn."""
        result: list[tuple[Drone, Connection, Zone]] = []
        for drone_id, connection in moves.items():
            if drone_id not in self.drones:
                raise SimulationError(f"No drone with id {drone_id}")
            drone = self.drones[drone_id]

            if drone.is_delivered:
                raise SimulationError(f"{drone.name} already delivered")
            if isinstance(drone.location, Transit):
                raise SimulationError(f"{drone.name} is already in transit")
            if (
                drone.location is not connection.zone_a
                and drone.location is not connection.zone_b
            ):
                raise SimulationError(
                    f"{drone.name} cannot take that connection right now")

            drone_destination = connection.other_zone(drone.location)
            if not self.graph.can_enter(drone_destination):
                raise SimulationError(
                    f"{drone.name} cannot access the other end")
            result.append((drone, connection, drone_destination))
        return result

    def _check_zone_capacity(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> None:
        """Check if a zone would exceed its capacity on a turn."""
        occupancy: Counter[str] = Counter()
        moving_drones = {
            drone.id: destination
            for drone, _, destination in planned
        }

        for drone in self.drones.values():
            if drone.is_delivered:
                continue
            if drone.id in moving_drones:
                destination = moving_drones[drone.id]
                if destination.type is not ZoneType.RESTRICTED:
                    occupancy[destination.name] += 1
            elif isinstance(drone.location, Transit):
                occupancy[drone.location.destination.name] += 1
            else:
                occupancy[drone.location.name] += 1

        for zone_name, count in occupancy.items():
            zone = self.graph.zones[zone_name]
            if count > self.graph.zone_capacity(zone):
                raise SimulationError(
                    f"{zone_name} has exceeded the allowed quota")

    def _check_connection_capacity(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> None:
        """Check if a connection would exceed its capacity on a turn."""
        passage: Counter[str] = Counter()
        links: dict[str, Connection] = {}
        for _, connection, _ in planned:
            passage[connection.name] += 1
            links[connection.name] = connection

        for connection_name, count in passage.items():
            if count > links[connection_name].capacity:
                raise SimulationError(
                    f"{connection_name} has exceeded the allowed quota")

    def _apply(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> str:
        """Apply the planned moves and finish transits on the current turn.

        The location of the drones is updated according to the validated
        planned moves. If a drone is in transit, it reaches the destination
        on this turn. If the destination is restricted, the drone enters
        transit by moving to the bridge.
        """
        pairs: list[tuple[int, str]] = []
        for drone_id, drone in self.drones.items():
            if isinstance(drone.location, Transit):
                drone.finish_transit()
                if isinstance(drone.location, Zone):
                    pairs.append((drone_id, drone.location.name))
                else:
                    raise SimulationError("Issue during transit")
        for drone, link, destination in planned:
            if destination.type is ZoneType.RESTRICTED:
                drone.enter_transit(link)
                if isinstance(drone.location, Transit):
                    pairs.append((drone.id, link.name))
                else:
                    raise SimulationError("Issue trying to engage transit")
            else:
                drone.move_location(link)
                if drone.location is destination:
                    pairs.append((drone.id, destination.name))
                else:
                    raise SimulationError("Issue during movement")
        pairs.sort()
        return " ".join(f"D{drone_id}-{name}" for drone_id, name in pairs)

    def snapshot(self) -> dict[int, Zone | Connection]:
        """Return each drone's current location"""
        result: dict[int, Zone | Connection] = {}
        for id, drone in self.drones.items():
            if isinstance(drone.location, Transit):
                result[id] = drone.location.connection
            else:
                result[id] = drone.location
        return result

    def drone_route(self) -> None:
        for id, drone in self.drones.items():
            if isinstance(drone.location, Zone):
                self.route[id].append(drone.location.name)
            else:
                self.route[id].append(drone.location.connection.name)

    def step(self, moves: dict[int, Connection]) -> str:
        """Check moves legality, zone and connection capacity on one turn."""
        planned = self._check_moves(moves)
        self._check_zone_capacity(planned)
        self._check_connection_capacity(planned)
        result = self._apply(planned)
        self.turn += 1
        return result

    def run(
            self,
            visual: bool,
            moves_per_turn: list[dict[int, Connection]],
            display: Callable[["Simulation"], None],
            snapshots: list[dict[int, Zone | Connection]]
    ) -> tuple[int, list[str]]:
        """Play a whole plan and check if all drones are delivered.

        For every turn, the legality of the move and the capacities of
        zone and connection will be checked.

        Parameters
        ----------
        visual : bool
            Toggle colored terminal output or not.
        moves_per_turn : list[dict[int, Connection]]
            One moves dictionary per turn.
        display : callable
            Called after each turn to display colored output on terminal.

        Returns
        -------
        tuple[int, list[str]]
            The number of turns and the output lines per turn.
        """
        result: list[str] = []
        if visual:
            print(f"Turn {self.turn}:", file=sys.stderr)
            display(self)
            print(file=sys.stderr)
        for turn in moves_per_turn:
            this_turn = self.step(turn)
            snapshots.append(self.snapshot())
            self.drone_route()
            result.append(this_turn)
            if visual:
                print(f"Turn {self.turn}: {this_turn}", file=sys.stderr)
                display(self)
                print(file=sys.stderr)
        if not self.all_delivered:
            raise SimulationError("Some drones were not delivered")
        print(self.route)
        return (self.turn, result)
