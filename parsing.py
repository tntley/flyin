from enum import Enum
from dataclasses import dataclass


class ParserError(Exception):
    def __init__(
            self,
            line_no: int,
            message: str
    ) -> None:
        self.line_no = line_no
        super().__init__(f"Error on line {self.line_no}: {message}")


def parse_file() -> None:
    try:
        with open("./maps/easy/01_linear_path.txt", "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print(f"line {line_no}: {line.rstrip()}")
                    scan_line(line_no, stripped)
    except (FileNotFoundError, PermissionError):
        print("Invalid file: inaccessible or inexistent")
    except ParserError as p:
        print(p)


def scan_line(
        line_no: int,
        line: str
) -> None:
    label, sep, interest = line.partition(":")
    if not sep:
        raise ParserError(line_no, "missing ':' after label")
    match label.strip():
        case "nb_drones":
            body, forbidden = split_from_metadata(line_no, interest)
            if forbidden is not None:
                raise ParserError(line_no, "metadata forbidden here")
            if len(body.split()) != 1:
                raise ParserError(line_no, "expected one number only")
        case "start_hub" | "hub" | "end_hub":
            body, final_metadata = process_line_content(
                line_no,
                interest,
                expected_number=3,
                message_content="name x y"
            )
        case "connection":
            body, final_metadata = process_line_content(
                line_no,
                interest,
                expected_number=1,
                message_content="zone-zone"
            )
        case _:
            raise ParserError(line_no, f"unknown type '{label.strip()}'")


def process_line_content(
        line_no: int,
        interest: str,
        expected_number: int,
        message_content: str
) -> tuple[str, dict[str, str]]:
    body, metadata = split_from_metadata(line_no, interest)
    if len(body.split()) != expected_number:
        raise ParserError(line_no, f"line should be formatted as {message_content}")
    final_metadata = read_optional_metadata(line_no, metadata)
    if final_metadata:
        print(final_metadata)
    return (body, final_metadata)


def split_from_metadata(
        line_no: int,
        interest: str
) -> tuple[str, str | None]:
    opening = interest.find("[")
    ending = interest.find("]")
    if opening == -1 and ending == -1:
        return (interest, None)
    else:
        if interest.count("[") != interest.count("]"):
            raise ParserError(line_no, f"missing pair bracket")
        if not interest.endswith("]"):
            raise ParserError(line_no, f"garbage value")
        if interest.count("[") != 1 or interest.count("]") != 1:
            raise ParserError(line_no, f"too many brackets")
    return (interest[:opening], interest[opening+1:ending])


def read_optional_metadata(
        line_no: int,
        metadata: str | None
) -> dict[str, str]:
    if metadata is None:
        return {}
    return parsing_metadata(line_no, metadata)


def parsing_metadata(
        line_no: int,
        content: str
) -> dict[str, str]:
    result: dict[str, str] = {}
    content = content.strip()
    if not content:
        raise ParserError(line_no, "empty brackets")
    subparts = content.split()
    for part in subparts:
        if "=" in part:
            key, _, value = part.partition("=")
            if not key or not value:
                raise ParserError(line_no, "missing key/value")
            elif key in result:
                raise ParserError(line_no, "duplicate metadata detected")
            result[key] = value
        else:
            raise ParserError(line_no, "malformed metadata")
    return result


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:

    name: str
    x: int
    y: int
    type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    capacity: int = 1
    start: bool = False
    end: bool = False

    @property
    def entry_cost(self) -> int:
        match self.type.value:
            case "blocked":
                raise ValueError("this zone is inaccessible")
            case "restricted":
                return 2
            case "normal" | "priority":
                return 1

    @property
    def is_priority(self) -> bool:
        return self.type is ZoneType.PRIORITY


@dataclass
class Connection:

    zone_a: Zone
    zone_b: Zone
    capacity: int = 1

    def other_zone(self, zone: Zone) -> Zone:
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        else:
            raise ValueError(f"{zone.name} is not part of this link")

    @property
    def name(self) -> str:
        return f"{self.zone_a.name}-{self.zone_b.name}"


class MapParser:

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start: Zone | None = None
        self.end: Zone | None = None
        self.links: set[frozenset[str]] = set()

    def parse(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print(f"line {line_no}: {line.rstrip()}")
                    self._scan_line(line_no, stripped)
        self._final_check()

    def _scan_line(
            self,
            line_no: int,
            line: str
    ) -> None:
        label, sep, interest = line.partition(":")
        if not sep:
            raise ParserError(line_no, "missing ':' after label")
        if self.nb_drones is None and label.strip() != "nb_drones":
            raise ParserError(line_no, "the first line should be nb_drones")
        match label.strip():
            case "nb_drones":
                self._parse_nb_drones(line_no, interest)
            case "start_hub" | "hub" | "end_hub":
                self._parse_zone(line_no, label, interest)
            case "connection":
                self._parse_connection(line_no, interest)

            case _:
                raise ParserError(line_no, f"unknown type '{label.strip()}'")

    def _process_line_content(
            self,
            line_no: int,
            interest: str,
            expected_number: int,
            message_content: str
    ) -> tuple[list[str], dict[str, str]]:
        body, metadata = self._split_from_metadata(line_no, interest)
        if len(body.split()) != expected_number:
            raise ParserError(line_no, f"line should be formatted as {message_content}")
        final_metadata = self._read_optional_metadata(line_no, metadata)
        if final_metadata:
            print(final_metadata)
        return (body.split(), final_metadata)

    @staticmethod
    def _split_from_metadata(
            line_no: int,
            interest: str
    ) -> tuple[str, str | None]:
        opening = interest.find("[")
        ending = interest.find("]")
        if opening == -1 and ending == -1:
            return (interest, None)
        else:
            if interest.count("[") != interest.count("]"):
                raise ParserError(line_no, f"missing pair bracket")
            if not interest.endswith("]"):
                raise ParserError(line_no, f"garbage value")
            if interest.count("[") != 1 or interest.count("]") != 1:
                raise ParserError(line_no, f"too many brackets")
        return (interest[:opening], interest[opening+1:ending])

    def _read_optional_metadata(
            self,
            line_no: int,
            metadata: str | None
    ) -> dict[str, str]:
        if metadata is None:
            return {}
        return self._parsing_metadata(line_no, metadata)

    @staticmethod
    def _parsing_metadata(
            line_no: int,
            content: str
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        content = content.strip()
        if not content:
            raise ParserError(line_no, "empty brackets")
        subparts = content.split()
        for part in subparts:
            if "=" in part:
                key, _, value = part.partition("=")
                if not key or not value:
                    raise ParserError(line_no, "missing key/value")
                elif key in result:
                    raise ParserError(line_no, "duplicate metadata detected")
                result[key] = value
            else:
                raise ParserError(line_no, "malformed metadata")
        return result

    def _parse_nb_drones(
            self,
            line_no: int,
            interest: str
    ) -> None:
        body, forbidden = self._split_from_metadata(line_no, interest)
        if len(body.split()) != 1:
            raise ParserError(line_no, "expected one number only")
        if forbidden is not None:
            raise ParserError(line_no, "metadata forbidden here")
        if self.nb_drones:
            raise ParserError(line_no, "there should only be one nb_drones line")
        else:
            try:
                converted = int(body)
                if converted <= 0:
                    raise ParserError(line_no, "number should be greater than 0")
                self.nb_drones = converted
            except ValueError:
                raise ParserError(line_no, "invalid number")

    def _parse_zone(
            self,
            line_no: int,
            label: str,
            interest: str,
    ) -> None:
        body, final_metadata = self._process_line_content(
            line_no,
            interest,
            expected_number=3,
            message_content="name x y"
        )
        zone = self._build_zone(
            line_no,
            label,
            body,
            final_metadata
        )
        if zone.start:
            if self.start is None:
                self.start = zone
            else:
                raise ParserError(line_no, "there should be one start zone only")
        if zone.end:
            if self.end is None:
                self.end = zone
            else:
                raise ParserError(line_no, "there should be one end zone only")
        if zone.name not in self.zones:
            self.zones[zone.name] = zone
        else:
            raise ParserError(line_no, "duplicate zone")

    def _build_zone(
            self,
            line_no: int,
            label: str,
            body: list[str],
            metadata: dict[str, str]
    ) -> Zone:
        name, x, y = body
        if name.find("-") != -1:
            raise ParserError(line_no, "zone name contains forbidden dash")
        try:
            for value in (x, y):
                converted = int(value)
        except ValueError:
            raise ParserError(line_no, "coordinates should be integers")
        zone = Zone(name, int(x), int(y))
        if label == "start_hub":
            zone.start = True
        elif label == "end_hub":
            zone.end = True
        for key, value in metadata.items():
            match key:
                case "zone":
                    try:
                        zone.type = ZoneType(value)
                    except ValueError:
                        raise ParserError(line_no, f"unknown zone type: {value}")
                case "max_drones":
                    try:
                        converted = int(value)
                        if converted <= 0:
                            raise ParserError(
                                line_no,
                                "max drone number should be positive"
                            )
                        zone.capacity = converted
                    except ValueError:
                        raise ParserError(line_no, "max drone should be an int")
                case "color":
                    zone.color = value
                case _:
                    raise ParserError(line_no, "unknown metadata")
        return zone

    def _parse_connection(
            self,
            line_no: int,
            interest: str
    ) -> None:
        body, final_metadata = self._process_line_content(
            line_no,
            interest,
            expected_number=1,
            message_content="zone-zone"
        )
        linked = body[0]
        if linked.count("-") != 1:
            raise ParserError(line_no, "connection requires one dash only")
        zone_a, dash, zone_b = linked.partition("-")
        if not dash or not zone_b or not zone_a:
            raise ParserError(line_no, "malformed connection")
        if zone_a not in self.zones or zone_b not in self.zones:
            raise ParserError(line_no, "use only previously registered zones")
        if zone_a == zone_b:
            raise ParserError(line_no, "linked zones should be different")
        connection = Connection(
            self.zones[zone_a],
            self.zones[zone_b]
        )
        print(f"{zone_a} is linked to : {connection.other_zone(self.zones[zone_a]).name}")
        for key, value in final_metadata.items():
            match key:
                case "max_link_capacity":
                    try:
                        converted = int(value)
                        if converted <= 0:
                            raise ParserError(
                                line_no,
                                "max drone number should be positive"
                            )
                        connection.capacity = converted
                    except ValueError:
                        raise ParserError(
                            line_no,
                            "max drone should be an int"
                        )
                case _:
                    raise ParserError(line_no, "unknown metadata")
        if frozenset({zone_a, zone_b}) in self.links:
            raise ParserError(line_no, "duplicate connection detected")
        else:
            self.links.add(frozenset({zone_a, zone_b}))
        self.connections.append(connection)

    def _final_check(self) -> None:
        if self.start is None or self.end is None or self.nb_drones == 0:
            raise ParserError(0, "missing mandatory map component")


if __name__ == "__main__":
    # parse_file()
    parser = MapParser()
    parser.parse("./maps/easy/01_linear_path.txt")
    for name, zone in parser.zones.items():
        print(f"{name}: {zone}")
    print()
    for link in parser.connections:
        print(link)
