from enum import Enum


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


def read_metadata(
        line_no: int,
        line: str
) -> None:
    result = {}
    parts = line.partition(":")
    interest = parts[2]
    if interest:
        opening = interest.find("[")
        ending = interest.find("]")
        if opening > ending:
            raise ParserError(line_no, "mismatched bracket")
        if opening != -1 and ending != -1:
            content = interest[opening+1:ending]
            subparts = content.split()
            for part in subparts:
                if "=" in part:
                    key, _, value = part.partition("=")
                    if not key or not value:
                        raise ParserError(line_no, "missing key/value")
                    elif key in result.keys():
                        raise ParserError(line_no, "duplicate metadata detected")
                    result.update({key: value})
                else:
                    raise ParserError(line_no, "malformed metadata")
            print(result)
        elif (opening != -1 and ending == -1) or (opening == -1 and ending != -1):
            raise ParserError(line_no, "missing pair bracket")
        else:
            print("No metadata")
    else:
        raise ParserError(line_no, "zone not defined properly")


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    


if __name__ == "__main__":
    parse_file()
