from drones import Drone, Transit
from parsing import Zone, Connection
from graph import Graph


class Simulation:
    def __init__(
            self,
            graph: Graph
    ) -> None:
        self.turns: int = 0
        self.drones: list[Drone] | None = None
        self.graph = graph

    def _make_drones(self) -> None:
        self.drones = [
            Drone(i, self.graph.start, self.graph.end)
            for i in range(1, self.graph.nb_drones + 1)
        ]

    def run(self) -> None:
        self._make_drones()
