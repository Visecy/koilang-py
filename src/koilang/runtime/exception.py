from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from .runtime import Runtime


class KoiRuntimeError(Exception):
    """
    Base exception for runtime errors
    """
    def __init__(self, *args: object, runtime: Optional["Runtime"] = None) -> None:
        self.runtime = runtime
        super().__init__(*args)


class KoiRuntimeCommandNotFoundError(KoiRuntimeError):
    """
    Exception thrown when an unknown command is encountered
    """
    pass



class JumpRequest(KoiRuntimeError):  # noqa: N818
    """Internal exception used to signal a jump request."""

    def __init__(self, position: int, *, runtime: "Runtime") -> None:
        self.position = position
        super().__init__(f"Jump to position {position}", runtime=runtime)

