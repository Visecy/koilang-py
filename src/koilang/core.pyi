"""
Type stubs for koilang.core - Python bindings for KoiLang

This module provides comprehensive Python bindings for KoiLang command structures,
parsing functionality, error handling, and output generation.

KoiLang is a markup language that uses commands prefixed with # symbols to
represent structured content. This module allows Python programs to parse,
manipulate, and generate KoiLang content.
"""

from os import PathLike
from typing import IO, Any, Callable, Optional, Union

from typing_extensions import Self

from .types import ParameterType
from .model import FormatterOptions, ParserConfig, WriterConfig

class Command:
    """
    Represents a complete KoiLang command with natural Python interface.

    A command consists of a name and a list of parameters. Parameters can be:
    - Basic values: int, float, str
    - Composite parameters: tuple (name, value) where value can be single, list, or dict

    This class provides convenient access to both positional args and named kwargs,
    making it easy to work with KoiLang commands in Python code.

    Example:
        >>> cmd = Command("heading", [1, ("style", "bold")])
        >>> print(cmd.name)  # "heading"
        >>> print(cmd.args)  # [1]
        >>> print(cmd.kwargs)  # {"style": "bold"}
    """

    def __init__(self, name: str, params: list[ParameterType] = []) -> None:
        """
        Create a new command with the specified name and parameters.

        Args:
            name: The command name as a string
            params: List of parameters, which can be:
                - Basic values: int, float, str
                - Composite parameters: tuple (name, value) where value can be single, list, or dict

        Returns:
            A new Command instance

        Raises:
            ValueError: If any parameter has an unsupported type
        """
        ...

    @classmethod
    def new_text(cls, content: str) -> Self:
        """
        Create a text command representing regular content.

        Args:
            content: The text content as a string

        Returns:
            A new Command instance representing text content
        """
        ...

    @classmethod
    def new_annotation(cls, content: str) -> Self:
        """
        Create an annotation command.

        Args:
            content: The annotation content as a string

        Returns:
            A new Command instance representing an annotation
        """
        ...

    @classmethod
    def new_number(cls, value: int, args: list[ParameterType]) -> Self:
        """
        Create a number command with integer value and additional parameters.

        Args:
            value: The integer value for the number command
            args: List of additional parameters for the command

        Returns:
            A new Command instance representing a number command

        Raises:
            ValueError: If any parameter has an unsupported type
        """
        ...

    @property
    def name(self) -> str:
        """Get the command name.

        Returns:
            The command name as a string
        """
        ...

    @name.setter
    def name(self, value: str) -> None:
        """Set the command name.

        Args:
            value: The new command name as a string
        """
        ...

    @property
    def params(self) -> list[Any]:
        """Get the command parameters as Python objects.

        Returns:
            List of all parameters as Python objects (ints, floats, strings, tuples, lists, dicts)
        """
        ...

    @params.setter
    def params(self, value: list[ParameterType]) -> None:
        """Set the command parameters from Python objects.

        Args:
            params: List of new parameters (same types as accepted by __init__)

        Returns:
            None

        Raises:
            ValueError: If any parameter has an unsupported type
        """
        ...

    @property
    def args(self) -> list[Any]:
        """Get the command args (basic value parameters).

        Returns:
            List of basic value parameters (ints, floats, strings) excluding composite parameters
        """
        ...

    @property
    def kwargs(self) -> dict[str, Any]:
        """Get the command kwargs (composite parameters as dict).

        Returns:
            Dictionary mapping parameter names to their composite values (single, list, or dict)
        """
        ...

    def add_param(self, param: ParameterType) -> None:
        """Add a parameter to the command.

        Args:
            param: Parameter to add (same types as accepted in params list)

        Returns:
            None

        Raises:
            ValueError: If parameter has an unsupported type
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Check equality with another command.

        Args:
            other: Another Command instance to compare with

        Returns:
            True if both commands have the same name and parameters
        """
        ...

    def __repr__(self) -> str:
        """Get a string representation of the command.

        Returns:
            String representation in format: Command('name', [param1, param2, ...])
        """
        ...

    def __str__(self) -> str:
        """Convert command to string.

        Returns:
            String representation of the command in KoiLang format
        """
        ...

