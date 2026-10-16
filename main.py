import sys
from parsing import ParserError, MapParser, Connection
from graph import Graph, PathFinder
from simulation import SimulationError, Simulation
from planner import ReservationTable, Planner


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
        for name, zone in parser.zones.items():
            print(f"{name}: {zone}")
        print()
        for link in parser.connections:
            print(link)
        graph = Graph(
            parser.zones,
            parser.connections,
            parser.start,
            parser.end,
            parser.nb_drones
        )
        print()
        for zone in parser.zones.values():
            linked = graph.connections_of(zone)
            linked_name = [
                connection.name for connection in linked]
            print(f"{zone.name}: {linked_name}")
        print()
        print(graph.zones)

        # the following is a separated test for Simulation class
        print()
        simulation = Simulation(graph)
        test_simulation(graph, simulation)

        # testing the planner
        print()
        planner = Planner(graph)
        table = ReservationTable(graph)
        options = planner._next_state(graph.zones["waypoint1"], 1, table)
        for time, next_zone, link in options:
            print(time, next_zone.name, link.name if link else "Wait")
        table.book_zone(graph.zones["waypoint1"], 1)
        print("manually booking waypoint1")
        options = planner._next_state(graph.start, 0, table)
        for time, next_zone, link in options:
            print(time, next_zone.name, link.name if link else "Wait")


        # path = PathFinder(graph)
        # final = path.find_path()
        # final_name = [zone.name for zone in final]
        # print(final_name)
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


def test_simulation(graph: Graph, simulation: Simulation) -> None:
    # the following is a separated test for Simulation class
    start = graph.zones["start"]
    waypoint1 = graph.zones["waypoint1"]
    waypoint2 = graph.zones["waypoint2"]
    goal = graph.zones["goal"]
    moves = [
        {1: graph.connection_between(start, waypoint1)},
        {1: graph.connection_between(waypoint1, waypoint2),
         2: graph.connection_between(start, waypoint1)},
        {2: graph.connection_between(waypoint1, waypoint2)},
        {1: graph.connection_between(waypoint2, goal)},
        {2: graph.connection_between(waypoint2, goal)}
    ]
    result = simulation.run(moves)
    print(f"Number of turn: {result[0]}")
    for line in result[1]:
        print(line)


if __name__ == "__main__":
    main()

