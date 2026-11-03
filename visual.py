"""Graphical interface to visualize the drones routing on the graph."""

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from graph import Graph
from parsing import Zone, Connection, ZoneType

Location = Zone | Connection
Snapshot = dict[int, Location]
Point = tuple[float, float]

BACKGROUND = (25, 25, 35)
LINE = (200, 200, 200)
TEXT = (235, 235, 235)
DEFAULT_ZONE = (128, 128, 128)
PRIORITY = (34, 139, 34)
RESTRICTED = (255, 165, 0)
BLOCKED = (255, 0, 0)
DRONE = (255, 192, 203)


class GraphicalDisplay:
    """Window displaying recorded snapshots of the drones at each turn.

    Attributes
    ----------
    graph: Graph
        The network to be displayed.
    snapshots: list[Snapshot]
        Each drones location after 0, 1, 2... turns
    """

    MARGIN = 80
    ZONE_RADIUS = 20
    DRONE_SIZE = 24
    TURN_DELAY = 800

    def __init__(
            self,
            graph: Graph,
            snapshots: list[Snapshot]
    ) -> None:
        """Open the window, initialize pygame and every constant."""
        pygame.init()

        self.screen = pygame.display.set_mode((1500, 800))
        pygame.display.set_caption("Fly-in")
        self.background = pygame.image.load("assets/background.png")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 30)

        self.graph = graph
        self.snapshots = snapshots

        self.zone_pos = self._compute_zone_positions()
        self.zone_colors = {
            name: self._extract_color(zone.color)
            for name, zone in graph.zones.items()
        }
        self.drone_image = self._load_drone_image("assets/drone.png")

    def _compute_zone_positions(self) -> dict[str, Point]:
        """Define the zone's coordinate inside the window."""
        zones = self.graph.zones.values()
        min_x = min(zone.x for zone in zones)
        max_x = max(zone.x for zone in zones)
        min_y = min(zone.y for zone in zones)
        max_y = max(zone.y for zone in zones)

        width, height = self.screen.get_size()
        available_width = width - (self.MARGIN * 2)
        available_height = height - (self.MARGIN * 2)

        scale = min(
            available_width / max(max_x - min_x, 1),
            available_height / max(max_y - min_y, 1)
        )

        used_width = (max_x - min_x) * scale
        used_height = (max_y - min_y) * scale
        offset_x = self.MARGIN + (available_width - used_width) / 2
        offset_y = self.MARGIN + (available_height - used_height) / 2

        return ({
            zone.name: (
                offset_x + (zone.x - min_x) * scale,
                offset_y + used_height - (zone.y - min_y) * scale
            )
            for zone in zones
        })

    @staticmethod
    def _extract_color(name: str | None) -> pygame.Color:
        """Extract the actual color, defaulting to gray otherwise."""
        if name is None:
            return pygame.Color(DEFAULT_ZONE)
        try:
            return pygame.Color(name)
        except ValueError:
            return pygame.Color(DEFAULT_ZONE)

    def _load_drone_image(self, path: str) -> pygame.Surface | None:
        """Load drone image and resize it."""
        try:
            image = pygame.image.load(path).convert_alpha()
        except (FileNotFoundError, PermissionError):
            return None
        size = (self.DRONE_SIZE, self.DRONE_SIZE)
        return pygame.transform.smoothscale(image, size)

    def _location_pos(self, location: Location) -> Point:
        """Center of a zone, or middle of a connection."""
        if isinstance(location, Zone):
            return self.zone_pos.get(location.name)
        x1, y1 = self.zone_pos.get(location.zone_a.name)
        x2, y2 = self.zone_pos.get(location.zone_b.name)
        return ((x2 + x1) / 2, (y2 + y1) / 2)

    def _drone_positions(self, snapshot: Snapshot) -> dict[int, Point]:
        """Define position of each drone, arranging drone sharing a zone."""
        groups: dict[str, list[int]] = {}
        for id in sorted(snapshot):
            location_name = snapshot[id].name
            if location_name not in groups:
                groups[location_name] = []
            groups[location_name].append(id)

        positions: dict[int, Point] = {}
        spacing = self.DRONE_SIZE * 0.6
        for ids in groups.values():
            x, y = self._location_pos(snapshot[ids[0]])
            first = x - spacing * (len(ids) - 1) / 2
            for index, id in enumerate(ids):
                positions[id] = (first + index * spacing, y)
        return positions

    @staticmethod
    def _decompose_movement(
        start: Point,
        end: Point,
        progress: float
    ) -> Point:
        return (
            start[0] + (end[0] - start[0]) * progress,
            start[1] + (end[1] - start[1]) * progress
        )

    def _draw_map(self) -> None:
        """Draw the connections and the zones with label on top."""
        for link in self.graph.connections:
            start = self.zone_pos[link.zone_a.name]
            end = self.zone_pos[link.zone_b.name]
            pygame.draw.line(self.screen, LINE, start, end, 3)
        for name, (x, y) in self.zone_pos.items():
            center = (round(x), round(y))
            pygame.draw.circle(
                self.screen,
                self.zone_colors[name],
                center,
                self.ZONE_RADIUS
            )
            zone = self.graph.zones[name]
            if zone.is_priority:
                pygame.draw.circle(
                    self.screen,
                    PRIORITY,
                    center,
                    self.ZONE_RADIUS + 10,
                    5
                )
            if zone.type is ZoneType.RESTRICTED:
                pygame.draw.circle(
                    self.screen,
                    RESTRICTED,
                    center,
                    self.ZONE_RADIUS + 10,
                    5
                )
            if zone.type is ZoneType.BLOCKED:
                pygame.draw.circle(
                    self.screen,
                    BLOCKED,
                    center,
                    self.ZONE_RADIUS + 10,
                    5
                )
            label = self.font.render(name, True, TEXT)
            self.screen.blit(
                label, label.get_rect(midtop=(
                    center[0],
                    center[1] + 31
                ))
            )

    def _draw_drones(
            self, before: Snapshot, after: Snapshot, progress: float
    ) -> None:
        """Draw every drone between two snapshot positions."""
        start = self._drone_positions(before)
        end = self._drone_positions(after)
        for id, start_pos in start.items():
            x, y = self._decompose_movement(
                start_pos, end[id], progress
            )
            center = (round(x), round(y))
            if self.drone_image is not None:
                rect = self.drone_image.get_rect(center=center)
                self.screen.blit(self.drone_image, rect)
            else:
                rect = pygame.Rect(0, 0, 10, 10)
                rect.center = center
                pygame.draw.rect(self.screen, DRONE, rect)

    def _draw_frame(
            self, turn: int, next_turn: int, progress: float, paused: bool
    ) -> None:
        """Draw one complete frame and update the screen."""
        self.screen.blit(self.background, (0, 0))
        self._draw_map()
        self._draw_drones(
            self.snapshots[turn],
            self.snapshots[next_turn],
            progress
        )
        last = len(self.snapshots) - 1
        status = f"Turn {turn}/{last}" + (" (PAUSED)" if paused else "")
        self.screen.blit(
            self.font.render(status, True, TEXT),
            (15, 15)
        )
        pygame.display.flip()

    def run(self) -> None:
        """Play every frames until the windows is closed."""
        turn = 0
        last = len(self.snapshots) - 1
        paused = False
        last_change = pygame.time.get_ticks()
        running = True

        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            running = False
                        case pygame.K_SPACE:
                            paused = not paused
                        case pygame.K_RIGHT:
                            turn = min(turn + 1, last)
                        case pygame.K_LEFT:
                            turn = max(turn - 1, 0)
                    last_change = now  # restart current move

            if paused:
                last_change = now  # keep the progress at zero
            progress = min(
                (now - last_change) / self.TURN_DELAY,
                1.0
            )
            if progress >= 1.0 and turn < last:
                turn += 1
                last_change = now
                progress = 0.0

            next_turn = min(turn + 1, last)
            self._draw_frame(turn, next_turn, progress, paused)
            self.clock.tick(60)
        pygame.quit()
