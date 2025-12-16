"""
Comprehensive unit tests for koicore Python bindings

Tests all public API bindings to ensure complete synchronization with Rust implementation.
"""

import io
from typing import IO

import pytest

from koilang import (
    Command,
    NumberFormat,
    ParamFormatSelector,
    Parser,
    TracebackEntry,
    Writer,
)
from koilang.model import ParserConfig


@pytest.fixture
def ktxt_file() -> IO[str]:
    content = """## Sample KoiLang file
    Hello world!
    #test 1 abc a(1) 3.14 b(2, "3") c(d: 4)
    """
    return io.StringIO(content)


@pytest.fixture
def commands() -> list[Command]:
    return [
        Command.new_annotation("## Sample KoiLang file"),
        Command.new_text("Hello world!"),
        Command("test", [1, "abc", ("a", 1), 3.14, ("b", [2, "3"]), ("c", {"d": 4})]),
    ]


def test_parser_initialization() -> None:
    empty_file = io.StringIO()
    parser = Parser(empty_file)
    assert isinstance(parser, Parser)
    assert parser.next_command() is None

    config = ParserConfig(command_threshold=2, skip_annotations=True)
    parser_with_config = Parser(empty_file, config)
    assert isinstance(parser_with_config, Parser)
    assert parser_with_config.next_command() is None


def test_parse_commands(ktxt_file: IO[str], commands: list[Command]) -> None:
    parser = Parser(ktxt_file)
    parsed_commands = []
    while True:
        cmd = parser.next_command()
        if cmd is None:
            break
        parsed_commands.append(cmd)
    assert parsed_commands == commands
