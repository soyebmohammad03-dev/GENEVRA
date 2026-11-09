"""Render installed GENEVRA help as self-contained HTML for review."""

import argparse
import contextlib
import html
import io
import pydoc
from pathlib import Path

from genevra.cli import build_parser

MODULES = ("genevra.analysis.coverage_envelope", "genevra.experiments.config")


def render(output: Path) -> None:
    """Write the CLI and selected public API help to a new HTML file."""
    parser = build_parser()
    subcommands = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        parser.print_help()
        for command in subcommands.choices.values():
            print()
            command.print_help()
    sections = [("Command reference", buffer.getvalue())]
    for module in MODULES:
        sections.append((module, pydoc.render_doc(module, renderer=pydoc.plaintext)))
    body = "\n".join(
        f"<section><h2>{html.escape(title)}</h2><pre>{html.escape(text)}</pre></section>"
        for title, text in sections
    )
    with output.open("x", encoding="utf-8") as handle:
        handle.write(
            '<!doctype html>\n<html lang="en"><meta charset="utf-8">\n'
            "<title>GENEVRA software help</title><h1>GENEVRA software help</h1>\n"
            f"{body}\n</html>\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    render(parser.parse_args().output)
