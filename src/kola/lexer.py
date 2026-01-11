from typing import Union, IO, Optional, Iterable
import sys
import io


class BaseLexer(IO[str]):
    """
    KoiLang lexer reading from stdin
    Wraps sys.stdin instead of inheriting from IOBase
    """

    def __init__(self, *, encoding: str | None = None):
        self.encoding = encoding
        self.filename = "<stdin>"
        self._closed = False
        # Wrap sys.stdin as the underlying IO object
        self._io = sys.stdin

    def close(self):
        """Close the lexer"""
        self._closed = True

    @property
    def closed(self) -> bool:
        """Check if the lexer is closed"""
        return self._closed

    def fileno(self) -> int:
        """Return the file descriptor"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.fileno()

    def flush(self):
        """Flush the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self._io.flush()

    def isatty(self) -> bool:
        """Return whether this is an 'interactive' stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.isatty()

    def read(self, size: int = -1) -> str:
        """Read up to size characters from stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.read(size)

    def readline(self, size: int = -1) -> str:
        """Read a line from the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.readline(size)

    def readlines(self, hint: int = -1) -> list[str]:
        """Read and return a list of lines from the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.readlines(hint)

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Change stream position"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.seek(offset, whence)

    def tell(self) -> int:
        """Return current stream position"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.tell()

    def writable(self) -> bool:
        """Return whether the stream supports writing"""
        return self._io.writable()

    def write(self, s: str) -> int:
        """Write string to stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._io.write(s)

    def writelines(self, lines: Iterable[str]) -> None:
        """Write a list of lines to stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self._io.writelines(lines)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        if self.closed:
            return f"<kola lexer in file '{self.filename}' closed>"
        else:
            return f"<kola lexer in file '{self.filename}'>"


class FileLexer(BaseLexer):
    """
    KoiLang lexer reading from file
    Wraps a file object instead of inheriting from IOBase
    """

    def __init__(self, path, *, encoding: str | None = None):
        self._filenameo = path
        self.encoding = encoding
        self.filename = path
        # Wrap a file object as the underlying IO
        self._io = open(path, 'r', encoding=self.encoding)
        self._closed = False

    def close(self):
        """Close the lexer and the underlying file"""
        if not self.closed:
            self._io.close()
            self._closed = True

    @property
    def filename(self):
        return self._filenameo

    @filename.setter
    def filename(self, value):
        self._filenameb = value


class StringLexer(BaseLexer):
    """
    KoiLang lexer reading from string provided
    Wraps a StringIO object instead of inheriting from IOBase
    """

    def __init__(self, content: Union[str, bytes], **kwds):
        self.encoding = kwds.get('encoding', 'utf-8')
        self.filename = "<string>"
        
        # Handle content
        if isinstance(content, bytes):
            self._content = content.decode(self.encoding)
        else:
            self._content = content
        
        # Wrap a StringIO object as the underlying IO
        self._io = io.StringIO(self._content)
        self._closed = False

    def close(self):
        """Close the lexer"""
        if not self.closed:
            self._io.close()
            self._closed = True

    def __repr__(self):
        return f"<kola string lexer>"
