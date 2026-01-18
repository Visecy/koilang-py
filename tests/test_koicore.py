"""
Comprehensive unit tests for koicore Python bindings

Tests all public API bindings to ensure complete synchronization with Rust implementation.
"""

import io
from typing import IO

import pytest

from koilang.core import (
    Command,
    NumberFormat,
    ParamFormatSelector,
    Parser,
    Writer,
)
from koilang.model import ParserConfig, FormatterOptions


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


def test_writer_with_str_path(tmp_path):
    output_file = tmp_path / "test_str.koi"
    output_path = str(output_file)

    with Writer(output_path) as writer:
        writer.write_command(Command("test", [1, "abc"]))

    assert output_file.exists()
    content = output_file.read_text()
    assert "#test 1 abc" in content


def test_writer_with_pathlib_path(tmp_path):
    output_file = tmp_path / "test_pathlib.koi"

    with Writer(output_file) as writer:
        writer.write_command(Command("hello", ["world"]))

    assert output_file.exists()
    content = output_file.read_text()
    assert "#hello world" in content


def test_writer_context_manager(tmp_path):
    output_file = tmp_path / "test_ctx.koi"

    writer = Writer(str(output_file))
    with writer:
        writer.write_command(Command("foo", ["bar"]))

    # Check if we can still read (file should be closed/flushed)
    content = output_file.read_text()
    assert "#foo bar" in content


def test_writer_explicit_close(tmp_path):
    output_file = tmp_path / "test_close.koi"

    writer = Writer(str(output_file))
    writer.write_command(Command("manual", [123]))
    writer.close()

    content = output_file.read_text()
    assert "#manual 123" in content


def test_write_command_with_options():
    output = io.BytesIO()
    writer = Writer(output)

    cmd = Command("test", [42, "hello"])

    # Custom options for the command
    options = FormatterOptions(
        indent=0,
        use_tabs=False,
        newline_before=False,
        newline_after=False,
        compact=True,
        force_quotes_for_vars=False,
        number_format=NumberFormat.HEX,
        newline_before_param=False,
        newline_after_param=False,
        should_override=True,
    )

    writer.write_command_with_options(cmd, options=options)
    writer.close()

    result = output.getvalue().decode("utf-8")
    # 42 in hex is 0x2a
    assert "#test 0x2a hello" in result


def test_write_command_with_param_options():
    output = io.BytesIO()
    writer = Writer(output)

    cmd = Command("test", [42, 255])

    # Custom options for specific parameters
    # Param 0: Decimal, Param 1: Hex
    param_options = {
        ParamFormatSelector.by_position(0): FormatterOptions(
            indent=0,
            use_tabs=False,
            newline_before=False,
            newline_after=False,
            compact=True,
            force_quotes_for_vars=False,
            number_format=NumberFormat.DECIMAL,
            newline_before_param=False,
            newline_after_param=False,
            should_override=True,
        ),
        ParamFormatSelector.by_position(1): FormatterOptions(
            indent=0,
            use_tabs=False,
            newline_before=False,
            newline_after=False,
            compact=True,
            force_quotes_for_vars=False,
            number_format=NumberFormat.HEX,
            newline_before_param=False,
            newline_after_param=False,
            should_override=True,
        ),
    }

    writer.write_command_with_options(cmd, param_options=param_options)
    writer.close()

    result = output.getvalue().decode("utf-8")
    assert "#test 42 0xff" in result


def test_write_command_with_named_param_options():
    output = io.BytesIO()
    writer = Writer(output)

    # Composite parameter: ("val", 123)
    cmd = Command("test", [("val", 123)])

    param_options = {
        ParamFormatSelector.by_name("val"): FormatterOptions(
            indent=0,
            use_tabs=False,
            newline_before=False,
            newline_after=False,
            compact=True,
            force_quotes_for_vars=False,
            number_format=NumberFormat.BINARY,
            newline_before_param=False,
            newline_after_param=False,
            should_override=True,
        )
    }

    writer.write_command_with_options(cmd, param_options=param_options)
    writer.close()

    result = output.getvalue().decode("utf-8")
    # 123 in binary is 0b1111011
    assert "val(0b1111011)" in result

