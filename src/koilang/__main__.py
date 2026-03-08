import argparse
import importlib
import importlib.metadata
from io import StringIO
import logging
import sys
from typing import Any, Callable, Optional

from .core import Command
from .model import ParserConfig
from .runtime import Runtime
from .runtime.exception import KoiRuntimeCommandNotFoundError

sys.path.append(".")
logger = logging.getLogger("koilang.__main__")


class InteractiveExitError(EOFError):
    """Exception raised to exit interactive mode."""
    pass


class InteractiveEnv:
    """Interactive environment with built-in commands implemented via runtime mechanism."""

    def do_exit(self) -> None:
        """Handle the exit command to terminate interactive mode."""
        raise InteractiveExitError()

    def do_quit(self) -> None:
        """Handle the quit command to terminate interactive mode."""
        raise InteractiveExitError()


def ignore_missing_command_middleware(runtime: Runtime, command: Command, next_handler: Callable[[Command], Any]) -> Any:
    try:
        return next_handler(command)
    except KoiRuntimeCommandNotFoundError:
        if command.name == "@text":
            logger.info(f"text: {''.join(command.args)!r}")
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

    if isinstance(obj, type):
        return obj()
    return obj


def is_interactive_input() -> bool:
    """Check if stdin is connected to a TTY."""
    return sys.stdin.isatty()


def get_version() -> str:
    """Get the koilang package version."""
    try:
        return importlib.metadata.version("koilang")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def print_banner() -> None:
    """Print the interactive mode banner with version and copyright info."""
    print(f"KoiLang {get_version()} on Python {sys.version_info}")
    print('Type "#exit/#quit" or "ctrl+d" to exit interactive mode')
    print()


def run_interactive_mode(
    config: ParserConfig,
    middleware: list[Callable[..., Any]],
    file_path: Optional[str] = None,
    env_spec: Optional[str] = None,
    show_banner: bool = True,
) -> None:
    """Run interactive REPL mode using prompt_toolkit."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.history import InMemoryHistory
    except ImportError:
        print(
            "Interactive mode requires prompt_toolkit. "
            "Please install it with: pip install koilang[interactive]",
            file=sys.stderr,
        )
        sys.exit(1)

    runtime = Runtime(config=config, middleware=middleware)
    interactive_env = InteractiveEnv()
    runtime.env_enter(interactive_env)

    if env_spec:
        try:
            env = load_env_object(env_spec)
            runtime.env_enter(env)
        except Exception:
            logger.error("error loading environment", exc_info=True)
            sys.exit(1)

    if file_path is not None:
        try:
            runtime.execute(file_path)
        except Exception:
            logger.error("error executing file before interactive mode", exc_info=True)
            sys.exit(1)

    if show_banner:
        print_banner()

    session: PromptSession[str] = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
    )

    try:
        while True:
            try:
                lines: list[str] = []
                while True:
                    if lines:
                        prompt = ".... "
                    else:
                        prompt = "koi> "
                    line = session.prompt(prompt)
                    lines.append(line)
                    if not line.endswith("\\"):
                        break
                full_input = "\n".join(lines)
                runtime.execute(StringIO(full_input))
            except EOFError:
                break
            except Exception:
                logger.error("error executing command", exc_info=True)
            except KeyboardInterrupt:
                continue
    finally:
        runtime.env_exit(interactive_env)


def run_stdin_mode(
    config: ParserConfig,
    middleware: list[Callable[..., Any]],
    file_path: Optional[str] = None,
    env_spec: Optional[str] = None,
) -> None:
    """Run in stdin mode - read from stdin until EOF without prompts."""
    runtime = Runtime(config=config, middleware=middleware)

    interactive_env = InteractiveEnv()
    runtime.env_enter(interactive_env)

    if env_spec:
        try:
            env = load_env_object(env_spec)
            runtime.env_enter(env)
        except Exception:
            logger.error("error loading environment", exc_info=True)
            sys.exit(1)

    if file_path is not None:
        try:
            runtime.execute(file_path)
        except InteractiveExitError:
            pass
        except Exception:
            logger.error("error executing file", exc_info=True)
            sys.exit(1)

    try:
        runtime.execute(sys.stdin)
    except InteractiveExitError:
        pass
    except Exception:
        logger.error("error executing stdin input", exc_info=True)
        sys.exit(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Run a KoiLang file or enter interactive mode.")
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        help="The koilang file to run (optional: if not provided, enters interactive mode)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode even if file is provided",
    )
    parser.add_argument(
        "-e",
        "--env",
        type=str,
        help="The python object to use as root_env, in format <module_path>:<attribute>",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress banner and version information in interactive mode",
    )

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

    config = ParserConfig(
        command_threshold=args.command_threshold,
        skip_annotations=args.skip_annotations,
        convert_number_command=not args.no_convert_number_command,
        skip_add_traceback=args.skip_add_traceback,
        preserve_empty_lines=args.preserve_empty_lines,
        preserve_indent=args.preserve_indent,
    )

    middleware: list[Callable[..., Any]] = []
    if not args.fail_on_unknown_command:
        middleware.append(ignore_missing_command_middleware)

    should_interactive = args.interactive or args.file is None

    if should_interactive:
        show_banner = not args.quiet
        if is_interactive_input():
            run_interactive_mode(
                config=config,
                middleware=middleware,
                file_path=args.file,
                env_spec=args.env,
                show_banner=show_banner,
            )
        else:
            run_stdin_mode(
                config=config,
                middleware=middleware,
                file_path=args.file,
                env_spec=args.env,
            )
        return

    if args.env:
        try:
            runtime = Runtime(config=config, middleware=middleware)
            env = load_env_object(args.env)
            runtime.env_enter(env)
            runtime.execute(args.file)
        except Exception:
            logger.error("error loading environment", exc_info=True)
            sys.exit(1)
    else:
        try:
            runtime = Runtime(config=config, middleware=middleware)
            runtime.execute(args.file)
        except Exception:
            logger.error("error executing koilang file", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
