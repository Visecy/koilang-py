from typing import TypeAlias, TypedDict


BasicValueType: TypeAlias = str | int | float
CompositeValueType: TypeAlias = BasicValueType | list[BasicValueType] | dict[str, BasicValueType]
ParameterType: TypeAlias = BasicValueType | tuple[str, CompositeValueType]


class ParserConfig(TypedDict, total=False):
    """Configuration options for the KoiLang parser."""
    command_threshold: int
    """Command threshold (default: 1)."""
    skip_annotations: bool
    """Whether to skip annotation commands (default: False)."""
    convert_number_command: bool
    """Whether to convert number commands (default: True)."""
    skip_add_traceback: bool
    """Whether to skip adding traceback information (default: False)."""
