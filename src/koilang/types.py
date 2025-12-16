from typing import TypeAlias


BasicValueType: TypeAlias = str | int | float
CompositeValueType: TypeAlias = BasicValueType | list[BasicValueType] | dict[str, BasicValueType]
ParameterType: TypeAlias = BasicValueType | tuple[str, CompositeValueType]
