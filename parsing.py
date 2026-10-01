from typing import Any


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
        with open("./maps/easy/01_linear_path.txt", "r") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print(f"line {line_no}: {line.rstrip()}")
                    read_metadata(line_no, line)
    except (FileNotFoundError, PermissionError):
        print("Invalid file: inaccessible or inexistent")
    except ParserError as p:
        print(p)


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


if __name__ == "__main__":
    parse_file()
