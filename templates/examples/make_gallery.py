"""
Build docs/gallery.md from the example scripts.

Each numbered example contributes a section with its description, the
images it writes, and its full source code.

Run (after examples/run_all.py):  python examples/make_gallery.py
"""

import ast
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"

IMAGE_RE = re.compile(r'OUT / "([^"]+\.png)"')


def md_escape(text: str, table: bool = False) -> str:
    """Escape text for a Markdown heading (or a table cell)."""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("|", "\\|") if table else text


def anchor(script: Path) -> str:
    """Stable anchor from the file name: 03_titles_and_subtitles -> titles-and-subtitles."""
    return script.stem.split("_", 1)[1].replace("_", "-")


def section(script: Path) -> str:
    source = script.read_text()
    doc = ast.get_docstring(ast.parse(source)) or ""
    title, _, body = doc.partition("\n")
    body = "\n".join(
        line for line in body.strip().splitlines() if not line.startswith("Run:")
    ).strip()
    images = list(dict.fromkeys(IMAGE_RE.findall(source)))
    anchor_title = title.rstrip(".")

    out = [f'<a id="{anchor(script)}"></a>', "", f"## {md_escape(anchor_title)}", ""]
    if body:
        out += [body, ""]
    for img in images:
        out += [f"![{md_escape(anchor_title, table=True)}](images/{img})", ""]
    out += [
        f"<details><summary>Code: <code>examples/{script.name}</code></summary>",
        "",
        "```python",
        source.rstrip(),
        "```",
        "",
        "</details>",
        "",
    ]
    return "\n".join(out)


def main():
    scripts = sorted(HERE.glob("[0-9][0-9]_*.py"))
    parts = [
        "# Gallery",
        "",
        (
            "Every image in the documentation, with the code that made it. "
            "The scripts live in `examples/`; run `python examples/run_all.py` "
            "to regenerate the images and `python examples/make_gallery.py` "
            "to rebuild this page."
        ),
        "",
        "| Example | Script |",
        "|---|---|",
    ]
    for s in scripts:
        title = (ast.get_docstring(ast.parse(s.read_text())) or s.stem).split("\n")[0]
        name = title.rstrip(".")
        parts.append(
            f"| [{md_escape(name, table=True)}](#{anchor(s)}) | `examples/{s.name}` |"
        )
    parts.append("")
    parts += [section(s) for s in scripts]
    (DOCS / "gallery.md").write_text("\n".join(parts))
    print("wrote", DOCS / "gallery.md")


if __name__ == "__main__":
    main()
