from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """Configuration options for the KoiLang parser."""

    command_threshold: int = 1
    skip_annotations: bool = False
    convert_number_command: bool = True
    skip_add_traceback: bool = False
    preserve_empty_lines: bool = False
    preserve_indent: bool = False


@dataclass
class FormatterOptions:
    """Formatter options for the KoiLang writer."""

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
    """Configuration options for the KoiLang writer."""

    global_options: FormatterOptions = field(default_factory=FormatterOptions)
    command_options: dict[str, FormatterOptions] = field(default_factory=dict)
    command_threshold: int = 1
