import argparse
import importlib
import logging
import sys
from typing import Any, Callable

from .core import Command
from .model import ParserConfig
from .runtime import Runtime
from .runtime.exception import KoiRuntimeCommandNotFoundError

sys.path.append(".")
logger = logging.getLogger("koilang.__main__")


def ignore_missing_command_middleware(runtime: Runtime, command: Command, next_handler: Callable[[Command], Any]) -> Any:
    try:
        return next_handler(command)
    except KoiRuntimeCommandNotFoundError:
        if command.name == "@text":
            logger.warning("text handler not found, skipping")
        elif command.name == "@annotation":
            logger.warning("annotation handler not found, skipping")
        else:
            logger.warning(f"command '{command.name}' not found")


def load_env_object(env_spec: str) -> Any:
    """Load an environment object from a string format <module>:<attribute>."""
    if ":" not in env_spec:
        raise ValueError("Environment must be specified as <module_path>:<attribute_name>")

    module_name, attr_name = env_spec.split(":", 1)

    module = importlib.import_module(module_name)
    if not hasattr(module, attr_name):
        raise AttributeError(f"Module '{module_name}' has no attribute '{attr_name}'")

    obj = getattr(module, attr_name)

    # If it's a class, instantiate it
    if isinstance(obj, type):
        return obj()
    return obj


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Run a KoiLang file.")
    parser.add_argument("file", type=str, help="The koilang file to run")
    parser.add_argument(
        "-e",
        "--env",
        type=str,
        help="The python object to use as root_env, in format <module_path>:<attribute>",
    )

    # ParserConfig options
    parser.add_argument(
        "--command-threshold",
        type=int,
        default=1,
        help="Minimum number of '#' characters required to identify a command (default: 1)",
    )
    parser.add_argument(
        "--skip-annotations",
        action="store_true",
        help="If set, the parser will ignore all annotation lines",
    )
    parser.add_argument(
        "--no-convert-number-command",
        action="store_true",
        help="If set, numeric commands (e.g., #123) are NOT automatically converted",
    )
    parser.add_argument(
        "--skip-add-traceback",
        action="store_true",
        help="If set, suppresses the addition of Python-level traceback info to errors",
    )
    parser.add_argument(
        "--preserve-empty-lines",
        action="store_true",
        help="If set, empty lines are preserved as empty text commands instead of being skipped",
    )
    parser.add_argument(
        "--preserve-indent",
        action="store_true",
        help="If set, leading indentation in text sections is preserved",
    )

    parser.add_argument(
        "--fail-on-unknown-command",
        action="store_true",
        help="If set, the runtime will raise an error when an unknown command is encountered",
    )

    args = parser.parse_args()

    # Construct ParserConfig
    config = ParserConfig(
        command_threshold=args.command_threshold,
        skip_annotations=args.skip_annotations,
        convert_number_command=not args.no_convert_number_command,
        skip_add_traceback=args.skip_add_traceback,
        preserve_empty_lines=args.preserve_empty_lines,
        preserve_indent=args.preserve_indent,
    )

    middleware = []
    if not args.fail_on_unknown_command:
        middleware.append(ignore_missing_command_middleware)

    try:
        runtime = Runtime(config=config, middleware=middleware)

        if args.env:
            try:
                env = load_env_object(args.env)
                runtime.env_enter(env)
            except Exception:
                logger.error("error loading environment", exc_info=True)
                sys.exit(1)

        runtime.execute(args.file)

    except Exception:
        logger.error("error executing koilang file", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
