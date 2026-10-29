import pygame
import sys
from parsing import MapParser, Zone, Connection
from graph import Graph
from main import define_flag
from simulation import Simulation
from planner import Planner
from terminal import TerminalColor
from graph import PathFinder


WHITE = (255,255,255)
PINK =  (255,192,203)

def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((1500, 800))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Fly-in")
    pygame.display.flip()
    background = pygame.image.load("background.png")


    flags = define_flag()
    path: str = flags.map_file
    parser = MapParser()
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
    terminal = TerminalColor()
    route = PathFinder(graph)
    test_path = route.find_path()
    max_time = (len(test_path) + graph.nb_drones) * 2
    turns = planner.plan(max_time)
    snapshots: list[dict[int, Zone | Connection]] = [simulation.snapshot()]
    result = simulation.run(flags.visual, turns, terminal.display_status, snapshots)

    drone_route = simulation.route
    running = True
    zone_pos = zone_position(graph, screen)
    current_turn = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
        screen.blit(background, (0, 0))
        display(zone_pos, graph, screen)
        if current_turn < len(drone_route):
            show_drones(drone_route, current_turn, screen, zone_pos)
        pygame.display.flip()
        clock.tick(30)
        current_turn +=  1
    pygame.quit()


def zone_position(graph: Graph, screen: pygame.Surface) -> dict[str, tuple[int, int]]:
    max_x = max(zone.x for zone in graph.zones.values())
    max_y = max(zone.y for zone in graph.zones.values())

    min_x = min(zone.x for zone in graph.zones.values())
    min_y = min(zone.y for zone in graph.zones.values())

    map_width = max(max_x - min_x, 1)
    map_height = max(max_y - min_y, 1)

    available_width, available_height = screen.get_size()
    margin = 100
    available_width -= margin*2
    available_height -= margin*2
    scale = round(min(
        (available_width / map_width,
         available_height / map_height)), 1)

    used_width = map_width * scale
    used_height = map_height * scale

    shift_x = margin + (available_width - used_width) / 2
    shift_y = margin + (available_height - used_height) / 2

    zone_pos: dict[str, tuple[int, int]] = {}
    for zone in graph.zones.values():
        pos_x = shift_x + (zone.x - min_x) * scale
        pos_y = shift_y + used_height - (zone.y - min_y) * scale
        zone_pos[zone.name] = (int(pos_x), int(pos_y))
    return zone_pos


def display(
        zone_pos: dict[str, tuple[int, int]],
        graph: Graph,
        screen: pygame.Surface
) -> None:
    for connection in graph.connections:
        departure: tuple[int, int] = zone_pos[connection.zone_a.name]
        arrival = zone_pos[connection.zone_b.name]
        pygame.draw.line(
            screen,
            WHITE,
            departure,
            arrival,
            3
        )
    for pos_x, pos_y in zone_pos.values():
        pygame.draw.circle(
            screen,
            (0,0,250),
            (int(pos_x), int(pos_y)),
            20
        )


def show_drones(
        drone_route: dict[int, list[str]],
        current_turn: int,
        screen: pygame.Surface,
        zone_pos: dict[str, tuple[int, int]]
) -> None:
    velocity = 10
    for id in drone_route.keys():
        loc_name = drone_route[id][current_turn]
        if loc_name.find("-") == -1:
            x, y = zone_pos[loc_name]
            pygame.draw.rect(
                screen,
                PINK,
                (x,y,10,10)
            )
            destination_name = drone_route[id][current_turn + 1]
            x2, y2 = zone_pos[destination_name]
            while x <= x2 and y <= y2:
                x += velocity
                y += velocity
                pygame.draw.rect(
                    screen,
                    PINK,
                    (x,y,10,10)
                )
        else:
            zone_a, zone_b = loc_name.split("-")
            x1, y1 = zone_pos[zone_a]
            x2, y2 = zone_pos[zone_b]
            x = (x1 + x2)/2
            y = (y1 + y2)/2
            pygame.draw.rect(
                screen,
                PINK,
                (x,y,5,5)
            )


if __name__ == "__main__":
    main()
