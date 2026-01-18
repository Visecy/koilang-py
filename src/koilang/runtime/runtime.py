from typing import (
    IO,
    Any,
    Callable,
    List,
    Optional,
    Union,
)

from ..core import Command, Parser
from .context import wrap_handler


Middleware = Callable[["Runtime", Command, Callable[[], Any]], Any]


class Runtime:
    def __init__(
        self, root_env: Any, middleware: Optional[List[Middleware]] = None
    ) -> None:
        self.env_stack: List[Any] = [root_env]
        self.middleware: List[Middleware] = middleware or []
        self._current_command: Optional[Command] = None

    def env_enter(self, env: Any) -> None:
        self.env_stack.append(env)

    def env_exit(self, env: Any) -> None:
        if self.env_stack[-1] is not env:
            raise ValueError("Environment mismatch during exit")
        self.env_stack.pop()

    def execute(self, source: Union[str, IO[str]]) -> None:
        self._notify_lifecycle("on_start")
        try:
            parser = Parser(source)
            for cmd in parser:
                self._dispatch(cmd)
        finally:
            self._notify_lifecycle("on_end")

    def _notify_lifecycle(self, method_name: str) -> None:
        for env in self.env_stack:
            if hasattr(env, method_name):
                getattr(env, method_name)()

    def _dispatch(self, cmd: Command) -> Any:
        """Dispatch command through middleware chain."""
        if not self.middleware:
            return self._execute_command(cmd)

        # Build the middleware chain using direct iteration
        def execute_with_middleware(index: int) -> Any:
            if index >= len(self.middleware):
                return self._execute_command(cmd)
            return self.middleware[index](
                self, cmd, lambda: execute_with_middleware(index + 1)
            )

        return execute_with_middleware(0)

    def _get_method_name(self, cmd_name: str) -> str:
        if cmd_name.startswith("@"):
            return f"on_{cmd_name[1:]}"
        return f"do_{cmd_name}"

    def _get_command_name(self, method_name: str) -> str:
        if method_name.startswith("on_"):
            return f"@{method_name[3:]}"
        if method_name.startswith("do_"):
            return method_name[3:]
        return method_name

    def _execute_on_env(self, env: Any, method_name: str, cmd: Command) -> Any:
        handler_method = getattr(env, method_name)
        return wrap_handler(self, cmd, handler_method)

    def _execute_command(self, cmd: Command) -> Any:
        self._current_command = cmd
        try:
            method_name = self._get_method_name(cmd.name)

            # Search for handler in the environment stack, from top to bottom
            for env in reversed(self.env_stack):
                if hasattr(env, method_name):
                    return self._execute_on_env(env, method_name, cmd)

            return None
        finally:
            self._current_command = None
