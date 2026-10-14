from drones import Drone, Transit
from parsing import Zone, Connection, ZoneType
from graph import Graph
from collections import Counter


class SimulationError(Exception):
    def __init__(
            self,
            message: str
    ) -> None:
        self.message = message
        super().__init__(f"Error during simulation: {self.message}")


class Simulation:
    def __init__(
            self,
            graph: Graph
    ) -> None:
        self.turn: int = 0
        self.graph = graph
        self.drones: dict[int, Drone] = {
            i: Drone(i, self.graph.start, self.graph.end)
            for i in range(1, self.graph.nb_drones + 1)
        }

    @property
    def all_delivered(self) -> bool:
        return all(drone.is_delivered for drone in self.drones.values())

    def _check_moves(
            self,
            moves: dict[int, Connection]
    ) -> list[tuple[Drone, Connection, Zone]]:
        result: list[tuple[Drone, Connection, Zone]] = []
        for drone_id, connection in moves.items():
            if drone_id not in self.drones:
                raise SimulationError(f"No drone with id {drone_id}")
            drone = self.drones[drone_id]

            if drone.is_delivered:
                raise SimulationError(f"{drone.name} already delivered")
            if isinstance(drone.location, Transit):
                raise SimulationError(f"{drone.name} is already in transit")
            if drone.location is not connection.zone_a and drone.location is not connection.zone_b:
                raise SimulationError(f"{drone.name} cannot take that connection")

            drone_destination = connection.other_zone(drone.location)
            if not self.graph.can_enter(drone_destination):
                raise SimulationError(f"{drone.name} cannot access the other end")
            result.append((drone, connection, drone_destination))
        return result

    def _check_zone_capacity(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> None:
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
                occupancy[drone.location.destination.name] +=1
            else:
                occupancy[drone.location.name] += 1

        for zone_name, count in occupancy.items():
            zone = self.graph.zones[zone_name]
            if count > self.graph.zone_capacity(zone):
                raise SimulationError(f"{zone_name} has exceeded the allowed quota")

    def _check_connection_capacity(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> None:
        passage: Counter[str] = Counter()
        links: dict[str, Connection] = {}
        for _, connection, _ in planned:
            passage[connection.name] +=1
            links[connection.name] = connection

        for connection_name, count in passage.items():
            if count > links[connection_name].capacity:
                raise SimulationError(f"{connection_name} has exceeded the allowed quota")

    def _apply(
            self,
            planned: list[tuple[Drone, Connection, Zone]]
    ) -> str:
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
                drone.enter_transit()
                if 



    def step(self, moves: dict[int, Connection]) -> str:
        planned = self._check_moves(moves)
        self._check_zone_capacity(planned)
        self._check_connection_capacity(planned)
        result = ""
        for drone, _, destination in planned:
            result += f"{drone.name}-{destination.name} "
        return result