class Parser:
    """
    Python binding for the KoiLang parser.

    This class provides a high-level interface for parsing KoiLang content
    from various input sources including files, file-like objects, and strings.
    It can be used iteratively to process commands one by one, or with a
    callback function to process all commands automatically.

    Example:
        >>> parser = Parser("file.koi")
        >>> for command in parser:
        ...     print(command)
    """

    def __init__(
        self,
        path_or_file: Union[str, PathLike[str], IO[str]],
        /,
        config: Optional[ParserConfig] = None,
    ) -> None:
        """
        Create a new parser from various input sources.

        Args:
            path_or_file: Input source, can be:
                - String containing KoiLang text
                - File path (str or PathLike)
                - File-like object with readline() method
            config: Optional parser configuration with keys:
                - command_threshold: int (default: 1) - minimum # for commands
                - skip_annotations: bool (default: false) - skip annotation processing
                - convert_number_command: bool (default: true) - auto-convert numbers
                - skip_add_traceback: bool (default: false) - skip Python traceback

        Returns:
            New Parser instance

        Raises:
            ValueError: If input cannot be opened or read
            AttributeError: If file-like object lacks required methods
        """
        ...

    def next_command(self) -> Optional[Command]:
        """Get the next command from the input.

        Returns:
            Command object if a command is found, None if end of input is reached

        Raises:
            KoiParseError: If parsing fails (syntax errors, unexpected input, etc.)
            IOError: If there are input/output errors
        """
        ...

    def __iter__(self) -> Self:
        """Get an iterator over the parser commands.

        Returns:
            Self - the parser itself for iteration
        """
        ...

    def __next__(self) -> Command:
        """Get the next command from the parser (for iteration).

        Returns:
            Command object if a command is found

        Raises:
            StopIteration: If end of input is reached
            KoiParseError: If parsing fails
        """
        ...

    def process_with(self, callback: Callable[[Command], bool]) -> bool:
        """
        Process all commands using a callback function.

        This method provides an efficient way to process all commands in the input
        without manually handling iteration and error checking.

        Args:
            callback: Python callable that takes a Command and returns bool
                      Return True to continue processing, False to stop early

        Returns:
            True if processing reached end of input, False if stopped by callback

        Raises:
            ValueError: If callback is not callable
            KoiParseError: If parsing fails during processing
            Exception: If callback raises an exception
        """
        ...

class TracebackEntry:
    """
    Represents a traceback entry with location and context information.

    This class represents a single entry in the parsing traceback, containing
    detailed information about where in the parsing process an error occurred.
    It includes line numbers, column ranges, context information, and can have
    nested child entries for complex parsing scenarios.
    """

    def __init__(
        self, lineno: int, start_column: int, end_column: int, context: str
    ) -> None:
        """Create a new traceback entry.

        Args:
            lineno: Line number where the traceback point occurred
            start_column: Starting column position (0-based)
            end_column: Ending column position
            context: Description of the parsing context

        Returns:
            New TracebackEntry instance
        """
        ...

    @property
    def lineno(self) -> int:
        """Get the line number where this traceback point occurred.

        Returns:
            Line number as integer (1-based)
        """
        ...

    @property
    def column_range(self) -> tuple[int, int]:
        """Get the column range where this traceback point occurred.

        Returns:
            Tuple of (start_column, end_column) as integers
        """
        ...

    @property
    def context(self) -> str:
        """Get the context description for this traceback point.

        Returns:
            Context description as string
        """
        ...

    @property
    def children(self) -> list[Self]:
        """Get the child traceback entries.

        Returns:
            List of child TracebackEntry objects
        """
        ...

    @property
    def start_column(self) -> int:
        """Get the start column for convenience.

        Returns:
            Starting column position as integer
        """
        ...

    @property
    def end_column(self) -> int:
        """Get the end column for convenience.

        Returns:
            Ending column position as integer
        """
        ...

    def has_children(self) -> bool:
        """Check if this traceback entry has children.

        Returns:
            True if there are child entries, False otherwise
        """
        ...

    def __repr__(self) -> str:
        """Get string representation of the traceback entry.

        Returns:
            String representation with line number, column range, context, and children count
        """
        ...

    def __str__(self) -> str:
        """Convert traceback entry to formatted string.

        Returns:
            Formatted string representation of the traceback
        """
        ...

