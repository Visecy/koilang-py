import io
from typing import Any
from koilang.core import Command
from koilang.runtime import (
    Runtime,
    register_label,
    jump_to_label,
    jump_to_matching,
    scan_and_jump,
)


class LoopEnv:
    def __init__(self, count: int, start_pos: int) -> None:
        self.count = count
        self.start_pos = start_pos
    
    @classmethod
    def do_repeat(cls, count: int) -> None:
        from koilang.runtime import env_enter, get_current_position

        # Start of loop is the command AFTER '#repeat'
        loop_env = cls(int(count), get_current_position() + 1)
        env_enter(loop_env)

    def do_endrepeat(self) -> None:
        from koilang.runtime import env_exit, jump_to_position

        if self.count > 1:
            self.count -= 1
            jump_to_position(self.start_pos)
        else:
            env_exit(self)


class AdvancedEnv:
    def __init__(self) -> None:
        self.executed = []
        self.vars = {}

    def do_cmd(self, val: Any) -> None:
        self.executed.append(val)

    def do_set(self, key: str, val: Any) -> None:
        self.vars[key] = val

    def do_label(self, name: str) -> None:
        register_label(name)

    def do_goto(self, label: str) -> None:
        def find_label(cmd: Command) -> str | None:
            if cmd.name == "label" and len(cmd.args) > 0:
                return str(cmd.args[0])
            return None

        jump_to_label(label, find_label=find_label)

    def _as_bool(self, val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            lv = val.lower()
            if lv == "true":
                return True
            if lv == "false":
                return False
        return bool(val)

    def do_if(self, cond: Any) -> None:
        if not self._as_bool(cond):
            jump_to_matching(start="if", end="endif", alternative="else", offset=1)

    def do_else(self) -> None:
        jump_to_matching(start="if", end="endif", offset=1)

    def do_endif(self) -> None:
        pass

    do_repeat = LoopEnv.do_repeat


def test_forward_label_jump() -> None:
    env = AdvancedEnv()
    runtime = Runtime(env)
    runtime.enable_cache()

    source = """
#goto later
#cmd 1
#label later
#cmd 2
"""
    runtime.execute(io.StringIO(source.strip()))
    assert env.executed == [2]


def test_nested_blocks() -> None:
    env = AdvancedEnv()
    runtime = Runtime(env)
    runtime.enable_cache()

    source = """
#if False
  #cmd skip1
  #if True
    #cmd skip2
  #endif
  #cmd skip3
#else
  #cmd exec1
  #if True
    #cmd exec2
  #endif
  #cmd exec3
#endif
#cmd final
"""
    runtime.execute(io.StringIO(source.strip()))
    assert env.executed == ["exec1", "exec2", "exec3", "final"]


def test_generic_scan_jump() -> None:
    def find_magic_number(cmd, pos) -> bool:
        return cmd.name == "magic" and cmd.args[0] == 42

    class MagicEnv(AdvancedEnv):
        def do_find_magic(self):
            scan_and_jump(find_magic_number)

        def do_magic(self, n):
            self.executed.append(f"magic:{n}")

        def do_end(self):
            self.executed.append("end")

    env = MagicEnv()
    runtime = Runtime(env)
    runtime.enable_cache()

    source = """
#find_magic
#cmd skip
#magic 10
#magic 42
#cmd end
"""
    runtime.execute(io.StringIO(source.strip()))
    assert env.executed == ["magic:42", "end"]


def test_nested_loops_and_ifs() -> None:
    env = AdvancedEnv()
    runtime = Runtime(env)
    runtime.enable_cache()

    source = """
#repeat 2
  #cmd R1
  #if True
    #cmd I1
  #endif
  #repeat 2
    #cmd R2
  #endrepeat
#endrepeat
"""
    runtime.execute(io.StringIO(source.strip()))
    # Loop 1 (2 times):
    #   R1, I1, Loop 2 (2 times: R2, R2)
    # Total: R1, I1, R2, R2, R1, I1, R2, R2
    assert env.executed == ["R1", "I1", "R2", "R2", "R1", "I1", "R2", "R2"]


def test_complex_interop() -> None:
    env = AdvancedEnv()
    runtime = Runtime(env)
    runtime.enable_cache()

    # Mix forward goto inside loop with if blocks
    source = """
#set skip_inner False
#repeat 2
  #cmd loop_start
  #if True
    #goto skip_point
  #endif
  #cmd should_be_skipped
  #label skip_point
  #cmd loop_end
#endrepeat
"""
    runtime.execute(io.StringIO(source.strip()))
    assert env.executed == ["loop_start", "loop_end", "loop_start", "loop_end"]


def test_multiple_label_probe() -> None:
    env = AdvancedEnv()

    # Verify that during the search for 'end', other labels are registered.
    source_with_probe = """
#goto end
#label L2
#cmd logic_L2
#label L3
#cmd logic_L3
#label end
#cmd finished
"""
    runtime = Runtime(env)
    runtime.enable_cache()
    runtime.execute(io.StringIO(source_with_probe.strip()))

    # 1. Verify primary jump reached its destination
    assert env.executed == ["finished"]

    # 2. Verify that L2 and L3 were registered during the probe
    # We check the internal label index directly for verification
    assert "L2" in runtime._label_index
    assert "L3" in runtime._label_index

    # Also verify they point to correct positions in cache
    l2_pos = runtime._label_index["L2"]
    assert runtime._command_cache[l2_pos].name == "label"
    assert runtime._command_cache[l2_pos].args[0] == "L2"

    l3_pos = runtime._label_index["L3"]
    assert runtime._command_cache[l3_pos].name == "label"
    assert runtime._command_cache[l3_pos].args[0] == "L3"
