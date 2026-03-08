from typing import Any, IO, List, Optional, Set, Union, TYPE_CHECKING
from contextlib import contextmanager

from ..types import StrPathLike
from ..core import Command, Writer as CoreWriter
from ..model import FormatterOptions, WriterConfig

if TYPE_CHECKING:
    pass


def _build_params(args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[Any]:
    params = list(args)
    for k, v in kwargs.items():
        params.append((k, v))
    return params


class _OptionsProxy:
    """Proxy for applying temporary options to writer calls."""

    def __init__(
        self, writer: "Writer", options: FormatterOptions, targets: Optional[Set[str]]
    ) -> None:
        self._writer = writer
        self._options = options
        self._targets = targets

    def __enter__(self) -> "Writer":
        self._writer._options_stack.append((self._options, self._targets))
        return self._writer

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._writer._options_stack.pop()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_") or name.startswith("on_"):

            def wrapper(*args: Any, **kwargs: Any) -> Any:
                cmd_name = self._writer._get_command_name(name)
                if self._targets is None or cmd_name in self._targets:
                    # Apply options for this specific call
                    if name == "on_text":
                        cmd = Command.new_text(args[0] if args else "")
                    elif name == "on_annotation":
                        cmd = Command.new_annotation(args[0] if args else "")
                    else:
                        cmd = Command(cmd_name, _build_params(args, kwargs))
                    return self._writer.write_command(cmd, options=self._options)
                else:
                    # Default call
                    return getattr(self._writer, name)(*args, **kwargs)

            return wrapper
        return getattr(self._writer, name)


class Writer:
    """A programmatic interface for writing KoiLang content.

    Allows calling commands as methods and provides flexible formatting options.

    Example:
        >>> with Writer("output.koi") as w:
        ...     w.do_heading("Title")
        ...     with w.indent():
        ...         w.on_text("Some content")
        ...         w.with_options(compact=True).do_tight_cmd()
    """

    def __init__(
        self,
        target: Union[StrPathLike, IO[str]],
        config: Optional[WriterConfig] = None,
    ) -> None:
        self._core_writer = CoreWriter(target, config)
        self._options_stack: List[tuple[FormatterOptions, Optional[Set[str]]]] = []

    def __enter__(self) -> "Writer":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying writer."""
        self._core_writer.close()

    def newline(self) -> None:
        """Write a newline."""
        self._core_writer.newline()

    def inc_indent(self) -> None:
        """Increase indentation level."""
        self._core_writer.inc_indent()

    def dec_indent(self) -> None:
        """Decrease indentation level."""
        self._core_writer.dec_indent()

    @contextmanager
    def indent(self):
        """Context manager for temporary indentation."""
        self.inc_indent()
        try:
            yield self
        finally:
            self.dec_indent()

    def with_options(
        self,
        options: Optional[FormatterOptions] = None,
        target_commands: Optional[Union[List[str], Set[str]]] = None,
        **kwargs: Any,
    ) -> _OptionsProxy:
        """Apply temporary formatting options.

        Supports both fluent API and context manager usage.

        Args:
            options: Explicit FormatterOptions.
            target_commands: List or set of command names to apply these options to.
            **kwargs: Inline formatting options (passed to FormatterOptions constructor).
        """
        if options is None:
            options = FormatterOptions(**kwargs)

        targets = set(target_commands) if target_commands is not None else None
        return _OptionsProxy(self, options, targets)

    def write_command(
        self, command: Command, options: Optional[FormatterOptions] = None
    ) -> None:
        """Write a command object with optional formatting overrides."""
        if options:
            self._core_writer.write_command_with_options(command, options=options)
        else:
            # Check options stack
            active_options = None
            cmd_name = command.name
            for opt, targets in reversed(self._options_stack):
                if targets is None or cmd_name in targets:
                    active_options = opt
                    break

            if active_options:
                self._core_writer.write_command_with_options(
                    command, options=active_options
                )
            else:
                self._core_writer.write_command(command)

    def _get_command_name(self, method_name: str) -> str:
        if method_name.startswith("on_"):
            return f"@{method_name[3:]}"
        if method_name.startswith("do_"):
            return method_name[3:]
        return method_name

    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_") or name.startswith("on_"):

            def wrapper(*args: Any, **kwargs: Any) -> None:
                cmd_name = self._get_command_name(name)
                if name == "on_text":
                    cmd = Command.new_text(args[0] if args else "")
                elif name == "on_annotation":
                    cmd = Command.new_annotation(args[0] if args else "")
                else:
                    cmd = Command(cmd_name, _build_params(args, kwargs))
                self.write_command(cmd)

            return wrapper
        raise AttributeError(f"'Writer' object has no attribute '{name}'")
