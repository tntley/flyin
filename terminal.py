"""Display a colored terminal output as an alternative to graphical display."""

from simulation import Simulation
from drones import Transit
from parsing import Zone, ZoneType
import sys


class TerminalColor:
    """Put together a turn by turn colored simulation output.

    Each drone's movements and each zone's state for each turned are
    showed with the specified color for each zones. If the color is not
    in store, the zone appears as default.
    """

    COLORS = {
        "red": "\033[31m",
        "orange": "\033[38;5;136m",
        "yellow": "\033[33m",
        "green": "\033[32m",
        "blue": "\033[34m",
        "purple": "\033[38;5;63m"
    }

    RESET = "\033[0m"
    UNDERLINED = "\033[4m"
    BOLD = "\033[1m"

    def _paint(
            self,
            color: str | None,
            full: bool,
            priority: bool,
            text: str
    ) -> str:
        """Apply color and other style to the zone name.

        Parameters
        ----------
        color : str | None
            Color from the map file metadata.
        full : bool
            The zone is at full capacity on this turn.
        priority : bool
            The zone is a priority one.
        text : str
            The zone name to be styled and displayed.
        """
        prefix = ""
        if color in self.COLORS:
            prefix += self.COLORS[color]
        if full:
            prefix += self.UNDERLINED
        if priority:
            prefix += self.BOLD
        if not sys.stderr.isatty() or color not in self.COLORS:
            return text
        return prefix + text + self.RESET

    def display_status(self, simulation: Simulation) -> None:
        """Print each zone's color, occupancy and neighbor to stderr.

        Full zones are underlined, priority zones are bold, blocked zones
        are marked as such, and drones in transit are listed at the end.

        Parameters
        ----------
        simulation : Simulation
            The simulation whose current state is shown.
        """
        in_zone: dict[str, list[str]] = {}
        in_transit: list[str] = []
        for drone in simulation.drones.values():
            match drone.location:
                case Transit(link, _):
                    in_transit.append(f"{drone.name} on {link.name}")
                case Zone():
                    if drone.location.name not in in_zone:
                        in_zone[drone.location.name] = []
                    in_zone[drone.location.name].append(drone.name)

        padding = max(
            len(zone_name) for zone_name in simulation.graph.zones.keys()
            ) + len(" (restricted)")

        for zone_name, zone in simulation.graph.zones.items():
            drones_here = in_zone.get(zone_name, [])
            indicator = (f"{len(drones_here)}/"
                         f"{simulation.graph.zone_capacity(zone)}")
            full: bool = len(
                drones_here) == simulation.graph.zone_capacity(zone)
            priority: bool = zone.is_priority
            text = (
                zone.name +
                (" (restricted)" if zone.type is ZoneType.RESTRICTED else ""))

            print(self._paint(
                zone.color,
                full,
                priority,
                f"{text:<{padding}}"), file=sys.stderr, end="\t")

            if not simulation.graph.can_enter(zone):
                print("Blocked", file=sys.stderr)
                continue
            print(f"{indicator:<7}", end="", file=sys.stderr)
            list_drones = ", ".join(drones_here)
            second_padding = len(simulation.drones)*5
            print(f"{list_drones:<{second_padding}}", end="", file=sys.stderr)
            connections_of = simulation.graph.connections_of(zone)
            if zone is not simulation.graph.end:
                # print(
                # f"-> {', '.join(connection.other_zone(zone).name
                #  for connection in connections_of)}")
                for i, link in enumerate(connections_of):
                    destination = link.other_zone(zone)
                    text = self._paint(
                        destination.color,
                        False,
                        destination.is_priority,
                        destination.name
                    )
                    if i == len(connections_of) - 1:
                        print(text, file=sys.stderr)
                    else:
                        print(f"{text}, ", end="", file=sys.stderr)
            else:
                print(file=sys.stderr)

        for transit in in_transit:
            print("\t*", transit, file=sys.stderr)
