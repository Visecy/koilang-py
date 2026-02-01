from contextvars import Context, ContextVar, copy_context
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..core import Command

if TYPE_CHECKING:
    from .runtime import Runtime


runtime_ctx = ContextVar[Optional["Runtime"]]("runtime")
command_ctx = ContextVar[Optional[Command]]("command")


def current_runtime() -> "Runtime":
    runtime = runtime_ctx.get()
    if runtime is None:
        raise RuntimeError("No runtime found")
    return runtime


def current_command() -> Command:
    command = command_ctx.get()
    if command is None:
        raise RuntimeError("No command found")
    return command


def env_enter(env: Any) -> None:
    runtime = current_runtime()
    runtime.env_enter(env)


def env_exit(env: Any) -> None:
    runtime = current_runtime()
    runtime.env_exit(env)


def enable_cache() -> None:
    """Enable command caching in the current runtime."""
    runtime = current_runtime()
    runtime.enable_cache()


def disable_cache() -> None:
    """Disable command caching in the current runtime."""
    runtime = current_runtime()
    runtime.disable_cache()


def get_current_position() -> int:
    """Get the current execution position."""
    runtime = current_runtime()
    return runtime.get_current_position()


def register_label(label: str, position: Optional[int] = None) -> None:
    """Register a label at the specified position (default: current)."""
    runtime = current_runtime()
    runtime.register_label(label, position)


def jump_to_position(position: int) -> None:
    """Jump to a specific position in the cached commands."""
    runtime = current_runtime()
    runtime.jump_to_position(position)


def jump_to_label(
    label: str, find_label: Optional[Callable[[Command], str | None]] = None
) -> None:
    """Jump to a labeled command."""
    runtime = current_runtime()
    runtime.jump_to_label(label, find_label=find_label)


def scan_and_jump(strategy: Callable[[Command, int], bool], offset: int = 0) -> None:
    """Scan ahead and jump to the first command matching the strategy."""
    runtime = current_runtime()
    runtime.scan_and_jump(strategy, offset=offset)


def probe_until(strategy: Callable[[Command, int], bool]) -> None:
    """Scan ahead via the parser to fill the cache without jumping."""
    runtime = current_runtime()
    runtime.probe_until(strategy)


def jump_to_matching(
    start: str, end: str, alternative: Optional[str] = None, offset: int = 0
) -> None:
    """Jump to the matching marker, respecting nesting."""
    runtime = current_runtime()
    runtime.jump_to_matching(start, end, alternative, offset=offset)


def wrap_handler(
    runtime: "Runtime",
    cmd: Command,
    handler: Callable[..., Any],
    context: Context | None = None,
) -> Any:
    if not context:
        context = copy_context()

    def inner() -> Any:
        runtime_ctx.set(runtime)
        command_ctx.set(cmd)
        return handler(*cmd.args, **cmd.kwargs)

    return context.run(inner)
