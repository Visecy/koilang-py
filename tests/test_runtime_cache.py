import io
import pytest
from koilang.runtime import (
    Runtime,
    enable_cache,
    disable_cache,
    get_current_position,
    register_label,
    jump_to_position,
    jump_to_label,
)


class CacheTestEnv:
    def __init__(self) -> None:
        self.executed_commands: list[str] = []
        self.positions: list[int] = []

    def do_cmd(self, value: str = "") -> None:
        self.executed_commands.append(f"cmd:{value}")
        if enable_cache:
            try:
                self.positions.append(get_current_position())
            except RuntimeError:
                pass  # Cache not enabled

    def do_label(self, name: str) -> None:
        register_label(name)

    def do_goto(self, label: str) -> None:
        jump_to_label(label)

    def do_jump(self, pos: int) -> None:
        jump_to_position(pos)

    def at_start(self) -> None:
        self.executed_commands.clear()
        self.positions.clear()


def test_cache_enable_disable() -> None:
    """Test cache state management."""
    runtime = Runtime()
    runtime.env_enter(CacheTestEnv())

    # Cache should be disabled by default
    assert not runtime.is_cache_enabled()

    # Enable cache
    runtime.enable_cache()
    assert runtime.is_cache_enabled()

    # Disable cache
    runtime.disable_cache()
    assert not runtime.is_cache_enabled()


def test_cache_stores_commands() -> None:
    """Verify commands are cached when cache is enabled."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n#cmd c\n"))

    # Check that commands were cached
    assert len(runtime._command_cache) == 3
    assert runtime._command_cache[0].name == "cmd"
    assert runtime._command_cache[1].name == "cmd"
    assert runtime._command_cache[2].name == "cmd"


def test_cache_cleared_on_disable() -> None:
    """Verify cleanup when cache is disabled."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n"))

    # Cache should have commands
    assert len(runtime._command_cache) > 0

    # Disable should clear everything
    runtime.disable_cache()
    assert len(runtime._command_cache) == 0
    assert len(runtime._label_index) == 0
    assert runtime._current_position == -1


def test_jump_to_position() -> None:
    """Test position-based jumps."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    # Jump forward to skip cmd b
    runtime.execute(io.StringIO("#cmd a\n#jump 3\n#cmd b\n#cmd c\n"))

    # Should execute: a, jump to position 3 (cmd c, skipping jump and b), then c
    # Positions: 0=cmd a, 1=jump 3, 2=cmd b, 3=cmd c
    assert env.executed_commands == ["cmd:a", "cmd:c"]


def test_jump_to_label() -> None:
    """Test label-based jumps."""

    class LoopEnv:
        def __init__(self) -> None:
            self.executed_commands: list[str] = []
            self.loop_count = 0

        def do_cmd(self, value: str = "") -> None:
            self.executed_commands.append(f"cmd:{value}")

        def do_label(self, name: str) -> None:
            # Only register if not already registered (for loop scenarios)
            try:
                register_label(name)
            except ValueError:
                pass  # Already registered

        def do_goto(self, label: str) -> None:
            # Only jump once to avoid infinite loop
            if self.loop_count < 1:
                self.loop_count += 1
                jump_to_label(label)

    env = LoopEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(
        io.StringIO("#cmd a\n#label start\n#cmd b\n#cmd c\n#goto start\n#cmd d\n")
    )

    # Should execute: a, register label at pos 1, b, c, jump to label (pos 1), b, c, goto (but skip), d
    assert env.executed_commands == [
        "cmd:a",
        "cmd:b",
        "cmd:c",
        "cmd:b",
        "cmd:c",
        "cmd:d",
    ]


def test_forward_jump_fills_cache() -> None:
    """Verify streaming behavior - forward jumps fill cache."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()

    # Start execution
    source = io.StringIO("#cmd a\n#jump 3\n#cmd b\n#cmd c\n#cmd d\n")
    runtime.execute(source)

    # After cmd a, jump to position 3 should fill cache with positions 0,1,2,3
    # Then execute from position 3 onwards
    # Execution: a, then jump fills cache (a,jump,b,c), execute from pos 3 (c), then d
    assert "cmd:a" in env.executed_commands
    assert "cmd:c" in env.executed_commands
    assert "cmd:d" in env.executed_commands


