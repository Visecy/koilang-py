from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """Configuration options for the KoiLang parser.

    Attributes:
        command_threshold: Minimum number of '#' characters required to identify a command.
            - 1 (default): `#cmd` is a command, `##anno` is an annotation.
            - 0: All non-prefixed lines are commands.
        skip_annotations: If True, the parser will ignore all annotation lines.
        convert_number_command: If True, numeric commands (e.g., `#123`) are automatically converted.
        skip_add_traceback: If True, suppresses the addition of Python-level traceback info to errors.
        preserve_empty_lines: If True, empty lines are preserved as empty text commands instead of being skipped.
        preserve_indent: If True, leading indentation in text sections is preserved.
    """

    command_threshold: int = 1
    skip_annotations: bool = False
    convert_number_command: bool = True
    skip_add_traceback: bool = False
    preserve_empty_lines: bool = False
    preserve_indent: bool = False


@dataclass
class FormatterOptions:
    """Fine-grained formatting options for the KoiLang writer.

    These options can be applied globally via WriterConfig or specifically to certain commands
    or parameters during the writing process.

    Attributes:
        indent: Number of spaces for indentation (if using spaces).
        use_tabs: Whether to use tab characters for indentation instead of spaces.
        newline_before: Ensure a newline exists before this command.
        newline_after: Ensure a newline exists after this command.
        compact: If True, removes unnecessary whitespace.
        force_quotes_for_vars: Force quotes around literal values that would otherwise be unquoted.
        number_format: Custom format string for integers.
        float_format: Custom format string for floating point numbers.
        newline_before_param: Place each parameter on a new line before writing it.
        newline_after_param: Place a newline after each parameter.
        should_override: Internal flag to indicate these options should override parent settings.
    """

    indent: int = 4
    use_tabs: bool = False
    newline_before: bool = False
    newline_after: bool = False
    compact: bool = False
    force_quotes_for_vars: bool = False
    number_format: str = ""
    float_format: str = ""
    newline_before_param: bool = False
    newline_after_param: bool = False
    should_override: bool = False


@dataclass
class WriterConfig:
    """High-level configuration for the KoiLang writer.

    Attributes:
        global_options: Default FormatterOptions applied to all commands.
        command_options: Dictionary mapping command names to specific FormatterOptions.
        command_threshold: The threshold level to use when writing commands (e.g., 1 for '#').
    """

    global_options: FormatterOptions = field(default_factory=FormatterOptions)
    command_options: dict[str, FormatterOptions] = field(default_factory=dict)
    command_threshold: int = 1
