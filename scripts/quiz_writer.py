import argparse
from pathlib import Path
from this import s

HEADER = ""


class Parser:
    def __init__(self, contents: str) -> None:
        self.start: int = 0
        self.current: int = 0
        self.contents: str = contents
        self.buffer: str = ""

    def scan_tokens(self):
        while not self.is_end():
            self.start = self.current
            self.scan()

    def scan(self):
        c: str = self.advance()

        match c:
            case c if c.isalpha():
                ...
            case "$":
                self.start = self.current
                while not self.is_end() and self.peek() != " ":
                    _ = self.advance()
                key_word = self.contents[self.start : self.current]

                if key_word == "TITLE":
                    self.start = self.current
                    while not self.is_end() and self.peek() != "\n":
                        _ = self.advance()
                elif key_word == "AUTHOR":
                    ...
            case "%":
                self.start = self.current
                while not self.is_end() and self.peek() != "\n":
                    _ = self.advance()
                print(self.contents[self.start : self.current])
            case "?":
                self.start = self.current
                while not self.is_end() and self.peek() != "\n":
                    _ = self.advance()
                print(self.contents[self.start : self.current])
            case "!":
                self.start = self.current
                while not self.is_end() and self.peek() != "\n":
                    _ = self.advance()
                print(self.contents[self.start : self.current])
            case ">":
                self.start = self.current
                while not self.is_end() and self.peek() != "\n":
                    _ = self.advance()
                print(self.contents[self.start : self.current])
            case " " | "\t":
                return
            case "\n":
                return
            case _:
                print(f"Unknown char '{c}'")
                raise Exception

    def advance(self) -> str:
        if self.is_end():
            return "\0"
        self.current += 1
        return self.contents[self.current - 1]

    def peek(self) -> str:
        if self.is_end():
            return "\0"
        return self.contents[self.current]

    def is_end(self) -> bool:
        return self.current > len(self.contents)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    _ = arg_parser.add_argument("file", help="File path")

    args = arg_parser.parse_args()

    with open(args.file, "r") as f:
        contents = f.read()

    p = Parser(contents)

    p.scan_tokens()
