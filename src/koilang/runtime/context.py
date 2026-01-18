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


def wrap_handler(runtime: "Runtime", cmd: Command, handler: Callable[..., Any], context: Context | None = None) -> Any:
    if not context:
        context = copy_context()
    
    def inner() -> Any:
        runtime_ctx.set(runtime)
        command_ctx.set(cmd)
        return handler(*cmd.args, **cmd.kwargs)
    
    return context.run(inner)
