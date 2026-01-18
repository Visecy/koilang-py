import io
from typing import Any, Callable
from koilang.runtime import Executor, Runtime, env_enter, env_exit
from koilang.core import Command
from koilang.runtime.context import current_command


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

    def on_text(self, text: str) -> None:
        self.last_text = text

    def on_start(self) -> None:
        self.cmd_count = 0
        self.last_text = None


def test_runtime() -> None:
    runtime = Runtime(TestCommandSet())

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
    runtime = Runtime(TestCommandSet())

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

    def logger_middleware(
        runtime: Runtime, cmd: Command, next_handler: Callable[[], Any]
    ) -> Any:
        log.append(f"before {cmd.name}")
        ret = next_handler()
        log.append(f"after {cmd.name}")
        return ret

    def modifier_middleware(
        runtime: Runtime, cmd: Command, next_handler: Callable[[], Any]
    ) -> Any:
        if cmd.name == "cmd":
            # Modify args if list is mutable? or just check.
            # core.Command args are properties, usually we'd modify params logic or similar
            pass
        return next_handler()

    runtime = Runtime(
        TestCommandSet(), middleware=[logger_middleware, modifier_middleware]
    )
    runtime.execute(io.StringIO("#cmd\n"))

    assert log == ["before cmd", "after cmd"]


def test_dependency_command() -> None:
    class CmdEnv:
        def do_check(self) -> None:
            self.last_cmd_name = current_command().name

    env = CmdEnv()
    runtime = Runtime(env)
    runtime.execute(io.StringIO("#check"))
    runtime.execute(io.StringIO("#check"))
    assert env.last_cmd_name == "check"


def test_positional_only() -> None:
    class PosEnv:
        def do_p(self, x: int, /, y: int) -> None:
            self.res = (x, y)

    env = PosEnv()
    runtime = Runtime(env)
    runtime.execute(io.StringIO("#p 1 2"))
    assert env.res == (1, 2)


def test_executor() -> None:
    executor = Executor(TestCommandSet())

    executor.do_cmd()  # as runtime.execute("#cmd")
    assert len(executor.env_stack) == 1
    assert isinstance(executor.env_stack[0], TestCommandSet)
    assert executor.env_stack[0].cmd_count == 1

    executor[TestCommandSet].do_cmd(cnt=2)  # as runtime.execute("#cmd cnt(2)")
    assert executor.env_stack[0].cmd_count == 3

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