class KoiParserLineSource:
    """
    Represents source information for parser errors.

    This class contains metadata about where a parsing error occurred,
    including the file path, line number, and the actual line content.
    This information is crucial for debugging parsing issues and
    providing meaningful error messages to users.
    """

    def __init__(self, filename: str, lineno: int, text: Optional[str]) -> None:
        """Create a new parser line source.

        Args:
            filename: Path to the source file
            lineno: Line number (1-based)
            text: Optional text content of the line

        Returns:
            New KoiParserLineSource instance
        """
        ...

    @property
    def filename(self) -> str:
        """Source file path.

        The path to the file where the line originated from.
        This could be a file path, URL, or any other identifier for the source.
        """
        ...

    @property
    def lineno(self) -> int:
        """Line number in the source file.

        The line number where the error occurred, starting from 1.
        """
        ...

    @property
    def text(self) -> Optional[str]:
        """The input line content.

        The actual text content of the line where the error occurred.
        This is used to display the problematic code in error messages.
        """
        ...

    def __repr__(self) -> str:
        """Get string representation of the source.

        Returns:
            String in format: KoiParserLineSource(filename='path', lineno=123)
        """
        ...

# Exception classes for parsing errors
class KoiParseError(Exception):
    """Base class for all KoiLang parsing errors.

    This is the root exception class for all parsing errors that can occur
    when parsing KoiLang files. It provides access to traceback information
    and source location details for debugging parsing issues.
    """

    @property
    def lineno(self) -> Optional[int]:
        """Get the line number where the error occurred (if available)."""
        ...

    @property
    def filename(self) -> Optional[str]:
        """Get the filename where the error occurred (if available)."""
        ...

    @property
    def position(self) -> Optional[tuple[int, int]]:
        """Get the position (line, column) where the error occurred (if available)."""
        ...

    @property
    def traceback(self) -> Optional[TracebackEntry]:
        """Get the traceback entry for this error (if available)."""
        ...

    @property
    def source(self) -> Optional[KoiParserLineSource]:
        """Get the source information for this error (if available)."""
        ...

class KoiParserSyntaxError(KoiParseError):
    """Exception thrown when there are syntax errors in the input.

    This error is raised when the parser encounters malformed KoiLang syntax
    that cannot be processed. The error message will describe what was expected
    and what was found instead.
    """

    @property
    def message(self) -> str:
        """Get the error message.

        Returns:
            Human-readable error message describing the syntax error
        """
        ...

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            The error message
        """
        ...

class KoiParserUnexpectedInputError(KoiParseError):
    """Exception thrown when parser encounters unexpected input.

    This error is raised when the parser expects one type of token or structure
    but encounters something different. The remaining input that caused the issue
    is preserved for debugging purposes.
    """

    @property
    def remaining(self) -> str:
        """Get the remaining input that caused the unexpected input error.

        Returns:
            The remaining input that caused the error
        """
        ...

    @property
    def message(self) -> str:
        """Get the error message.

        Returns:
            Formatted error message describing the unexpected input
        """
        ...

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            The formatted error message
        """
        ...

