import sys
from parsing import ParserError, MapParser, Connection
from graph import Graph, PathFinder
from simulation import SimulationError, Simulation
from planner import ReservationTable, Planner, PlanningError
from terminal import TerminalColor


def main() -> None:
    parameters = sys.argv
    if len(parameters) != 2:
        print(
            "Usage: python3 main.py <path to map file>",
            file=sys.stderr)
        sys.exit(1)
    path = parameters[1]
    parser = MapParser()
    try:
        parser.parse(path)
        graph = Graph(
            parser.zones,
            parser.connections,
            parser.start,
            parser.end,
            parser.nb_drones
        )
        simulation = Simulation(graph)
        planner = Planner(graph)
        bottleneck = graph.zones["bottleneck"]
        link = graph.connection_between(graph.start, bottleneck)
        print("Zone capacity:", graph.zone_capacity(bottleneck))
        print("Connection capacity:", link.capacity)
        table = ReservationTable(graph)
        table.book_zone(bottleneck, 1)
        table.book_connection(link, 1)
        print("zone free:", table.is_zone_free(bottleneck, 1))
        print("connection free:", table.is_connection_free(bottleneck, 1))
        planner = Planner(graph)
        for turn, zone, connection in planner._next_state(graph.start, 0, table):
            print(turn, zone.name, connection.name if connection else "Wait")
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


if __name__ == "__main__":
    main()
