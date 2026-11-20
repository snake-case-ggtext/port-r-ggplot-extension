"""
Run every gallery example (``examples/NN_*.py``).

Each example must run without errors or warnings and write its images.
The images go to a temporary folder (``{{ENV}}_EXAMPLES_OUT``), so running
the tests never touches ``docs/images/``. Regenerate the gallery with
``python examples/run_all.py``.
"""

from __future__ import annotations

import runpy
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

pytest.importorskip("plotnine")

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.glob("[0-9][0-9]_*.py"))

pytestmark = pytest.mark.examples


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.stem)
def test_example_runs(script: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from plotnine import theme_get, theme_set

    monkeypatch.setenv("{{ENV}}_EXAMPLES_OUT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    old_theme = theme_get()
    try:
        with mpl.rc_context(), warnings.catch_warnings():
            warnings.simplefilter("error")
            runpy.run_path(str(script), run_name="__main__")
    finally:
        theme_set(old_theme)
        plt.close("all")

    images = list(tmp_path.glob("*.png"))
    assert images, f"{script.name} wrote no images"
    for image in images:
        assert image.stat().st_size > 5_000, f"{image.name} looks empty"
