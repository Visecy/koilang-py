# KoiLang Python

Python bindings and runtime for [KoiLang](https://github.com/Visecy/koicore), a markup language designed for narrative content, interactive fiction, and dialogue-driven applications.

<p align="center">
  <img src="https://img.shields.io/pypi/v/koilang?style=flat-square&color=orange" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/pyversions/koilang?style=flat-square" alt="Python Versions">
  <img src="https://img.shields.io/github/license/Visecy/koilang-py?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/actions/workflow/status/Visecy/koilang-py/release.yaml?branch=master&style=flat-square" alt="Build Status">
</p>

## Overview

KoiLang separates **data** (story content, dialogue, commands) from **instructions** (how your application handles those commands). `koilang-py` provides two layers:

1.  **Core Layer (`koilang.core`)**: High-performance Native Python bindings for the `koicore` Rust kernel. Includes the streaming parser and writer.
2.  **Runtime Layer (`koilang.runtime`)**: A high-level, decoupled runtime featuring middleware support, environment stacks, and command caching for advanced control flow (jumps, loops).

## Installation

```bash
pip install koilang
```

## Quick Start

### Using the Runtime

The Runtime layer manages state and dispatches commands to a stack of environments.

```python
import io
from koilang.runtime import Runtime

class MyGame:
    def do_character(self, name, text):
        print(f"{name}: {text}")

    def at_text(self, text):
        print(f"[Narrative]: {text}")

runtime = Runtime()
runtime.env_enter(MyGame())
runtime.execute(io.StringIO("#character Alice \"Hi!\"\nRegular text here."))
```

### Programmatic Generation (Writer)

The `Writer` class allows you to generate KoiLang code programmatically.

```python
from koilang.runtime import Writer

with Writer("story.koi") as w:
    w.do_character("Alice", "Hello World")
    w.at_text("This is a story about a girl named Alice.")
```

**Note:** The `Writer` class also supports advanced formatting options and indentation management. See the [Advanced Usage](#writer-formatting-options) section for details.

## CLI Usage

You can run KoiLang files directly using the command line interface:

```bash
python -m koilang story.koi
```

**Note:** If the file path is not provided, the CLI will enter interactive mode (requires `prompt_toolkit` for enhanced REPL experience).

### Common Arguments

- `-e`, `--env`: Specify the root environment object (format: `module:Attribute`).
- `--command-threshold`: Minimum number of `#` to identify a command (default: 1).
- `--fail-on-unknown-command`: Raise error if a command handler is not found.
- `--skip-annotations`: Skip all annotation lines during parsing.
- `--preserve-empty-lines`: Preserve empty lines as empty text commands.
- `--preserve-indent`: Preserve leading indentation in text sections.

Example:
```bash
python -m koilang story.koi -e my_game:GameEnv --command-threshold 0
```

### Interactive Mode

When no file is provided, or when using the `-i`/`--interactive` flag, the CLI enters interactive mode with a rich REPL experience:

```bash
# Enter interactive mode directly
python -m koilang

# Enter interactive mode after executing a file
python -m koilang story.koi -i

# Load an environment and enter interactive mode
python -m koilang -e my_game:GameEnv
```

**Features:**

- **Enhanced REPL**: Powered by `prompt_toolkit` with syntax highlighting, auto-completion, and command history
- **Multi-line Input**: Support for multi-line commands using backslash continuation
- **Built-in Commands**: 
  - `#exit` or `#quit`: Exit interactive mode
  - `ctrl+d`: Also exits interactive mode
- **Environment Stack**: Dynamically manage environments during the session
- **Session Lifecycle**: Automatically handles `at_start` and `at_end` hooks

**Example Session:**

```bash
$ python -m koilang
KoiLang 2.0.0b1 on Python 3.10.18 (main, Jun  4 2025, 17:36:27) [Clang 20.1.4 ]
Type "#exit/#quit" or "ctrl+d" to exit interactive mode

koi> #character Alice "Hello!"
2026-03-14 23:44:56,642 koilang.__main__ WARNING - command 'character' not found
koi> Hello World
2026-03-14 23:45:16,474 koilang.__main__ INFO - text: 'Hello World'
koi> #exit
```

**Installation for Interactive Mode:**

To use the enhanced interactive mode with `prompt_toolkit`, install with the interactive extra:

```bash
pip install koilang[interactive]
```

Without `prompt_toolkit`, the CLI will fall back to basic stdin mode when input is piped.

## KoiLang Syntax

KoiLang is designed to be human-readable and expressive. For a full reference, see the [koicore documentation](https://docs.rs/koicore/latest/koicore/).

### Line Types

There are three types of lines in KoiLang, distinguished by their syntax:

- **Commands**: Lines starting with `#` (by default).
  ```koilang
  #character Alice "Hello"
  ```
- **Text**: Lines without a `#` prefix.
  ```koilang
  This is a regular text line.
  ```
- **Annotations**: Lines starting with `##` (or more `#` characters).
  ```koilang
  ## This is a comment
  ```

> **Important Concept**: In KoiLang, **text lines and annotation lines are essentially special commands**. They correspond to command names `@text` and `@annotation` respectively, and can be captured and handled through their corresponding handler methods `at_text` and `at_annotation`.

### Commands and Parameters

KoiLang supports rich parameter types that map naturally to Python:

**Basic Syntax:**
```koilang
#command_name [param1] [param2] ...
```

**Parameter Types:**

- **Positional**:
  ```koilang
  #cmd 1 "string" 3.14
  ```
  Python: `do_cmd(1, "string", 3.14)`

- **Named (Composite)**:
  ```koilang
  #cmd key(value)
  ```
  Python: `do_cmd(key="value")`

- **Lists**:
  ```koilang
  #cmd list(1, 2, 3)
  ```
  Python: `do_cmd(list=[1, 2, 3])`

- **Dicts**:
  ```koilang
  #cmd dict(a: 1, b: 2)
  ```
  Python: `do_cmd(dict={"a": 1, "b": 2})`

### Text Lines

Text lines (lines without `#` prefix) are **special commands** in KoiLang with the command name `@text`.

**Handling:**

In your environment class, handle text lines using the `at_text` method:

```python
class MyGame:
    def at_text(self, text):
        """Handle text line content.
        
        Corresponds to text lines in KoiLang (lines without # prefix)
        Command name: @text
        
        Args:
            text: The text line content
        """
        print(f"[Narrative]: {text}")
```

**Example:**

```koilang
#character Alice "Hello!"
This is a text line.      → triggers at_text("This is a text line.")
Another line here.        → triggers at_text("Another line here.")
```

**Note:** Each text line triggers a separate `at_text` call. If you have multiple consecutive text lines, each line will call `at_text` individually unless the parser is configured to preserve empty lines or indentation.

### Annotation Lines

Annotation lines (lines starting with `##` or more `#`) are also **special commands** in KoiLang with the command name `@annotation`.

**Handling:**

In your environment class, you can capture annotation lines using the `at_annotation` method (though annotations are usually ignored):

```python
class MyGame:
    def at_annotation(self, text):
        """Handle annotation line content.
        
        Corresponds to annotation lines in KoiLang (lines starting with ##)
        Command name: @annotation
        
        Args:
            text: The annotation content (without ## prefix)
        """
        print(f"[Comment]: {text}")
```

**Annotation Behavior:**

```koilang
## This is a single-line annotation    → Command name: @annotation
### This is also an annotation         → Command name: @annotation
#### Multi-level annotations work too  → Command name: @annotation

#command arg  ## Inline annotations are NOT supported
```

**Default Behavior:**

By default, annotation lines are ignored by the parser (no handler is triggered). You can control this behavior via `ParserConfig`:

```python
from koilang.model import ParserConfig
from koilang.runtime import Runtime

# Skip all annotations (improves performance for annotation-heavy files)
config = ParserConfig(skip_annotations=True)
runtime = Runtime(config=config)
```

**Note:** Unlike some languages, KoiLang does not support inline annotations. Annotations must be on their own line and start at the beginning (after any indentation).

### Command Threshold

The `command_threshold` parameter determines how KoiLang identifies line types based on the number of `#` characters:

| Threshold | `#text` | `##text` | `###text` | `####text` | no-prefix |
|-----------|---------|----------|-----------|------------|-----------|
| 0 | Annotation | Annotation | Annotation | Annotation | Command |
| 1 (default) | Command | Annotation | Annotation | Annotation | Text |
| 2 | Text | Command | Annotation | Annotation | Text |
| 3 | Text | Text | Command | Annotation | Text |

- **Lines with < threshold `#` characters** → Text line (triggers `@text` command)
- **Lines with = threshold `#` characters** → Command (triggers `do_<name>` handler)
- **Lines with > threshold `#` characters** → Annotation line (triggers `@annotation` command)

**Use Cases:**

- `threshold=1`: Standard KoiLang syntax (default)
- `threshold=2`: Allows embedding KoiLang in languages where `#` has special meaning (single `#` prefix treated as text)
- `threshold=3`: Strict command parsing for complex nested structures

**Example:**

```python
from koilang.model import ParserConfig
from koilang.runtime import Runtime

# Use threshold=2 for embedding in Markdown
config = ParserConfig(command_threshold=2)
runtime = Runtime(config=config)

# In this mode:
# # This is text (1 # = text line → @text)
# ##command arg  (2 # = command → do_command)
# ###comment    (3 # = annotation line → @annotation)
```

## Advanced Usage

### Basic Parsing with Core

The Core layer provides direct bindings to the Rust parser. It works with file-like objects or filenames.

```python
import io
from koilang.core import Parser

# Parse from a string using io.StringIO
content = io.StringIO("#character Alice \"Hello, world!\"\nThis is regular text.")
parser = Parser(content)

for command in parser:
    print(f"Command: {command.name}, Args: {command.args}, Kwargs: {command.kwargs}")
```

### Complex Environments & Middleware

```python
from koilang.runtime import Runtime, Middleware
import time

# Middleware to log command execution timing
def logger_middleware(runtime, cmd, next_handler):
    start = time.time()
    result = next_handler(cmd)
    print(f"Executed #{cmd.name} in {time.time() - start:.4f}s")
    return result

class Scene:
    def at_start(self): print("Scene started")
    def do_bg(self, name): print(f"Background: {name}")

class Character:
    def do_say(self, text): print(f"Alice: {text}")

runtime = Runtime(middleware=[logger_middleware])
runtime.env_enter(Scene())
runtime.env_enter(Character())  # Stack: [Scene, Character]

# Character environment handles 'say', Scene handles 'bg'
runtime.execute(io.StringIO("#bg Forest\n#say \"Wait!\""))
```

### Dynamic Environment Registration

You can also register environments dynamically during command execution, enabling more flexible control flow:

```python
from koilang.runtime import Runtime, env_enter, env_exit
import io

class DialogManager:
    """Manages dialog contexts dynamically."""
    
    def do_enter_dialog(self, character_name):
        """Enter a dialog context for a specific character."""
        # Dynamically push a new environment onto the stack
        env_enter(CharacterDialog(character_name))
    
    def do_exit_dialog(self):
        """Exit the current dialog context."""
        # Note: In real usage, you'd need to track the env instance
        # This is a simplified example
        pass

class CharacterDialog:
    """Environment for a specific character's dialog."""
    
    def __init__(self, name):
        self.name = name
    
    def do_say(self, text):
        print(f"{self.name}: {text}")
    
    def do_emote(self, emotion):
        print(f"[{self.name} {emotion}]")
    
    def do_end(self):
        """Exit this dialog environment."""
        env_exit(self)

runtime = Runtime()
runtime.env_enter(DialogManager())

script = """
#enter_dialog Alice
#say "Hello there!"
#emote smiles
#end
#enter_dialog Bob  
#say "Hi Alice!"
#end
"""
runtime.execute(io.StringIO(script))
```

The `env_enter()` and `env_exit()` functions allow you to manage the environment stack from within command handlers, enabling dynamic scoping and context management.

### Jumps and Labels

With caching enabled, you can jump around the script.

```python
from koilang.runtime import Runtime, context
import io

class FlowControl:
    def do_label(self, name):
        context.register_label(name)

    def do_jump(self, target):
        context.jump_to_label(target)

runtime = Runtime()
runtime.enable_cache()
runtime.env_enter(FlowControl())

script = """
#jump Target
#character Alice "This will be skipped"
#label Target
#character Alice "Hello from the future!"
"""
runtime.execute(io.StringIO(script))
```

### Executor (Programmatic Command Execution)

The `Executor` provides a programmatic interface for executing commands within a Runtime:

```python
from koilang.runtime import Runtime
import io

class GameEnv:
    def do_move(self, direction):
        print(f"Moving {direction}")
    
    def do_attack(self, target):
        print(f"Attacking {target}")

runtime = Runtime()
runtime.env_enter(GameEnv())

# Get an executor to programmatically trigger commands
executor = runtime.get_executor()

# Execute commands as if they came from a KoiLang file
executor.do_move("north")      # Same as: runtime.execute("#move north")
executor.do_attack("dragon")   # Same as: runtime.execute("#attack dragon")
```

**Targeted Execution:**

You can also execute commands on specific environments in the stack:

```python
class Player:
    def do_status(self):
        print("Player status: OK")

class Enemy:
    def do_status(self):
        print("Enemy status: Dead")

runtime = Runtime()
runtime.env_enter(Player())
runtime.env_enter(Enemy())

executor = runtime.get_executor()

# Execute on the most recent Player environment
executor[Player].do_status()   # "Player status: OK"

# Execute on the most recent Enemy environment  
executor[Enemy].do_status()    # "Enemy status: Dead"

# Execute on a specific instance by index
executor[Player, 0].do_status()  # First Player instance
executor[Player, -1].do_status() # Last Player instance
```

### Session Management

The `run_session()` context manager groups multiple executions into a single lifecycle session:

```python
from koilang.runtime import Runtime
import io

class GameEnv:
    def at_start(self):
        print("Game started")
    
    def at_end(self):
        print("Game ended")

runtime = Runtime()
runtime.env_enter(GameEnv())

# Lifecycle hooks (at_start/at_end) are only called once
with runtime.run_session():
    runtime.execute(io.StringIO("#cmd1"))
    runtime.execute(io.StringIO("#cmd2"))
# Prints: "Game started" (once) and "Game ended" (once)
```

This is useful when you want to execute multiple files or inputs while ensuring lifecycle hooks are only called at the beginning and end of the entire session.

### Writer Formatting Options

The `Writer` class supports fine-grained formatting control:

```python
from koilang.runtime import Writer
import io

# Basic usage
output = io.StringIO()
with Writer(output) as w:
    w.do_heading("Title")
    w.at_text("Content here")
```

**Indentation Management:**

```python
output = io.StringIO()
with Writer(output) as w:
    w.do_parent()
    
    # Increase indentation
    w.inc_indent()
    w.do_child1()
    w.do_child2()
    
    # Decrease indentation
    w.dec_indent()
    w.do_sibling()
    
    # Or use context manager
    with w.indent():
        w.do_nested()
        w.do_content()
```

**Temporary Formatting Options:**

```python
output = io.StringIO()
with Writer(output) as w:
    w.do_cmd1(1, 2)
    
    # Apply compact formatting to a block of commands
    with w.with_options(compact=True):
        w.do_cmd2(3, 4)
        w.do_cmd3(5, 6)
    
    # Back to default formatting
    w.do_cmd4(7, 8)
    
    # Fluent API for single commands
    w.with_options(compact=True).do_tight_cmd(1, 2)
    
    # Target specific commands
    with w.with_options(compact=True, target_commands=["cmd1", "cmd2"]):
        w.do_cmd1(1, 2)  # Uses compact formatting
        w.do_cmd2(3, 4)  # Uses compact formatting
        w.do_cmd3(5, 6)  # Uses default formatting
```

**Available Formatting Options:**

The `with_options()` method accepts any of the following parameters:

| Option | Type | Description |
|--------|------|-------------|
| `indent` | int | Number of spaces for indentation |
| `use_tabs` | bool | Use tabs instead of spaces |
| `compact` | bool | Remove unnecessary whitespace |
| `newline_before` | bool | Add newline before command |
| `newline_after` | bool | Add newline after command |
| `force_quotes_for_vars` | bool | Force quotes around literals |
| `number_format` | str | Custom format for integers |
| `float_format` | str | Custom format for floats |
| `newline_before_param` | bool | Newline before each parameter |
| `newline_after_param` | bool | Newline after each parameter |

For advanced configuration, you can also pass a `WriterConfig` object to the `Writer` constructor.

## Migration Guide (from legacy `kola`)

`koilang-py` is the successor to the legacy `kola` module. This guide helps you migrate from the old `kola` API to the new `koilang` API.

### Key Differences

| Feature | Legacy `kola` | New `koilang` |
| --- | --- | --- |
| **Main Class** | `KoiLang` | `Runtime` |
| **Decorators** | `@kola_command`, `@kola_text` | Convention-based (`do_name`, `at_name`) |
| **Parsing** | `parse()`, `parse_file()` | `execute()` (supports IO and files) |
| **Extension** | Inheritance based | Composition (Runtime + Env Stack) |
| **Text Handler** | `@kola_text` decorator | `at_text()` method |
| **Number Commands** | `@kola_number` decorator | `do_114()`, `do_1919()` methods |
| **Environment** | Nested `Environment` class | Any Python object with `do_`/`at_` methods |
| **CLI** | `python -m kola file.kola` | `python -m koilang file.koi` |

### Basic Migration Example

**Legacy `kola` code:**

```python
from kola import KoiLang, kola_command, kola_text

class MyScript(KoiLang):
    @kola_command
    def greet(self, name):
        print(f"Hello, {name}!")
    
    @kola_text
    def handle_text(self, text):
        print(f"Text: {text}")

# Usage
script = MyScript()
script.parse_file("script.kola")
```

**New `koilang` code:**

```python
from koilang.runtime import Runtime

class MyEnv:
    def do_greet(self, name):
        print(f"Hello, {name}!")
    
    def at_text(self, text):
        print(f"Text: {text}")

# Usage
runtime = Runtime()
runtime.env_enter(MyEnv())
runtime.execute("script.koi")
```

### Decorator Migration

**Legacy decorators:**

```python
from kola import kola_command, kola_text, kola_number

class OldStyle(KoiLang):
    @kola_command("custom_name")
    def my_func(self): ...
    
    @kola_text
    def handle_text(self, text): ...
    
    @kola_number
    def handle_number(self, num): ...
```

**New convention-based approach:**

```python
class NewStyle:
    # Method name becomes command name
    def do_custom_name(self): ...
    
    # Text handler uses at_text
    def at_text(self, text): ...
    
    # Number commands use do_<number>
    def do_114(self): ...  # Handles #114
    def do_1919(self): ... # Handles #1919
```

### Environment Migration

**Legacy nested environment:**

```python
from kola import KoiLang, Environment, kola_env_enter, kola_env_exit

class Main(KoiLang):
    class SubEnv(Environment):
        @kola_env_enter("enter")
        def enter(self): ...
        
        @kola_env_exit("exit")
        def exit(self): ...
```

**New environment stack approach:**

```python
from koilang.runtime import Runtime, env_enter, env_exit

class Main:
    def do_enter(self):
        env_enter(SubEnv())
    
    def do_exit(self):
        # Get current env and exit it
        pass

class SubEnv:
    pass

runtime = Runtime()
runtime.env_enter(Main())
```

### Command Name Customization

**Legacy:**

```python
@kola_command("open")
def file(self, path): ...
```

**New:**

Simply name your method with the desired command name:

```python
def do_open(self, path): ...  # Handles #open
```

Or use the standard name if it matches:

```python
def do_file(self, path): ...  # Handles #file
```

### Parser Configuration Migration

**Legacy:**

```python
from kola import KoiLang

class MyParser(KoiLang):
    def __init__(self):
        super().__init__()
        self.command_threshold = 2
```

**New:**

```python
from koilang.runtime import Runtime
from koilang.model import ParserConfig

config = ParserConfig(command_threshold=2)
runtime = Runtime(config=config)
```

### Writer Migration

**Legacy:**

```python
from kola.writer import FileWriter, StringWriter

# File output
with FileWriter("output.kola") as w:
    w.write_command("cmd", arg1, arg2)
    w.write_text("Some text")

# String output
sw = StringWriter()
sw.write_command("cmd", arg1)
result = sw.getvalue()
```

**New:**

```python
from koilang.runtime import Writer
import io

# File output
with Writer("output.koi") as w:
    w.do_cmd(arg1, arg2)
    w.at_text("Some text")

# String output
output = io.StringIO()
with Writer(output) as w:
    w.do_cmd(arg1)
result = output.getvalue()
```

### Complete Example: File Generator

Here's a complete migration example based on the file generator from the legacy docs:

**Legacy `kola`:**

```python
import os
from kola import KoiLang, kola_command, kola_text

class FastFile(KoiLang):
    @kola_command
    def file(self, path: str, encoding: str = "utf-8") -> None:
        if self._file:
            self._file.close()
        path_dir = os.path.dirname(path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        self._file = open(path, "w", encoding=encoding)
    
    @kola_command
    def end(self) -> None:
        if self._file:
            self._file.close()
            self._file = None
    
    @kola_text
    def text(self, text: str) -> None:
        if not self._file:
            raise OSError("write texts before the file open")
        self._file.write(text)
    
    def at_start(self) -> None:
        self._file = None
    
    def at_end(self) -> None:
        self.end()

# Usage
FastFile().parse_file("makefiles.kola")
```

**New `koilang`:**

```python
import os
from koilang.runtime import Runtime

class FastFile:
    def __init__(self):
        self._file = None
    
    def at_start(self):
        self._file = None
    
    def at_end(self):
        self.do_end()
    
    def do_file(self, path: str, encoding: str = "utf-8") -> None:
        if self._file:
            self._file.close()
        path_dir = os.path.dirname(path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        self._file = open(path, "w", encoding=encoding)
    
    def do_end(self) -> None:
        if self._file:
            self._file.close()
            self._file = None
    
    def at_text(self, text: str) -> None:
        if not self._file:
            raise OSError("write texts before the file open")
        self._file.write(text)

# Usage
runtime = Runtime()
runtime.env_enter(FastFile())
runtime.execute("makefiles.koi")
```

### Summary of Changes

1. **No more inheritance**: Instead of inheriting from `KoiLang`, you create plain Python classes
2. **Convention over configuration**: Use `do_` prefix for commands, `at_` prefix for special handlers
3. **Runtime-centric**: All execution goes through a `Runtime` instance
4. **Environment stack**: Use `env_enter()`/`env_exit()` instead of nested environment classes
5. **Unified parsing**: `execute()` method handles both strings and file-like objects
6. **Simpler writer**: More intuitive API with method-based command generation
