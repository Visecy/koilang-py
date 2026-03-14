import io
from typing import Any, Callable
from koilang.runtime import Executor, Runtime, env_enter, env_exit
from koilang.core import Command
from koilang.runtime.context import current_command
from koilang.runtime.exception import KoiRuntimeCommandNotFoundError
import pytest


class TestEnv:
    @classmethod
    def do_enter(cls) -> None:
        env_enter(cls())

    def do_cmd(self, cnt: int = 1) -> None:
        pass

    def do_exit(self) -> None:
        env_exit(self)


class TestCommandSet:
    def __init__(self) -> None:
        self.cmd_count = 0
        self.last_text: str | None = None

    def do_cmd(self, cnt: int = 1) -> None:
        self.cmd_count += cnt

    do_enter = TestEnv.do_enter

    def at_text(self, text: str) -> None:
        self.last_text = text

    def at_start(self) -> None:
        self.cmd_count = 0
        self.last_text = None


def test_runtime() -> None:
    runtime = Runtime()
    runtime.env_enter(TestCommandSet())

    txt = "#cmd"
    runtime.execute(io.StringIO(txt))
    assert len(runtime.env_stack) == 1
    assert isinstance(runtime.env_stack[0], TestCommandSet)
    assert runtime.env_stack[0].cmd_count == 1

    txt = "#cmd 2\nHello world!"
    runtime.execute(io.StringIO(txt))
    assert len(runtime.env_stack) == 1
    assert isinstance(runtime.env_stack[0], TestCommandSet)
    assert runtime.env_stack[0].cmd_count == 2
    assert runtime.env_stack[0].last_text == "Hello world!"


def test_runtime_env() -> None:
    runtime = Runtime()
    runtime.env_enter(TestCommandSet())

    runtime.execute(io.StringIO("#cmd\n#enter\n#cmd\n"))
    assert len(runtime.env_stack) == 2
    assert isinstance(runtime.env_stack[1], TestEnv)
    assert isinstance(runtime.env_stack[0], TestCommandSet)
    # The first env (CommandSet) processed the first cmd
    assert runtime.env_stack[0].cmd_count == 1
    # inner env has do_cmd but it's empty, so nothing happens to cmd_count (which belongs to outer env)

    runtime.execute(io.StringIO("#exit\n#cmd\n"))
    assert len(runtime.env_stack) == 1
    assert isinstance(runtime.env_stack[0], TestCommandSet)
    assert runtime.env_stack[0].cmd_count == 1


def test_middleware() -> None:
    log = []

    def logger_middleware(runtime: Runtime, cmd: Command, next_handler: Callable[[Command], Any]) -> Any:
        log.append(f"before {cmd.name}")
        ret = next_handler(cmd)
        log.append(f"after {cmd.name}")
        return ret

    def modifier_middleware(runtime: Runtime, cmd: Command, next_handler: Callable[[Command], Any]) -> Any:
        if cmd.name == "cmd":
            # Modify args or replace command
            pass
        return next_handler(cmd)

    runtime = Runtime(middleware=[logger_middleware, modifier_middleware])
    runtime.env_enter(TestCommandSet())
    runtime.execute(io.StringIO("#cmd\n"))

    assert log == ["before cmd", "after cmd"]


def test_middleware_modify_command() -> None:
    log = []

    def modifier_middleware(runtime: Runtime, cmd: Command, next_handler: Callable[[Command], Any]) -> Any:
        if cmd.name == "cmd":
            new_cmd = Command(name="other", params=cmd.params)
            return next_handler(new_cmd)
        return next_handler(cmd)

    class TestEnv:
        def do_cmd(self) -> None:
            log.append("cmd")

        def do_other(self) -> None:
            log.append("other")

    runtime = Runtime(middleware=[modifier_middleware])
    runtime.env_enter(TestEnv())
    runtime.execute(io.StringIO("#cmd"))

    assert log == ["other"]


def test_dependency_command() -> None:
    class CmdEnv:
        def do_check(self) -> None:
            self.last_cmd_name = current_command().name

    env = CmdEnv()
    runtime = Runtime()
    runtime.env_enter(env)
    runtime.execute(io.StringIO("#check"))
    runtime.execute(io.StringIO("#check"))
    assert env.last_cmd_name == "check"


def test_positional_only() -> None:
    class PosEnv:
        def do_p(self, x: int, /, y: int) -> None:
            self.res = (x, y)

    env = PosEnv()
    runtime = Runtime()
    runtime.env_enter(env)
    runtime.execute(io.StringIO("#p 1 2"))
    assert env.res == (1, 2)


def test_executor() -> None:
    runtime = Runtime()
    runtime.env_enter(TestCommandSet())
    executor = runtime.get_executor()
    assert runtime is executor.runtime

    executor.do_cmd()  # as runtime.execute("#cmd")
    assert len(runtime.env_stack) == 1
    assert isinstance(runtime.env_stack[0], TestCommandSet)
    assert runtime.env_stack[0].cmd_count == 1

    executor[TestCommandSet].do_cmd(cnt=2)  # as runtime.execute("#cmd cnt(2)")
    assert runtime.env_stack[0].cmd_count == 3

    executor[TestEnv].do_enter()
    # equals to `executor[TestCommandSet].do_enter()`
    assert len(executor.env_stack) == 2
    assert isinstance(executor.env_stack[1], TestEnv)
    assert isinstance(executor.env_stack[0], TestCommandSet)

    executor[TestEnv].do_cmd()
    assert executor.env_stack[0].cmd_count == 3
    executor[TestCommandSet, -1].do_cmd()  # execute on last TestCommandSet environment
    assert executor.env_stack[0].cmd_count == 4

    executor[TestEnv, 0].do_exit()  # execute on first TestEnv environment
    assert len(executor.env_stack) == 1
    assert isinstance(executor.env_stack[0], TestCommandSet)
    assert executor.env_stack[0].cmd_count == 4


def test_annotation_without_handler() -> None:
    """Test that @annotation commands are silently skipped when no handler exists."""
    runtime = Runtime()
    runtime.env_enter(TestCommandSet())
    
    # Should not raise exception even without at_annotation handler
    runtime.execute(io.StringIO("## This is an annotation\n#cmd"))
    assert runtime.env_stack[0].cmd_count == 1


def test_other_command_without_handler() -> None:
    """Test that other commands still raise exception when handler not found."""
    runtime = Runtime()
    runtime.env_enter(TestCommandSet())
    
    # Should raise KoiRuntimeCommandNotFoundError for unknown commands
    with pytest.raises(KoiRuntimeCommandNotFoundError):
        runtime.execute(io.StringIO("#unknown_command"))


def test_annotation_with_handler() -> None:
    """Test that @annotation commands are handled correctly when handler exists."""
    annotations = []
    
    class AnnotationHandler:
        def at_annotation(self, text: str) -> None:
            annotations.append(text)
    
    runtime = Runtime()
    runtime.env_enter(AnnotationHandler())
    
    runtime.execute(io.StringIO("## Annotation 1\n## Annotation 2"))
    assert annotations == ["Annotation 1", "Annotation 2"]
