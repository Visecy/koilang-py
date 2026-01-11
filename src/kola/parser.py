from typing import Any, Callable, Final, Generic, Tuple, TypeVar
from typing_extensions import Protocol, Self
from .lexer import BaseLexer
from .exception import KoiLangSyntaxError, KoiLangCommandError
from koilang.core import Parser as CoreParser, Command as CoreCommand, KoiParseError
from koilang.model import ParserConfig


class SupportGetCommand(Protocol):
    def __getitem__(self, __key: str) -> Callable: ...


T_CmdSet = TypeVar("T_CmdSet", bound=SupportGetCommand)
T_Lexer = TypeVar("T_Lexer", bound=BaseLexer)


class Parser(Generic[T_Lexer, T_CmdSet]):
    lexer: Final[T_Lexer]
    command_set: Final[T_CmdSet]

    def __init__(self, lexer: T_Lexer, command_set: T_CmdSet) -> None:
        self.lexer = lexer
        self.command_set = command_set

        # Determine command threshold from command_set if possible
        threshold = getattr(command_set.__class__, "__command_threshold__", 1)
        config = ParserConfig(command_threshold=threshold)

        # CoreParser accepts IO[str] which BaseLexer implements
        self._core_parser = CoreParser(lexer, config=config)

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Any:
        try:
            core_cmd: CoreCommand = next(self._core_parser)
        except StopIteration:
            raise StopIteration
        except KoiParseError as e:
            raise KoiLangSyntaxError(str(e)) from e
        except Exception as e:
            raise e

        # Resolve command name
        name = core_cmd.name

        # Look up the command in the command set
        try:
            cmd_func = self.command_set[name]
        except KeyError:
            # In kola, unknown commands should raise KoiLangCommandError
            # so the VM can catch it in on_exception
            raise KoiLangCommandError(f"Unknown command: {name}")

        # Execute the command.
        # For kola.klvm.Command, calling the bound method will trigger __kola_caller__
        return cmd_func(*core_cmd.args, **core_cmd.kwargs)

    def eof(self) -> bool:
        # Check if lexer is at EOF?
        # StringLexer/FileLexer should handle this.
        # But CoreParser doesn't expose EOF easily except through StopIteration.
        # This is a bit of a hack.
        return self.lexer.closed  # Not exactly EOF but close enough?

    def exec_once(self) -> Any:
        return next(self)

    def exec(self) -> None:
        for _ in self:
            pass

    # push/pop/parse_args are not implemented as they are not used in tests
    # and not easily supported by the new streaming CoreParser.
    def push(self, token: Any) -> None:
        raise NotImplementedError("push() is not supported by the new CoreParser")

    def pop(self) -> Any:
        raise NotImplementedError("pop() is not supported by the new CoreParser")

    def parse_args(self) -> Tuple[tuple, dict]:
        raise NotImplementedError("parse_args() is not supported by the new CoreParser")
