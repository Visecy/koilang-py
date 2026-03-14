import io
from koilang.runtime import Writer, Runtime


def test_basic_writer():
    output = io.StringIO()
    with Writer(output) as w:
        w.do_heading("Title")
        w.at_text("Hello world")
        w.at_annotation("Note")
        w.do_cmd(1, 2, a=3)

    content = output.getvalue()
    assert "#heading Title" in content
    assert "Hello world" in content
    assert "## Note" in content  # Space after ##
    assert "#cmd 1 2 a(3)" in content


def test_writer_indent():
    output = io.StringIO()
    with Writer(output) as w:
        w.do_root()
        with w.indent():
            w.do_child()

    content = output.getvalue()
    assert "#root" in content
    assert "    #child" in content


def test_writer_options_fluent():
    output = io.StringIO()
    with Writer(output) as w:
        w.with_options(compact=True).do_cmd(1, 2, 3)

    content = output.getvalue()
    # In koicore, compact mode doesn't use commas.
    # It might affect other things like indentation or extraneous newlines.
    assert "#cmd 1 2 3" in content


def test_writer_options_context():
    output = io.StringIO()
    with Writer(output) as w:
        with w.with_options(compact=True):
            w.do_cmd1(1, 2)
            w.do_cmd2(3, 4)
        w.do_cmd3(5, 6)

    content = output.getvalue()
    assert "#cmd1 1 2" in content
    assert "#cmd2 3 4" in content
    assert "#cmd3 5 6" in content


def test_writer_target_commands():
    output = io.StringIO()
    with Writer(output) as w:
        with w.with_options(compact=True, target_commands=["cmd1"]):
            w.do_cmd1(1, 2)
            w.do_cmd2(3, 4)

    content = output.getvalue()
    assert "#cmd1 1 2" in content
    assert "#cmd2 3 4" in content


def test_runtime_get_writer():
    runtime = Runtime()
    output = io.StringIO()
    with runtime.get_writer(output) as w:
        w.do_test()

    assert "#test" in output.getvalue()


def test_runtime_get_writer_inherit_threshold():
    from koilang.model import ParserConfig

    runtime = Runtime(config=ParserConfig(command_threshold=2))
    output = io.StringIO()
    with runtime.get_writer(output) as w:
        w.do_test()

    # threshold 2 means commands start with ##
    assert "##test" in output.getvalue()


def test_writer_on_shortcuts():
    output = io.StringIO()
    with Writer(output) as w:
        w.at_text("Some text")
        w.at_annotation("Some note")

    content = output.getvalue()
    assert "Some text" in content
    assert "## Some note" in content  # Space after ##
