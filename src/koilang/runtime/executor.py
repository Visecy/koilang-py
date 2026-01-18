from typing import Any, Type, TypeVar, Union, cast

from ..core import Command
from .runtime import Runtime

T = TypeVar("T")


class _EnvProxy:
    def __init__(self, runtime: Runtime, env: Any) -> None:
        self.runtime = runtime
        if env is self:
            raise ValueError("Environment cannot be self")
        self.env = env

    def __getattr__(self, name: str) -> Any:
        method = getattr(self.env, name)
        if not name.startswith("do_") and not name.startswith("on_"):
            return method
        elif not callable(method):
            return method

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cmd_name = self.runtime._get_command_name(name)
            params = _build_params(args, kwargs)
            cmd = Command(cmd_name, params)
            return self.runtime._execute_on_env(self.env, name, cmd)

        return wrapper


class Executor(Runtime):
    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_") or name.startswith("on_"):
            def virtual_command(*args: Any, **kwargs: Any) -> Any:
                cmd_name = self._get_command_name(name)
                params = _build_params(args, kwargs)
                cmd = Command(cmd_name, params)
                return self._dispatch(cmd)

            return virtual_command
        raise AttributeError(f"'Executor' object has no attribute '{name}'")

    def __getitem__(self, key: Union[Type[T], tuple[Type[T], int]]) -> T:
        if isinstance(key, tuple):
            env_type, index = key
        else:
            env_type, index = key, None

        # Find environment
        target_env = None

        # Searching logic
        # If index is provided, we search for the Nth instance of that type.
        # If index is None, we default to the *last* instance (top of stack) usually?
        # Test says: `executor[TestCommandSet]` -> access implicit.
        # Test says: `executor[TestEnv, 0]` -> first instance.
        # Test says: `executor[TestCommandSet, -1]` -> last instance.

        matches = [e for e in self.env_stack if isinstance(e, env_type)]

        if not matches:
            if index is not None:
                raise KeyError(
                    f"Environment of type {env_type} at index {index} not found"
                )
            # If not found and no index specified, fallback to using the type itself (e.g. for classmethods)
            target_env = env_type

        elif index is None:
            # Default behavior not explicitly specified in snippet but implied 'current' or 'last' usually.
            # In `executor[TestCommandSet]`, expected is likely the active one (last pushed).
            target_env = matches[-1]
        else:
            try:
                target_env = matches[index]
            except IndexError:
                raise KeyError(
                    f"Environment of type {env_type} at index {index} not found"
                )

        return cast(T, _EnvProxy(self, target_env))


def _build_params(args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[Any]:
    params = list(args)
    for k, v in kwargs.items():
        params.append((k, v))
    return params
