from drones import Drone, Transit
from parsing import Zone, Connection
from graph import Graph
from collections import Counter


class Simulation:
    def __init__(
            self,
            graph: Graph
    ) -> None:
        self.turn: int = 0
        self.drones: list[Drone] = [
            Drone(i, self.graph.start, self.graph.end)
            for i in range(1, self.graph.nb_drones + 1)
        ]
        self.graph = graph

    @property
    def all_delivered(self) -> bool:
        return self.graph.end.capacity == len(self.drones)

    def step(self, moves: dict[int, Connection])
