import sys
from parsing import ParserError, MapParser
from graph import Graph


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
            linked_name = [f"{connection.zone_a.name}-{connection.zone_b.name}"
                           for connection in linked]
            print(f"{zone.name}: {linked_name}")
    except OSError as o:
        print(f"Unable to read map file: {o}", file=sys.stderr)
        sys.exit(1)
    except ParserError as p:
        print(p, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

