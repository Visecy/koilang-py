from pydantic import BaseModel
from koilang.core import NumberFormat


class ParserConfig(BaseModel):
    """Configuration options for the KoiLang parser."""
    command_threshold: int = 1
    skip_annotations: bool = False
    convert_number_command: bool = True
    skip_add_traceback: bool = False


class FormatterOptions(BaseModel, arbitrary_types_allowed=True):
    """Formatter options for the KoiLang writer."""
    indent: int = 4
    use_tabs: bool = False
    newline_before: bool = False
    newline_after: bool = False
    compact: bool = False
    force_quotes_for_vars: bool = False
    number_format: NumberFormat = NumberFormat.UNKNOWN
    newline_before_param: bool = False
    newline_after_param: bool = False
    should_override: bool = False


class WriterConfig(BaseModel):
    """Configuration options for the KoiLang writer."""
    global_option: FormatterOptions = FormatterOptions()
    command_options: dict[str, FormatterOptions] = {}
    command_threshold: int = 1
