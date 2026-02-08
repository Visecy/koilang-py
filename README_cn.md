# KoiLang Python

[KoiLang](https://github.com/Visecy/koicore) 的 Python 绑定和运行时，KoiLang 是一种专为叙事内容、交互式小说和对话驱动应用设计的标记语言。

<p align="center">
  <img src="https://img.shields.io/pypi/v/koilang?style=flat-square&color=orange" alt="PyPI 版本">
  <img src="https://img.shields.io/pypi/pyversions/koilang?style=flat-square" alt="Python 版本">
  <img src="https://img.shields.io/github/license/Visecy/koilang-py?style=flat-square" alt="许可证">
  <img src="https://img.shields.io/github/actions/workflow/status/Visecy/koilang-py/release.yaml?branch=master&style=flat-square" alt="构建状态">
</p>

## 概述

KoiLang 将**数据**（故事内容、对话、命令）与**指令**（应用程序如何处理这些命令）分离。`koilang-py` 提供两层架构：

1. **核心层 (`koilang.core`)**：高性能的 `koicore` Rust 内核原生 Python 绑定。包含流式解析器和写入器。
2. **运行时层 (`koilang.runtime`)**：高级解耦运行时，支持中间件、环境栈和命令缓存，用于实现高级控制流（跳转、循环）。

## 安装

```bash
pip install koilang
```

## 快速开始

### 使用运行时

运行时层管理状态并将命令分派到环境栈。

```python
import io
from koilang.runtime import Runtime

class MyGame:
    def do_character(self, name, text):
        print(f"{name}: {text}")

    def on_text(self, text):
        print(f"[叙述]: {text}")

runtime = Runtime()
runtime.env_enter(MyGame())
runtime.execute(io.StringIO("#character Alice \"Hi!\"\nRegular text here."))
```

### 程序化生成（写入器）

`Writer` 类允许你以编程方式生成 KoiLang 代码。

```python
from koilang.runtime import Writer

with Writer("story.koi") as w:
    w.do_character("Alice", "Hello World")
    w.on_text("This is a story about a girl named Alice.")
```

## CLI 用法

你可以使用命令行接口直接运行 KoiLang 文件：

```bash
python -m koilang story.koi
```

### 常用参数

- `-e`, `--env`：指定根环境对象（格式：`module:Attribute`）。
- `--command-threshold`：识别命令所需的最少 `#` 数量（默认：1）。
- `--fail-on-unknown-command`：如果找不到命令处理器则报错。

示例：
```bash
python -m koilang story.koi -e my_game:GameEnv --command-threshold 0
```

## KoiLang 语法

KoiLang 设计为人可读且富有表现力。完整参考请参阅 [koicore 文档](https://docs.rs/koicore/latest/koicore/)。

### 行类型

KoiLang 中有三种类型的行，通过语法区分：

- **命令**：以 `#` 开头的行（默认）。
  ```koilang
  #character Alice "Hello"
  ```
- **文本**：没有 `#` 前缀的行。
  ```koilang
  This is a regular text line.
  ```
- **注释**：以 `##`（或更多 `#` 字符）开头的行。
  ```koilang
  ## This is a comment
  ```

> **重要概念**：在 KoiLang 中，**文本行和注释行本质上是特殊的命令**。它们分别对应命令名 `@text` 和 `@annotation`，可以通过对应的处理器方法 `on_text` 和 `on_annotation` 来捕获和处理。

### 命令和参数

KoiLang 支持丰富的参数类型，可自然映射到 Python：

**基本语法：**
```koilang
#command_name [param1] [param2] ...
```

**参数类型：**

- **位置参数**：
  ```koilang
  #cmd 1 "string" 3.14
  ```
  Python: `do_cmd(1, "string", 3.14)`

- **命名（复合）参数**：
  ```koilang
  #cmd key(value)
  ```
  Python: `do_cmd(key="value")`

- **列表**：
  ```koilang
  #cmd list(1, 2, 3)
  ```
  Python: `do_cmd(list=[1, 2, 3])`

- **字典**：
  ```koilang
  #cmd dict(a: 1, b: 2)
  ```
  Python: `do_cmd(dict={"a": 1, "b": 2})`

### 文本行

文本行（没有 `#` 前缀的行）在 KoiLang 中是**特殊命令**，命令名为 `@text`。

**处理方式：**

在你的环境类中，使用 `on_text` 方法处理文本行：

```python
class MyGame:
    def on_text(self, text):
        """处理文本行内容。
        
        对应 KoiLang 中的文本行（没有 # 前缀的行）
        命令名：@text
        
        Args:
            text: 文本行内容
        """
        print(f"[叙述]: {text}")
```

**示例：**

```koilang
#character Alice "Hello!"
This is a text line.      → 触发 on_text("This is a text line.")
Another line here.        → 触发 on_text("Another line here.")
```

**注意：** 每个文本行都会触发单独的 `on_text` 调用。如果你有多行连续的文本，每行都会单独调用 `on_text`，除非解析器配置为保留空行或缩进。

### 注释行

注释行（以 `##` 或更多 `#` 开头的行）在 KoiLang 中也是**特殊命令**，命令名为 `@annotation`。

**处理方式：**

在你的环境类中，你可以使用 `on_annotation` 方法捕获注释行（尽管注释通常被忽略）：

```python
class MyGame:
    def on_annotation(self, text):
        """处理注释行内容。
        
        对应 KoiLang 中的注释行（以 ## 开头的行）
        命令名：@annotation
        
        Args:
            text: 注释内容（不含 ## 前缀）
        """
        print(f"[注释]: {text}")
```

**注释行为：**

```koilang
## This is a single-line annotation    → 命令名：@annotation
### This is also an annotation         → 命令名：@annotation
#### Multi-level annotations work too  → 命令名：@annotation

#command arg  ## 不支持行内注释
```

**默认行为：**

默认情况下，注释行会被解析器忽略（不触发处理器）。你可以通过 `ParserConfig` 控制此行为：

```python
from koilang.model import ParserConfig
from koilang.runtime import Runtime

# 跳过所有注释（对于注释较多的文件可提高性能）
config = ParserConfig(skip_annotations=True)
runtime = Runtime(config=config)
```

**注意：** 与某些语言不同，KoiLang 不支持行内注释。注释必须单独成行，并在开头（任何缩进之后）以 `#` 开头。

### 命令阈值

`command_threshold` 参数决定 KoiLang 如何根据 `#` 字符数量识别行类型：

| 阈值 | `#text` | `##text` | `###text` | `####text` | 无前缀 |
|-----------|---------|----------|-----------|------------|-----------|
| 0 | 注释 | 注释 | 注释 | 注释 | 命令 |
| 1 (默认) | 命令 | 注释 | 注释 | 注释 | 文本 |
| 2 | 文本 | 命令 | 注释 | 注释 | 文本 |
| 3 | 文本 | 文本 | 命令 | 注释 | 文本 |

- **`<` 阈值的 `#` 字符数** → 文本行（触发 `@text` 命令）
- **`=` 阈值的 `#` 字符数** → 命令（触发 `do_<name>` 处理器）
- **`>` 阈值的 `#` 字符数** → 注释行（触发 `@annotation` 命令）

**使用场景：**

- `threshold=1`：标准 KoiLang 语法（默认）
- `threshold=2`：允许在 `#` 有特殊含义的语言中嵌入 KoiLang（单个 `#` 前缀被视为文本）
- `threshold=3`：用于复杂嵌套结构的严格命令解析

**示例：**

```python
from koilang.model import ParserConfig
from koilang.runtime import Runtime

# 在 Markdown 中使用 threshold=2
config = ParserConfig(command_threshold=2)
runtime = Runtime(config=config)

# 在此模式下：
# # This is text (1 个 # = 文本行 → @text)
# ##command arg  (2 个 # = 命令 → do_command)
# ###comment    (3 个 # = 注释行 → @annotation)
```

## 高级用法

### 使用核心层进行基本解析

核心层提供对 Rust 解析器的直接绑定。它适用于类文件对象或文件名。

```python
import io
from koilang.core import Parser

# 使用 io.StringIO 从字符串解析
content = io.StringIO("#character Alice \"Hello, world!\"\nThis is regular text.")
parser = Parser(content)

for command in parser:
    print(f"Command: {command.name}, Args: {command.args}, Kwargs: {command.kwargs}")
```

### 复杂环境和中间件

```python
from koilang.runtime import Runtime, Middleware
import time

# 记录命令执行时间的中间件
def logger_middleware(runtime, cmd, next_handler):
    start = time.time()
    result = next_handler(cmd)
    print(f"Executed #{cmd.name} in {time.time() - start:.4f}s")
    return result

class Scene:
    def on_start(self): print("Scene started")
    def do_bg(self, name): print(f"Background: {name}")

class Character:
    def do_say(self, text): print(f"Alice: {text}")

runtime = Runtime(middleware=[logger_middleware])
runtime.env_enter(Scene())
runtime.env_enter(Character())  # 栈：[Scene, Character]

# Character 环境处理 'say'，Scene 处理 'bg'
runtime.execute(io.StringIO("#bg Forest\n#say \"Wait!\""))
```

### 动态环境注册

你还可以在命令执行期间动态注册环境，实现更灵活的控制流：

```python
from koilang.runtime import Runtime, env_enter, env_exit
import io

class DialogManager:
    """动态管理对话上下文。"""
    
    def do_enter_dialog(self, character_name):
        """进入特定角色的对话上下文。"""
        # 动态将新环境推入栈
        env_enter(CharacterDialog(character_name))
    
    def do_exit_dialog(self):
        """退出当前对话上下文。"""
        # 注意：实际使用时你需要跟踪环境实例
        # 这是一个简化示例
        pass

class CharacterDialog:
    """特定角色对话的环境。"""
    
    def __init__(self, name):
        self.name = name
    
    def do_say(self, text):
        print(f"{self.name}: {text}")
    
    def do_emote(self, emotion):
        print(f"[{self.name} {emotion}]")
    
    def do_end(self):
        """退出此对话环境。"""
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

`env_enter()` 和 `env_exit()` 函数允许你从命令处理器内部管理环境栈，实现动态作用域和上下文管理。

### 跳转和标签

启用缓存后，你可以在脚本中跳转。

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

### 执行器（程序化命令执行）

`Executor` 为在运行时中执行命令提供程序化接口：

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

# 获取执行器以程序化触发命令
executor = runtime.get_executor()

# 执行命令，如同来自 KoiLang 文件
executor.do_move("north")      # 等同于：runtime.execute("#move north")
executor.do_attack("dragon")   # 等同于：runtime.execute("#attack dragon")
```

**目标执行：**

你还可以在栈中的特定环境上执行命令：

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

# 在最近的 Player 环境上执行
executor[Player].do_status()   # "Player status: OK"

# 在最近的 Enemy 环境上执行  
executor[Enemy].do_status()    # "Enemy status: Dead"

# 通过索引在特定实例上执行
executor[Player, 0].do_status()  # 第一个 Player 实例
executor[Player, -1].do_status() # 最后一个 Player 实例
```

### 写入器格式化选项

`Writer` 类支持细粒度的格式控制：

```python
from koilang.runtime import Writer
from koilang.model import FormatterOptions, WriterConfig
import io

# 基本用法
output = io.StringIO()
with Writer(output) as w:
    w.do_heading("Title")
    w.on_text("Content here")

# 使用自定义格式化选项
config = WriterConfig(
    global_options=FormatterOptions(indent=2, compact=True),
    command_threshold=1
)

with Writer(output, config=config) as w:
    w.do_cmd(1, 2, 3)  # 使用紧凑格式
```

**可用的 FormatterOptions：**

| 选项 | 类型 | 描述 |
|--------|------|-------------|
| `indent` | int | 缩进空格数 |
| `use_tabs` | bool | 使用制表符代替空格 |
| `compact` | bool | 移除不必要的空白 |
| `newline_before` | bool | 在命令前添加换行 |
| `newline_after` | bool | 在命令后添加换行 |
| `force_quotes_for_vars` | bool | 强制为字面量添加引号 |
| `number_format` | str | 整数的自定义格式 |
| `float_format` | str | 浮点数的自定义格式 |
| `newline_before_param` | bool | 在每个参数前换行 |
| `newline_after_param` | bool | 在每个参数后换行 |

**使用上下文管理器的临时选项：**

```python
output = io.StringIO()
with Writer(output) as w:
    w.do_cmd1(1, 2)
    
    # 对一块命令应用紧凑格式
    with w.with_options(compact=True):
        w.do_cmd2(3, 4)
        w.do_cmd3(5, 6)
    
    # 恢复默认格式
    w.do_cmd4(7, 8)
```

**单命令的流畅 API：**

```python
output = io.StringIO()
with Writer(output) as w:
    # 对单个命令应用选项
    w.with_options(compact=True).do_tight_cmd(1, 2)
    
    # 针对特定命令
    with w.with_options(compact=True, target_commands=["cmd1", "cmd2"]):
        w.do_cmd1(1, 2)  # 使用紧凑格式
        w.do_cmd2(3, 4)  # 使用紧凑格式
        w.do_cmd3(5, 6)  # 使用默认格式
```

**缩进管理：**

```python
output = io.StringIO()
with Writer(output) as w:
    w.do_parent()
    
    # 增加缩进
    w.inc_indent()
    w.do_child1()
    w.do_child2()
    
    # 减少缩进
    w.dec_indent()
    w.do_sibling()
    
    # 或使用上下文管理器
    with w.indent():
        w.do_nested()
        w.do_content()
```

## 迁移指南（从旧版 `kola`）

`koilang-py` 是旧版 `kola` 模块的继任者。本指南帮助你从旧的 `kola` API 迁移到新的 `koilang` API。

### 主要差异

| 特性 | 旧版 `kola` | 新版 `koilang` |
| --- | --- | --- |
| **主类** | `KoiLang` | `Runtime` |
| **装饰器** | `@kola_command`, `@kola_text` | 基于约定 (`do_name`, `on_name`) |
| **解析** | `parse()`, `parse_file()` | `execute()`（支持 IO 和文件） |
| **扩展** | 基于继承 | 组合（运行时 + 环境栈） |
| **文本处理器** | `@kola_text` 装饰器 | `on_text()` 方法 |
| **数字命令** | `@kola_number` 装饰器 | `do_114()`, `do_1919()` 方法 |
| **环境** | 嵌套 `Environment` 类 | 任何带有 `do_`/`on_` 方法的 Python 对象 |
| **CLI** | `python -m kola file.kola` | `python -m koilang file.koi` |

### 基本迁移示例

**旧版 `kola` 代码：**

```python
from kola import KoiLang, kola_command, kola_text

class MyScript(KoiLang):
    @kola_command
    def greet(self, name):
        print(f"Hello, {name}!")
    
    @kola_text
    def handle_text(self, text):
        print(f"Text: {text}")

# 用法
script = MyScript()
script.parse_file("script.kola")
```

**新版 `koilang` 代码：**

```python
from koilang.runtime import Runtime

class MyEnv:
    def do_greet(self, name):
        print(f"Hello, {name}!")
    
    def on_text(self, text):
        print(f"Text: {text}")

# 用法
runtime = Runtime()
runtime.env_enter(MyEnv())
runtime.execute("script.koi")
```

### 装饰器迁移

**旧版装饰器：**

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

**新版基于约定的方法：**

```python
class NewStyle:
    # 方法名成为命令名
    def do_custom_name(self): ...
    
    # 文本处理器使用 on_text
    def on_text(self, text): ...
    
    # 数字命令使用 do_<number>
    def do_114(self): ...  # 处理 #114
    def do_1919(self): ... # 处理 #1919
```

### 环境迁移

**旧版嵌套环境：**

```python
from kola import KoiLang, Environment, kola_env_enter, kola_env_exit

class Main(KoiLang):
    class SubEnv(Environment):
        @kola_env_enter("enter")
        def enter(self): ...
        
        @kola_env_exit("exit")
        def exit(self): ...
```

**新版环境栈方法：**

```python
from koilang.runtime import Runtime, env_enter, env_exit

class Main:
    def do_enter(self):
        env_enter(SubEnv())
    
    def do_exit(self):
        # 获取当前环境并退出
        pass

class SubEnv:
    pass

runtime = Runtime()
runtime.env_enter(Main())
```

### 命令名自定义

**旧版：**

```python
@kola_command("open")
def file(self, path): ...
```

**新版：**

只需用所需的命令名命名你的方法：

```python
def do_open(self, path): ...  # 处理 #open
```

或使用标准名称（如果匹配）：

```python
def do_file(self, path): ...  # 处理 #file
```

### 解析器配置迁移

**旧版：**

```python
from kola import KoiLang

class MyParser(KoiLang):
    def __init__(self):
        super().__init__()
        self.command_threshold = 2
```

**新版：**

```python
from koilang.runtime import Runtime
from koilang.model import ParserConfig

config = ParserConfig(command_threshold=2)
runtime = Runtime(config=config)
```

### 写入器迁移

**旧版：**

```python
from kola.writer import FileWriter, StringWriter

# 文件输出
with FileWriter("output.kola") as w:
    w.write_command("cmd", arg1, arg2)
    w.write_text("Some text")

# 字符串输出
sw = StringWriter()
sw.write_command("cmd", arg1)
result = sw.getvalue()
```

**新版：**

```python
from koilang.runtime import Writer
import io

# 文件输出
with Writer("output.koi") as w:
    w.do_cmd(arg1, arg2)
    w.on_text("Some text")

# 字符串输出
output = io.StringIO()
with Writer(output) as w:
    w.do_cmd(arg1)
result = output.getvalue()
```

### 完整示例：文件生成器

以下是基于旧版文档中文件生成器的完整迁移示例：

**旧版 `kola`：**

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

# 用法
FastFile().parse_file("makefiles.kola")
```

**新版 `koilang`：**

```python
import os
from koilang.runtime import Runtime

class FastFile:
    def __init__(self):
        self._file = None
    
    def on_start(self):
        self._file = None
    
    def on_end(self):
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
    
    def on_text(self, text: str) -> None:
        if not self._file:
            raise OSError("write texts before the file open")
        self._file.write(text)

# 用法
runtime = Runtime()
runtime.env_enter(FastFile())
runtime.execute("makefiles.koi")
```

### 变更总结

1. **不再继承**：你不再从 `KoiLang` 继承，而是创建普通的 Python 类
2. **约定优于配置**：使用 `do_` 前缀表示命令，`on_` 前缀表示特殊处理器
3. **以运行时为中心**：所有执行都通过 `Runtime` 实例进行
4. **环境栈**：使用 `env_enter()`/`env_exit()` 代替嵌套环境类
5. **统一解析**：`execute()` 方法处理字符串和类文件对象
6. **更简单的写入器**：使用基于方法的命令生成，API 更直观
