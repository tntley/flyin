"""Create Drone objects based on parsed data from the map file."""

from dataclasses import dataclass
from parsing import Zone, Connection


@dataclass(frozen=True)
class Transit:
    """Drone's position while it travels on a link between two zones.

    Entering a restricted zone requires 2 turns, the drone will spend
    the first of those on the connection, and reaches the other end
    on the next turn.
    The object is frozen because the transit cannot change midway, it's
    fixed and can't be changed from the outside.

    Attributes
    ----------
    connection : Connection
        The connection it's currently on in etween two zones.
    destination : Zone
        The other end of the connection it will reach on the next turn.
    """

    connection: Connection
    destination: Zone


class Drone:
    """Describe the state of a drone, its name and its location.

    Attributes
    ----------
    drone_id : int
        Number between 1 and the max number of drones to id it.
    location : Zone | Transit, default start
        Drone is either locate in a zone or on transit, starts at the
        starting zone.
    end : Zone
        The ending zone to identify if it has arrived there yet.
    """

    def __init__(
            self,
            drone_id: int,
            start: Zone,
            end: Zone
    ) -> None:
        """Create a Drone object with its id.

        Parameters
        ----------
        drone_id :
            Number between 1 and the max number of drones to id it.
        start : Zone
            The drone starts its journey here.
        end : Zone
            The drone ends its journey here.
        """
        self.id = drone_id
        self.location: Zone | Transit = start
        self.end = end

    @property
    def name(self) -> str:
        """Name the drone as its id prefixed by 'D'.

        Returns
        -------
        str
            The name of the drone.
        """
        return f"D{self.id}"

    @property
    def is_delivered(self) -> bool:
        """Check whether the drone has arrived to the end."""
        return self.location is self.end

    def move_location(self, link: Connection) -> None:
        """Update the location of the drone.

        Parameters
        ----------
        link : Connection
            Bridge the drone is taking from a zone to the other end.
        """
        if not isinstance(self.location, Zone):
            raise ValueError(f"Drone {self.name} is not in a zone")
        if (
            self.location is not link.zone_a
            and self.location is not link.zone_b
        ):
            raise ValueError(
                f"Drone {self.name} is currently not"
                " on either end of that link")
        self.location = link.other_zone(self.location)

    def enter_transit(self, link: Connection) -> None:
        """Move the drone's location from a zone to a bridge connected to it.

        If the drone is heading to a restricted zone, it spends its first
        turn of two on the bridge.

        Parameters
        ----------
        link : Connection
            Bridge the drone is taking from a zone to the other end.
        """
        if self.location is link.zone_a or self.location is link.zone_b:
            self.location = Transit(link, link.other_zone(self.location))
        elif not isinstance(self.location, Zone):
            raise ValueError(f"Drone {self.name} is already in transit")
        else:
            raise ValueError(
                f"Drone {self.name} is currently not"
                "on either end of that link")

    def finish_transit(self) -> None:
        """Move the drone's location from the bridge to the other end of it."""
        match self.location:
            case Transit(_, destination):
                self.location = destination
            case _:
                raise ValueError(f"Drone {self.name} currently not in transit")
