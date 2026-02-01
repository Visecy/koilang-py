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
from .executor import Executor


Middleware = Callable[["Runtime", Command, Callable[[], Any]], Any]


class _JumpRequest(Exception):
    """Internal exception used to signal a jump request."""

    def __init__(self, position: int) -> None:
        self.position = position
        super().__init__(f"Jump to position {position}")


class Runtime:
    def __init__(
        self, root_env: Any, middleware: Optional[List[Middleware]] = None
    ) -> None:
        self.env_stack: List[Any] = [root_env]
        self.middleware: List[Middleware] = middleware or []
        self._current_command: Optional[Command] = None

        # Cache-related attributes
        self._cache_enabled: bool = False
        self._command_cache: List[Command] = []
        self._label_index: dict[str, int] = {}
        self._current_position: int = -1
        self._parser: Optional[Parser] = None

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
            self._parser = parser
            self._current_position = -1

            while True:
                self._current_position += 1

                # Fetch command
                if self._cache_enabled and self._current_position < len(
                    self._command_cache
                ):
                    # From cache
                    cmd = self._command_cache[self._current_position]
                else:
                    # Beyond cache or cache disabled
                    cmd = parser.next_command()
                    if cmd is None:
                        break

                    if self._cache_enabled:
                        self._command_cache.append(cmd)
                        # Sync position to cache index in case it was just enabled
                        self._current_position = len(self._command_cache) - 1

                try:
                    self._dispatch(cmd)
                except _JumpRequest as jump:
                    # Handle jump by setting position
                    # The loop will increment it, so we set it to target - 1
                    self._current_position = jump.position - 1
        finally:
            self._notify_lifecycle("on_end")
            self._parser = None

    def get_executor(self) -> Executor:
        return Executor(self)

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

    # Cache management methods
    def enable_cache(self) -> None:
        """Enable command caching. If called during execution, caching starts from next command."""
        self._cache_enabled = True

    def disable_cache(self) -> None:
        """Disable caching and clear all cached data."""
        self._cache_enabled = False
        self._command_cache.clear()
        self._label_index.clear()
        # Reset position to signal parser-only execution
        self._current_position = -1

    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache_enabled

    def get_current_position(self) -> int:
        """Get the current execution position."""
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled to get position")
        return self._current_position

    def register_label(self, label: str, position: Optional[int] = None) -> None:
        """Register a label at the specified position (default: current position)."""
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled to register labels")

        pos = position if position is not None else self._current_position
        if pos < 0 or pos >= len(self._command_cache):
            raise ValueError(f"Invalid position {pos} for label '{label}'")

        if label in self._label_index:
            if self._label_index[label] == pos:
                return
            raise ValueError(
                f"Label '{label}' already registered at position {self._label_index[label]}"
            )

        self._label_index[label] = pos

    def jump_to_position(self, position: int) -> None:
        """Jump to a specific command position in the cache."""
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled for jumps")

        if position < 0:
            raise ValueError("Position must be non-negative")

        # If jumping forward, fill cache to target position
        if position >= len(self._command_cache):
            self._fill_cache_to(position)

        # Validate position exists
        if position >= len(self._command_cache):
            raise ValueError(f"Position {position} not available")

        # Raise exception to signal jump
        raise _JumpRequest(position)

    def jump_to_label(
        self,
        label: str,
        find_label: Optional[Callable[[Command], str | None]] = None,
    ) -> None:
        """Jump to a labeled command.

        If the label is not found and find_label is provided, it scans ahead
        to find and register labels until the target is reached.
        """
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled for jumps")

        if label not in self._label_index:
            if find_label is None:
                raise ValueError(f"Label '{label}' not found")

            # Try to find the label by probing
            def strategy(cmd: Command, pos: int) -> bool:
                found_name = find_label(cmd)
                if found_name:
                    # Automatically register what we found
                    self.register_label(found_name, position=pos)
                return found_name == label

            self.probe_until(strategy)

            # Re-check if we found it
            if label not in self._label_index:
                raise ValueError(f"Label '{label}' not found after probe")

        self.jump_to_position(self._label_index[label])

    def scan_and_jump(
        self, strategy: Callable[[Command, int], bool], offset: int = 0
    ) -> None:
        """Scan ahead from current position and jump to the first command that matches the strategy.

        An optional offset can be applied to the target position (e.g. 1 to jump after the match).
        """
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled for scanning")

        pos = self._current_position + 1
        while True:
            if pos < len(self._command_cache):
                cmd = self._command_cache[pos]
            else:
                if not self._parser:
                    raise ValueError("Jump target not found before end of input")

                cmd = self._parser.next_command()
                if cmd is None:
                    raise ValueError("Jump target not found before end of input")

                self._command_cache.append(cmd)

            if strategy(cmd, pos):
                self.jump_to_position(pos + offset)
                return

            pos += 1

    def probe_until(self, strategy: Callable[[Command, int], bool]) -> None:
        """Scan ahead via the parser to fill the cache until the strategy returns True.

        This is intended for forward-looking metadata registration (e.g. labels).
        It does NOT trigger a jump.
        """
        if not self._cache_enabled:
            raise RuntimeError("Cache must be enabled for probing")

        pos = len(self._command_cache)
        while True:
            # Check existing cache first (though usually called to look past it)
            if pos < len(self._command_cache):
                cmd = self._command_cache[pos]
            else:
                if not self._parser:
                    return  # Exhausted

                cmd = self._parser.next_command()
                if cmd is None:
                    return  # Exhausted

                self._command_cache.append(cmd)

            if strategy(cmd, pos):
                return

            pos += 1

    def jump_to_matching(
        self,
        start: str,
        end: str,
        alternative: Optional[str] = None,
        offset: int = 0,
    ) -> None:
        """Jump to the matching 'end' or 'alternative' marker, respecting nested 'start' markers."""
        depth = 1

        def strategy(cmd: Command, pos: int) -> bool:
            nonlocal depth
            if cmd.name == start:
                depth += 1
            elif cmd.name == end:
                depth -= 1
                if depth == 0:
                    return True
            elif depth == 1 and alternative and cmd.name == alternative:
                return True
            return False

        self.scan_and_jump(strategy, offset=offset)

    def _fill_cache_to(self, target_position: int) -> None:
        """Fill cache with commands up to target position."""
        if not self._parser:
            raise RuntimeError("No active parser for cache filling")

        while len(self._command_cache) <= target_position:
            cmd = self._parser.next_command()
            if cmd is None:
                break  # End of input

            self._command_cache.append(cmd)
