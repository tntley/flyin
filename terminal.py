from simulation import Simulation
from drones import Transit
from parsing import Zone, ZoneType
import sys

class TerminalColor:

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

    def _paint(self, color: str | None, full: bool, priority: bool, text : str) -> str:
        if color in self.COLORS and sys.stdout.isatty() :
            if full and priority:
                return (self.UNDERLINED + self.BOLD + self.COLORS[color] + text + self.RESET)
            elif full:
                return self.UNDERLINED + self.COLORS[color] + text + self.RESET
            elif priority:
                return self.BOLD + self.COLORS[color] + text + self.RESET
            return self.COLORS[color] + text + self.RESET
        elif full:
            return (self.UNDERLINED + text + self.RESET)
        return text

    def display_status(self, simulation: Simulation) -> None:
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

        padding = max(len(zone_name) for zone_name in simulation.graph.zones.keys()) + len(" (restricted)")

        for zone_name, zone in simulation.graph.zones.items():
            drones_here = in_zone.get(zone_name, [])
            indicator = f"{len(drones_here)}/{simulation.graph.zone_capacity(zone)}"
            full: bool = len(drones_here) == simulation.graph.zone_capacity(zone)
            priority: bool = zone.is_priority
            text = zone.name + (" (restricted)" if zone.type is ZoneType.RESTRICTED else "")

            print(self._paint(
                zone.color,
                full,
                priority,
                f"{text:<{padding}}"), end="\t")

            if not simulation.graph.can_enter(zone):
                print("Blocked")
                continue
            print(f"{indicator:<7}", end="")
            list_drones = ", ".join(drones_here)
            second_padding = len(simulation.drones)*5
            print(f"{list_drones:<{second_padding}}", end="")
            connections_of = simulation.graph.connections_of(zone)
            if zone is not simulation.graph.end:
                # print(f"-> {', '.join(connection.other_zone(zone).name for connection in connections_of)}")
                for i, link in enumerate(connections_of):
                    destination = link.other_zone(zone)
                    text = self._paint(
                        destination.color,
                        False,
                        destination.is_priority,
                        destination.name
                    )
                    if i == len(connections_of) - 1:
                        print(text)
                    else:
                        print(f"{text}, ", end="")
            else:
                print()

        for transit in in_transit:
            print("\t*", transit)
