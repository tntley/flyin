"""Entry point: loads arguments from tty and instantiate everything."""

import sys
from parsing import ParserError, MapParser, Zone, Connection
from graph import Graph, PathFinder
from simulation import SimulationError, Simulation
from planner import Planner, PlanningError
from terminal import TerminalColor
import argparse
import os


def main() -> None:
    """Run the program from graph creation to simulation."""
    param = argparse.ArgumentParser(
        description="Pathfinding for drones with constraints."
    )
    param.add_argument(
        "map_file",
        help="Pathway to the map file to run."
    )
    param.add_argument(
        "--visual",
        action="store_true",
        help="Toggle the optional colored terminal output"
    )
    param.add_argument(
        "--gui",
        action="store_true",
        help="Toggle the optional graphical user interface."
    )
    flags = param.parse_args()

    visual: bool = flags.visual
    gui: bool = flags.gui
    map_file: str = flags.map_file
    parser = MapParser()
    try:
        parser.parse(map_file)

        if parser.start is None or parser.end is None:
            raise ParserError(0, "missing starting or ending zone")
        graph = Graph(
            parser.zones,
            parser.connections,
            parser.start,
            parser.end,
            parser.nb_drones
        )

        simulation = Simulation(graph)

        planner = Planner(graph)
        display = TerminalColor()

        path = PathFinder(graph)

        test_path = path.find_path()
        if test_path is None:
            raise ValueError("No route found.")
        max_time = (len(test_path) + graph.nb_drones) * 2
        turns = planner.plan(max_time)

        capture: dict[int, Zone | Connection] = simulation.snapshot()

        snapshots: list[dict[int, Zone | Connection]] = [capture]

        result = simulation.run(
            visual, turns, display.display_status, snapshots)
        for line in result[1]:
            print(line)
        if gui:
            os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
            from visual import GraphicalDisplay
            graphic = GraphicalDisplay(graph, snapshots)
            graphic.run()
    except OSError as o:
        print(f"Unable to read map file: {o}", file=sys.stderr)
        sys.exit(1)
    except ValueError as v:
        print(v, file=sys.stderr)
        sys.exit(1)
    except ParserError as p:
        print(p, file=sys.stderr)
        sys.exit(1)
    except SimulationError as s:
        print(s, file=sys.stderr)
        sys.exit(1)
    except PlanningError as t:
        print(t, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Program interrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