def test_backward_jump() -> None:
    """Test jumping to earlier positions."""

    class LoopEnv:
        def __init__(self) -> None:
            self.executed_commands: list[str] = []
            self.jump_count = 0

        def do_cmd(self, value: str = "") -> None:
            self.executed_commands.append(f"cmd:{value}")

        def do_jump(self, pos: int) -> None:
            # Only jump once to avoid infinite loop
            if self.jump_count < 1:
                self.jump_count += 1
                jump_to_position(pos)

    env = LoopEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n#jump 0\n#cmd c\n"))

    # Execute: a, b, jump to 0 (once), a, b, jump (skip), c
    assert env.executed_commands.count("cmd:a") == 2
    assert env.executed_commands.count("cmd:b") == 2
    assert env.executed_commands.count("cmd:c") == 1


def test_jump_without_cache_fails() -> None:
    """Error handling - jumps require cache to be enabled."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    # Cache not enabled, should raise error
    with pytest.raises(RuntimeError, match="Cache must be enabled"):
        runtime.jump_to_position(0)


def test_label_registration() -> None:
    """Test explicit label registration API."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#label start\n#cmd b\n"))

    # Label should be registered at position 1
    assert "start" in runtime._label_index
    assert runtime._label_index["start"] == 1


def test_label_duplicate_fails() -> None:
    """Test that duplicate labels raise an error."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()

    with pytest.raises(ValueError, match="already registered"):
        runtime.execute(io.StringIO("#label test\n#label test\n"))


def test_get_current_position() -> None:
    """Test position tracking."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n#cmd c\n"))

    # Positions should be tracked during execution
    assert len(env.positions) == 3
    assert env.positions == [0, 1, 2]


def test_cache_continuity() -> None:
    """Verify no gaps in cache."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n#cmd c\n"))

    # Cache should be continuous
    assert len(runtime._command_cache) == 3
    for i in range(3):
        assert runtime._command_cache[i] is not None


def test_position_without_cache_fails() -> None:
    """Test that getting position requires cache."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    with pytest.raises(RuntimeError, match="Cache must be enabled"):
        runtime.get_current_position()


def test_register_label_without_cache_fails() -> None:
    """Test that registering labels requires cache."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    with pytest.raises(RuntimeError, match="Cache must be enabled"):
        runtime.register_label("test")


def test_jump_beyond_available_commands() -> None:
    """Test jumping beyond available commands."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    runtime.enable_cache()

    # Jump to position 10 should fail if there aren't enough commands
    # The jump should try to fill cache but hit EOF and raise ValueError
    with pytest.raises(ValueError, match="Position 10 not available"):
        runtime.execute(io.StringIO("#cmd a\n#cmd b\n#jump 10\n"))


def test_dynamic_cache_switching() -> None:
    """Test enabling and disabling cache during execution."""

    class DynamicEnv:
        def __init__(self) -> None:
            self.executed = []

        def do_cmd(self, val: str) -> None:
            self.executed.append(val)

        def do_enable(self) -> None:
            enable_cache()

        def do_disable(self) -> None:
            disable_cache()

    env = DynamicEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    source = """
#cmd 1
#enable
#cmd 2
#cmd 3
#disable
#cmd 4
"""
    runtime.execute(io.StringIO(source.strip()))

    # Sequence:
    # 1. cmd 1: cache off
    # 2. enable: cache off during fetch, but handler calls enable_cache()
    # 3. cmd 2: cache on. Fetch -> append to cache[0]. current_pos=0.
    # 4. cmd 3: cache on. Fetch -> append to cache[1]. current_pos=1.
    # 5. disable: cache on during fetch. Fetch -> append to cache[2]. handler calls disable_cache() -> cache cleared, current_pos=-1.
    # 6. cmd 4: cache off. fetch -> next_command. current_pos=0.

    assert env.executed == [1, 2, 3, 4]
    # Internal check: when #disable was called, it cleared the cache.
    assert len(runtime._command_cache) == 0


def test_cache_disabled_by_default() -> None:
    """Test that cache is disabled by default and execution works normally."""
    env = CacheTestEnv()
    runtime = Runtime()
    runtime.env_enter(env)

    # Execute without cache
    runtime.execute(io.StringIO("#cmd a\n#cmd b\n#cmd c\n"))

    # Should execute normally
    assert env.executed_commands == ["cmd:a", "cmd:b", "cmd:c"]

    # Cache should be empty
    assert len(runtime._command_cache) == 0
