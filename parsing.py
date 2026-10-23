"""Parse Flyin map files into Zones, Connections objects and drone count."""


from enum import Enum
from dataclasses import dataclass


class ParserError(Exception):
    """Error raised when map file contains invalid data or is malformed.

    Attributes
    ----------
    line_no : int
        The line number where the error was found.
    message :str
        Custom message explaining the error found.
    """

    def __init__(
            self,
            line_no: int,
            message: str
    ) -> None:
        super().__init__(f"Error on line {line_no}: {message}")


class ZoneType(Enum):
    """Defined list of strings accepted as zone type."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:
    """A zone of the map, with every details describing it.

    Attributes
    ----------
    name : str
        Name of the zone, as defined in the map file.
    x : int
        Horizontal coordinate.
    y : int
        Vertical coordinate.
    type : ZoneType, default ZoneType.NORMAL
        Rules for entering the zone.
    color : str | None, default None
        The color of the zone, for representation purposes.
    capacity : int, default 1
        The maximum number of drones it can hold.
    start : bool, default False
        Indicates if the zone is the start.
    end : bool, default False
        Indicates if the zone is the end.
    """

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
        """Number of turns needed to enter this zone.

        Raises
        ------
        ValueError
            If the zone is blocked and inaccessible.
        """
        match self.type:
            case ZoneType.BLOCKED:
                raise ValueError("this zone is inaccessible")
            case ZoneType.RESTRICTED:
                return 2
            case ZoneType.NORMAL | ZoneType.PRIORITY:
                return 1

    @property
    def is_priority(self) -> bool:
        """Whether pathfinding should prioritize this zone."""
        return self.type is ZoneType.PRIORITY


@dataclass
class Connection:
    """A bidirectionnal connection between two zones of the map.

    Attributes
    ----------
    zone_a : Zone
        Zone at one end of the connection.
    zone_b : Zone
        Zone at the other end of the connection.
    capacity : int, default 1
        The maximum number of drones that can pass this link simultaneously.
    """

    zone_a: Zone
    zone_b: Zone
    capacity: int = 1

    def other_zone(self, zone: Zone) -> Zone:
        """Return the zone linked to a zone through this connection.

        Parameters
        ----------
        zone : Zone
            One of the two ends of this connection.

        Returns
        -------
        Zone
            The other end.

        Raises
        ------
        ValueError
            If the specified zone isn't part of this link.
        """
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        else:
            raise ValueError(f"{zone.name} is not part of this link")

    @property
    def name(self) -> str:
        """Unique name to identify the connection.

        This is formatted as the two zone names linked by a '-'.
        """
        return f"{self.zone_a.name}-{self.zone_b.name}"


class MapParser:
    """Class for storing all data exctracted from the parsed map file.

    Attributes
    ----------
    nb_drones : int, default 0
        The number of drones in action.
    zones : dict[str, Zone], default {}
        A name of the zone to Zone object dict.
    connections : list[Connection], default []
        A list of all the connections in the map.
    start : Zone | None, default None
        The starting zone of the map, as defined in the map file.
    end : Zone | None, default None
        The goal of the map, as defined in the map file.
    links : set[frozenset[str]], default set()
        Pairs of zone names forming one bidirectional connection.
    """

    def __init__(self) -> None:
        """Create the object to store all the valid data from map file."""
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start: Zone | None = None
        self.end: Zone | None = None
        self.links: set[frozenset[str]] = set()

    def parse(self, path: str) -> None:
        """Read the map file per line and parse its content.

        Parameters
        ----------
        path : str
            The pathway pointing to the map file to be read.
        """
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    # print(f"line {line_no}: {line.rstrip()}")
                    self._scan_line(line_no, stripped)
        self._final_check()

    def _scan_line(
            self,
            line_no: int,
            line: str
    ) -> None:
        """Read the content of every non-commented line in the map file.

        Following the label of the line, this method will call the right
        handler to extract the right data.
        """
        label, sep, interest = line.partition(":")
        if not sep:
            raise ParserError(line_no, "missing ':' after label")
        if not self.nb_drones and label.strip() != "nb_drones":
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
        """Check the format of the values for one line.

        Parameters
        ----------
        line_no : int
            The number of the current line being read.
        interest : str
            Line content after the ':'.
        expected_number : int
            Number of main elements expected for this labelled line.
        message_content : str
            Format of the expected data for this label.

        Returns
        -------
        tuple[list[str], dict[str, str]]
            A tuple of splitted data (name, coordinates)
            and a dict of metadata.
        """
        body, metadata = self._split_from_metadata(line_no, interest)
        if len(body.split()) != expected_number:
            raise ParserError(
                line_no, f"line should be formatted as {message_content}")
        final_metadata = self._read_optional_metadata(line_no, metadata)
        # if final_metadata:
        #     print(final_metadata)
        return (body.split(), final_metadata)

    @staticmethod
    def _split_from_metadata(
            line_no: int,
            interest: str
    ) -> tuple[str, str | None]:
        """Separates the name and coordinates from the metadatas.

        Parameters
        ----------
        line_no : int
            Number of the currently read line.
        interest : str
            Line content after the ':', containing the values to be split.

        Returns
        -------
        tupl[str, str | None]
            A tuple of the content outside the brackets and the content inside.
            The latter is None if there's no brackets.
        """
        opening = interest.find("[")
        ending = interest.find("]")
        if opening == -1 and ending == -1:
            return (interest, None)
        else:
            if interest.count("[") != interest.count("]"):
                raise ParserError(line_no, "missing pair bracket")
            if not interest.endswith("]"):
                raise ParserError(line_no, "garbage value")
            if interest.count("[") != 1 or interest.count("]") != 1:
                raise ParserError(line_no, "too many brackets")
        return (interest[:opening], interest[opening+1:ending])

    def _read_optional_metadata(
            self,
            line_no: int,
            metadata: str | None
    ) -> dict[str, str]:
        """Extract the content of the brackets as pair of metadatas.

        Parameters
        ----------
        line_no : int
            Number of the currently read line.
        metadata : str
            Content of the brackets in the current line.

        Returns
        -------
        dict[str, str]
            Content of the brackets turned into a dict.
        """
        if metadata is None:
            return {}
        return self._parsing_metadata(line_no, metadata)

    @staticmethod
    def _parsing_metadata(
            line_no: int,
            content: str
    ) -> dict[str, str]:
        """Parse the pairs of key/value metadata into a proper dict.

        Parameters
        ----------
        line_no : int
            Number of the currently read line.
        content : str
            Content of the brackets on the current line.

        Returns
        -------
        dict[str, str]
            Content of the brackets turned into a dict.
        """
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
        """Extract the number of drones from map file and stores it.

        Parameters
        ----------
        line_no : int
            Number of the current line.
        interest : str
            Line content after the ':'.
        """
        body, forbidden = self._split_from_metadata(line_no, interest)
        if len(body.split()) != 1:
            raise ParserError(line_no, "expected one number only")
        if forbidden is not None:
            raise ParserError(line_no, "metadata forbidden here")
        if self.nb_drones:
            raise ParserError(
                line_no, "there should only be one nb_drones line")
        else:
            try:
                converted = int(body)
                if converted <= 0:
                    raise ParserError(
                        line_no, "number should be greater than 0")
                self.nb_drones = converted
            except ValueError:
                raise ParserError(line_no, "invalid number")

    def _parse_zone(
            self,
            line_no: int,
            label: str,
            interest: str,
    ) -> None:
        """Handle the lines labelled as hubs and parse their content.

        Parameters
        ----------
        line_no : int
            Number of the current line.
        label : str
            Content prior the ':', considered label.
        interest : str
            Line content after the ':'.
        """
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
                raise ParserError(
                    line_no, "there should be one start zone only")
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
        """Create a Zone object with the parsed datas and metadatas.

        Parameters
        ----------
        line_no : int
            Number of the current line.
        label : str
            Content prior the ':', considered label.
        body : list[str]
            Splitted main data(name and coordinates) to build the Zone object.
        metadata : dict[str, str]
            Pairs of metadatas from the brackets turned into dict.

        Returns
        -------
        Zone
            Zone object on the map, made with the extracted data from the line.
        """
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
                        raise ParserError(
                            line_no, f"unknown zone type: {value}")
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
                        raise ParserError(
                            line_no, "max drone should be an int")
                case "color":
                    if not isinstance(value, str):
                        raise ParserError(line_no, "invalid color")
                    zone.color = value
                case _:
                    raise ParserError(line_no, "unknown metadata")
        return zone

    def _parse_connection(
            self,
            line_no: int,
            interest: str
    ) -> None:
        """Handle the lines labelled 'connection' and parse their content.

        This instantiates a Connection object for the map with its required
        components from the data parsed here.

        Parameters
        ----------
        line_no : int
            Number of the current line.
        interest : str
            Line content after the ':'.
        """
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
        print(f"{zone_a} is linked to :"
              f" {connection.other_zone(self.zones[zone_a]).name}")
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
