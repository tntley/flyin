from simulation import Simulation
from drones import Transit
from parsing import Zone
import sys


COLORS = {
    "red": "\033[31m",
    "orange": "\033[38;5;136m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "blue": "\033[34m",
    "purple": "\033[38;5;63m"
}

RESET = "\033[0m"

def paint(color: str | None, text : str) -> str:
    if color in COLORS and sys.stdout.isatty():
        return (COLORS[color] + text + RESET)
    else:
        return text


def display_status(simulation: Simulation) -> None:
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

    padding = max(len(zone_name) for zone_name in simulation.graph.zones.keys())

    for zone_name, zone in simulation.graph.zones.items():
        print(paint(zone.color, f"{zone_name:<{padding}}"), end="\t")

        drones_here = in_zone.get(zone_name, [])
        indicator = f"{len(drones_here)}/{simulation.graph.zone_capacity(zone)}"
        if not simulation.graph.can_enter(zone):
            print("Blocked")
            continue
        print(f"{indicator:<7}", end="")
        print(drones_here)
    for transit in in_transit:
        print(transit)


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

    def _paint(self, color: str | None, full: bool, text : str) -> str:
        if color in self.COLORS and sys.stdout.isatty() :
            return (self.UNDERLINED + self.COLORS[color] + text + self.RESET if full
                    else self.COLORS[color] + text + self.RESET)
        elif full :
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

        padding = max(len(zone_name) for zone_name in simulation.graph.zones.keys())

        for zone_name, zone in simulation.graph.zones.items():
            drones_here = in_zone.get(zone_name, [])
            indicator = f"{len(drones_here)}/{simulation.graph.zone_capacity(zone)}"
            full: bool = len(drones_here) == simulation.graph.zone_capacity(zone)

            print(self._paint(zone.color, full, f"{zone_name:<{padding}}"), end="\t")

            if not simulation.graph.can_enter(zone):
                print("Blocked")
                continue
            print(f"{indicator:<7}", end="")
            print(drones_here)
        for transit in in_transit:
            print("\t*", transit)
