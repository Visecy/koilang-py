"""
Type stubs for koilang.core - Python bindings for KoiLang

This module provides Python bindings for KoiLang command structures and parsing functionality.
"""

from os import PathLike
from typing import IO, Any, Callable, List, Optional, Tuple, Union

from typing_extensions import Self

from .types import ParameterType, ParserConfig


class Command:
    """
    Represents a complete KoiLang command with natural Python interface.
    
    A command consists of a name and a list of parameters. Parameters can be:
    - Basic values: int, float, str
    - Composite parameters: tuple (name, value) where value can be single, list, or dict
    """
    
    def __init__(self, name: str, params: List[ParameterType] = ...) -> None: ...
    
    @classmethod
    def new_text(cls, content: str) -> Self:
        """Create a text command representing regular content."""
        ...
    
    @classmethod  
    def new_annotation(cls, content: str) -> Self:
        """Create an annotation command."""
        ...
    
    @classmethod
    def new_number(cls, value: int, args: List[ParameterType]) -> Self:
        """Create a number command with integer value and additional parameters."""
        ...
    
    @property
    def name(self) -> str:
        """Get the command name."""
        ...
    
    @name.setter
    def name(self, value: str) -> None:
        """Set the command name."""
        ...
    
    @property
    def params(self) -> List[Any]:
        """Get the command parameters as Python objects."""
        ...
    
    @params.setter
    def params(self, value: List[ParameterType]) -> None:
        """Set the command parameters from Python objects."""
        ...

    @property
    def args(self) -> list[Any]:
        """Get the command args (basic value parameters)."""
        ...
    
    @property
    def kwargs(self) -> dict[str, Any]:
        """Get the command kwargs (composite parameters as dict)."""
        ...

    def add_param(self, param: ParameterType) -> None:
        """Add a parameter to the command."""
        ...
    
    def __eq__(self, other: object) -> bool: ...
    
    def __repr__(self) -> str: ...
    
    def __str__(self) -> str: ...


class Parser:
    """
    Python binding for the KoiLang parser.
    
    Parses KoiLang content from files, file-like objects, or path-like objects.
    """
    
    def __init__(
        self, 
        path_or_file: Union[str, PathLike[str], IO[str]], 
        /, 
        config: Optional[ParserConfig] = None
    ) -> None:
        """
        Create a new parser from string path, path-like object, or file-like object.
        
        Args:
            path_or_file: Either a file path string, path-like object, or file-like object
                         with readline() method
            config: Optional parser configuration dict
        """
        ...
    
    def next_command(self) -> Optional[Command]:
        """
        Get the next command from the input.
        
        Returns:
            Command object if a command is found, None if end of input is reached
            
        Raises:
            KoiParseError: If parsing fails
        """
        ...
    
    def __iter__(self) -> Self:
        """Get an iterator over the parser commands.
        
        Returns:
            PyParser object itself, which can be iterated over
        """
        ...
    
    def __next__(self) -> Command:
        """Get the next command from the parser.
        
        Returns:
            PyCommand object if a command is found
            None if end of input is reached
            
        Raises:
            ParseError if parsing fails
        """
        ...
    
    def process_with(self, callback: Callable[[Command], bool]) -> bool:
        """
        Process all commands using a callback function.
        
        Args:
            callback: Python function that takes a Command and returns bool.
                     Return True to continue, False to stop processing.
        
        Returns:
            True if processing reached end of input, False if stopped by callback
            
        Raises:
            KoiParseError: If parsing fails
            Exception: If callback raises an exception
        """
        ...


class TracebackEntry:
    """
    Represents a traceback entry with location and context information.
    
    Provides detailed parsing error information including file locations, 
    line numbers, column positions, and parsing context.
    """
    
    def __init__(self, lineno: int, start_column: int, end_column: int, context: str) -> None: ...
    
    @property
    def lineno(self) -> int:
        """Get the line number where this traceback point occurred."""
        ...
    
    @property
    def column_range(self) -> Tuple[int, int]:
        """Get the column range where this traceback point occurred.
        
        Returns:
            A tuple (start_column, end_column)
        """
        ...
    
    @property
    def context(self) -> str:
        """Get the context description for this traceback point."""
        ...
    
    @property
    def children(self) -> List[Self]:
        """Get the child traceback entries.
        
        Returns:
            A list of TracebackEntry objects
        """
        ...
    
    @property
    def start_column(self) -> int:
        """Get the start column for convenience."""
        ...
    
    @property
    def end_column(self) -> int:
        """Get the end column for convenience."""
        ...
    
    def has_children(self) -> bool:
        """Check if this traceback entry has children."""
        ...


class KoiParserLineSource:
    """
    Represents source information for parser errors.
    
    Contains file path, line number, and text content where an error occurred.
    """
    
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


# Exception classes for parsing errors
class KoiParseError(Exception):
    """Base class for all KoiLang parsing errors."""
    
    @property
    def lineno(self) -> Optional[int]:
        """Get the line number where the error occurred (if available)."""
        ...
    
    @property
    def filename(self) -> Optional[str]:
        """Get the filename where the error occurred (if available)."""
        ...
    
    @property
    def position(self) -> Optional[Tuple[int, int]]:
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
    """Thrown when there are syntax errors in the input."""
    
    @property
    def message(self) -> str:
        """Get the error message."""
        ...


class KoiParserUnexpectedInputError(KoiParseError):
    """Thrown when parser encounters unexpected input."""
    
    @property
    def remaining(self) -> str:
        """Get the remaining input that caused the unexpected input error."""
        ...
    
    @property
    def message(self) -> str:
        """Get the error message."""
        ...


class KoiParserUnexpectedEofError(KoiParseError):
    """Thrown when parser reaches unexpected end of input."""
    
    @property
    def expected(self) -> str:
        """Get the description of what was expected when EOF was encountered."""
        ...
    
    @property
    def message(self) -> str:
        """Get the error message."""
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
]
