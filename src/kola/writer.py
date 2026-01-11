import os
import io
from types import TracebackType
from typing import Any, Type, Union, Optional
from typing_extensions import Protocol, runtime_checkable, Self

from koilang.core import Writer as CoreWriter, Command as CoreCommand
from koilang.model import WriterConfig, FormatterOptions


@runtime_checkable
class WriterItemLike(Protocol):
    def __kola_write__(self, __writer: "BaseWriter", __level: int) -> None: ...


class BaseWriterItem(object):
    def __kola_write__(self, writer: "BaseWriter", level: int) -> None: ...


class BaseWriter(object):
    def __init__(self, indent: int = 4, command_threshold: int = 1) -> None:
        self._indent_val = indent
        self._command_threshold = command_threshold
        self._writer: Optional[CoreWriter] = None
        self._io: Optional[io.IOBase] = None
        self._closed = False

    def _init_writer(self, py_file: Union[str, os.PathLike, io.IOBase]):
        config = WriterConfig(
            global_options=FormatterOptions(indent=self._indent_val),
            command_threshold=self._command_threshold,
        )
        self._writer = CoreWriter(py_file, config=config)
        if isinstance(py_file, io.IOBase):
            self._io = py_file

    @property
    def indent(self) -> int:
        if self._writer:
            try:
                return self._writer.get_indent()
            except AttributeError:
                pass
        return 0

    def raw_write(self, text: str) -> None:
        # CoreWriter doesn't expose raw write easily, but we can write it to the IO if we have it
        if self._io:
            self._io.write(text)
        elif self._writer:
            # Fallback for when we don't have direct access to IO?
            # Actually CoreWriter usually has the IO.
            pass

    def close(self) -> None:
        if not self._closed:
            if self._writer:
                try:
                    self._writer.close()
                except AttributeError:
                    pass
                self._writer = None
            if self._io:
                self._io.close()
                self._io = None
            self._closed = True

    def inc_indent(self) -> None:
        if self._writer:
            self._writer.inc_indent()

    def dec_indent(self) -> None:
        if self._writer:
            self._writer.dec_indent()

    def newline(self, concat_prev: bool = False) -> None:
        if self._writer:
            self._writer.newline()

    def write_text(self, text: str) -> None:
        if self._writer:
            self._writer.write_command(CoreCommand.new_text(text))

    def write_annotation(self, annotation: str) -> None:
        if self._writer:
            self._writer.write_command(CoreCommand.new_annotation(annotation))

    def write_command(self, __name: Union[str, int], *args: Any, **kwds: Any) -> None:
        if not self._writer:
            return

        if isinstance(__name, int):
            # Number command
            params = []
            for arg in args:
                params.append(arg)
            for k, v in kwds.items():
                params.append((k, v))
            cmd = CoreCommand.new_number(__name, params)
        else:
            params = []
            for arg in args:
                params.append(arg)
            for k, v in kwds.items():
                params.append((k, v))
            cmd = CoreCommand(__name, params)

        self._writer.write_command(cmd)

    def write(self, command: Union[str, WriterItemLike]) -> None:
        if isinstance(command, str):
            self.write_text(command)
        elif isinstance(command, WriterItemLike):
            command.__kola_write__(self, self.indent)
        else:
            raise TypeError(f"Expected str or WriterItemLike, got {type(command)}")

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_ins: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()


class FileWriter(BaseWriter):
    def __init__(
        self,
        __path: Union[str, bytes, os.PathLike],
        encoding: str = "utf-8",
        indent: int = 4,
        command_threshold: int = 1,
    ) -> None:
        super().__init__(indent, command_threshold)
        self.path = __path
        self.encoding = encoding
        # CoreWriter works best with binary file objects from Python
        self._io = open(__path, "wb")
        self._init_writer(self._io)


class StringWriter(BaseWriter):
    def __init__(self, indent: int = 4, command_threshold: int = 1) -> None:
        super().__init__(indent, command_threshold)
        self._buffer = io.BytesIO()
        self._init_writer(self._buffer)

    def getvalue(self) -> str:
        # CoreWriter doesn't have a flush() method, it writes directly to IO
        return self._buffer.getvalue().decode("utf-8")