class KoiParserUnexpectedEofError(KoiParseError):
    """Exception thrown when parser reaches unexpected end of input.

    This error is raised when the parser expects more input but encounters
    the end of file unexpectedly. The error message describes what was expected
    to be found.
    """

    @property
    def expected(self) -> str:
        """Get the description of what was expected when EOF was encountered.

        Returns:
            Description of what was expected
        """
        ...

    @property
    def message(self) -> str:
        """Get the error message.

        Returns:
            Formatted error message describing the unexpected EOF
        """
        ...

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            The formatted error message
        """
        ...

# NumberFormat enum
class NumberFormat:
    """Number format options for command parameter formatting.

    This enum defines the different numeric formats that can be used when
    writing commands to KoiLang files. It controls how numeric values are
    represented in the output.
    """

    UNKNOWN: NumberFormat
    """Unset number format (default) - uses natural representation"""

    DECIMAL: NumberFormat
    """Decimal format (e.g., 42)"""

    HEX: NumberFormat
    """Hexadecimal format (e.g., 0x2A)"""

    OCTAL: NumberFormat
    """Octal format (e.g., 052)"""

    BINARY: NumberFormat
    """Binary format (e.g., 0b101010)"""

# ParamFormatSelector enum
class ParamFormatSelector:
    """Selector for parameter format configuration.

    This class provides ways to select specific parameters for custom formatting
    rules. You can select parameters either by their position (0-based index)
    in the parameter list or by their name for composite parameters.
    """

    def __init__(self) -> None:
        """ParamFormatSelector should not be instantiated directly.

        Use the class methods by_position() or by_name() to create instances.
        """
        ...

    @classmethod
    def by_position(cls, position: int) -> Self:
        """Create a selector by position index.

        Args:
            position: 0-based position in the parameter list

        Returns:
            New ParamFormatSelector instance
        """
        ...

    @classmethod
    def by_name(cls, name: str) -> Self:
        """Create a selector by parameter name.

        Args:
            name: Name of the composite parameter

        Returns:
            New ParamFormatSelector instance
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Check equality with another ParamFormatSelector.

        Args:
            other: Another ParamFormatSelector to compare with

        Returns:
            True if both selectors are equivalent
        """
        ...

    def __hash__(self) -> int:
        """Get hash value for dictionary keys.

        Returns:
            Hash value for use in dictionaries and sets
        """
        ...

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation in format: ParamFormatSelector.Position(n) or ParamFormatSelector.Name("name")
        """
        ...

# Writer class
class Writer:
    """KoiLang writer for generating formatted output.

    This class provides functionality to write KoiLang commands to output streams
    with various formatting options. It handles indentation, number formatting,
    and can apply custom formatting rules for specific commands or parameters.
    """

    def __init__(
        self,
        py_file: Union[str, PathLike[str], IO[str]],
        config: Optional[WriterConfig] = None,
    ) -> None:
        """Create a new Writer from a path, PathLike, or Python file-like object.

        Args:
            py_file: Output target, can be:
                - File path (str or PathLike[str])
                - Python file-like object with write() and flush() methods
            config: Optional writer configuration

        Returns:
            New Writer instance

        Raises:
            TypeError: If the object doesn't have required write/flush methods and isn't a path
            ValueError: If file cannot be created
        """
        ...

    def write_command(self, command: Command) -> None:
        """Write a command using the default formatting options.

        Args:
            command: Command object to write

        Returns:
            None

        Raises:
            ValueError: If writing fails
        """
        ...

    def write_command_with_options(
        self,
        command: Command,
        options: Optional[FormatterOptions] = None,
        param_options: Optional[dict[ParamFormatSelector, FormatterOptions]] = None,
    ) -> None:
        """Write a command with custom formatting options.

        Args:
            command: Command object to write
            options: Optional custom formatting options
            param_options: Optional parameter-specific formatting options

        Returns:
            None

        Raises:
            ValueError: If writing fails
        """
        ...

    def inc_indent(self) -> None:
        """Increase the indentation level.

        This affects subsequent command writes by adding one level of indentation.
        """
        ...

    def dec_indent(self) -> None:
        """Decrease the indentation level, but not below 0.

        Ensures indentation never goes below zero.
        """
        ...

    def get_indent(self) -> int:
        """Get the current indentation level.

        Returns:
            Current indentation level as integer
        """
        ...

    def newline(self) -> None:
        """Write a newline character.

        Returns:
            None

        Raises:
            ValueError: If writing fails
        """
        ...

# Module exports
__all__ = [
    "Command",
    "Parser",
    "TracebackEntry",
    "KoiParserLineSource",
    "KoiParseError",
    "KoiParserSyntaxError",
    "KoiParserUnexpectedInputError",
    "KoiParserUnexpectedEofError",
    "NumberFormat",
    "ParamFormatSelector",
    "Writer",
]
