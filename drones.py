from graph import Graph, PathFinder
from dataclasses import dataclass
from parsing import Zone, Connection


@dataclass(frozen=True)
class Transit:
    connection: Connection
    destination: Zone


class Drone:
    def __init__(
            self,
            drone_id: int,
            start: Zone,
            end: Zone
    ) -> None:
        self.id = drone_id
        self.location: Zone | Transit = start
        self.end = end

    @property
    def name(self) -> str:
        return f"D{self.id}"

    @property
    def is_delivered(self) -> bool:
        return self.location is self.end

    def move_location(self, link: Connection) -> None:
        if not isinstance(self.location, Zone):
            raise ValueError(f"Drone {self.name} is not in a zone")
        if not self.location is link.zone_a and not self.location is not link.zone_b:
            raise ValueError(f"Drone {self.name} is currently not on either end of that link")
        self.location = link.other_zone(self.location)

    def enter_transit(self, link: Connection) -> None:
        if self.location is link.zone_a or self.location is link.zone_b:
            self.location = Transit(link, link.other_zone(self.location))
        elif not isinstance(self.location, Zone):
            raise ValueError(f"Drone {self.name} is already in transit")
        else:
            raise ValueError(f"Drone {self.name} is currently not on either end of that link")

    def finish_transit(self) -> None:
        match self.location:
            case Transit(_, destination):
                self.location = destination
            case _:
                raise ValueError(f"Drone {self.name} currently not in transit")





