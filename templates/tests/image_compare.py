"""
Image comparison harness for the plotnine geoms.

Adapted from plotnine's own test suite. A test compares a plot with a
baseline image using ``assert p == "name"``. The harness writes result images to
``tests/result_images/<test_module>/`` and compared with
``tests/baseline_images/<test_module>/<name>.png`` (tolerance 2, as in
plotnine).

Create or update baselines with ``pytest --update-baselines``.

Baselines depend on how text is rasterized, which differs between
platforms and between the FreeType versions bundled with matplotlib 3.10
and 3.11. The baselines are made in one reference environment, Linux with
matplotlib 3.11. Anywhere else the plot is
still drawn, so the code paths run, but the pixel comparison is skipped.
Set ``{{ENV}}_IMAGE_TESTS=force`` to compare (or update) anyway.

Everything here is local to image tests: ``ggplot.__eq__`` is only
patched while a test marked ``image`` runs (see ``conftest.py``), and the
size, dpi, fonts and rcParams are applied per comparison and restored.
"""

from __future__ import annotations

import inspect
import io
import os
import shutil
import sys
import types
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.testing.compare import compare_images

TOLERANCE = 2  # Same default tolerance as plotnine
DPI = 72
# 640 x 480 pixels, the size of vdiffr snapshots and of plotparity's R
# references (parity/cases.toml [render])
FIGURE_SIZE = (640 / DPI, 480 / DPI)

# Fonts that ship with matplotlib, for identical images everywhere
FONT_RCPARAMS = {
    "font.monospace": ["DejaVu Sans Mono"],
    "font.sans-serif": ["DejaVu Sans"],
    "font.serif": ["DejaVu Serif"],
}

# Where the baselines were made: Linux, matplotlib 3.11
REFERENCE_PLATFORM = "linux"
REFERENCE_MATPLOTLIB = (3, 11)


def reference_environment() -> tuple[bool, str]:
    """Whether this is the environment the baselines were made in."""
    if os.environ.get("{{ENV}}_IMAGE_TESTS", "").lower() == "force":
        return True, ""
    mpl_version = tuple(mpl.__version_info__[:2])
    if (
        not sys.platform.startswith(REFERENCE_PLATFORM)
        or mpl_version != REFERENCE_MATPLOTLIB
    ):
        here = f"{sys.platform}, matplotlib {mpl.__version__}"
        ref = "{}, matplotlib {}.{}".format(REFERENCE_PLATFORM, *REFERENCE_MATPLOTLIB)
        return False, f"image baselines are for {ref}; this is {here}"
    return True, ""


tests_dir = Path(__file__).parent
baseline_images_dir = tests_dir / "baseline_images"
result_images_dir = tests_dir / "result_images"

_state = {"update": False}


def set_update(flag: bool) -> None:
    _state["update"] = flag


def make_test_image_filenames(name: str, test_file: str):
    name_ = Path(name).with_suffix(".png")
    subdir = Path(test_file).stem
    filenames = types.SimpleNamespace(
        baseline=baseline_images_dir / subdir / name_,
        result=result_images_dir / subdir / name_,
        expected=result_images_dir / subdir / f"{name_.stem}-expected.png",
    )
    filenames.result.parent.mkdir(parents=True, exist_ok=True)
    return filenames


class _test_cleanup:
    """Deterministic rcParams and fonts, restored on exit."""

    def __enter__(self):
        from plotnine.themes.theme import DEFAULT_RCPARAMS

        plt.close("all")
        self._rc = mpl.rcParams.copy()
        self._default_rc = dict(DEFAULT_RCPARAMS)
        mpl.rcdefaults()
        mpl.rcParams["text.hinting"] = "auto"
        mpl.rcParams["text.antialiased"] = True
        DEFAULT_RCPARAMS.update(FONT_RCPARAMS)
        mpl.rcParams.update(FONT_RCPARAMS)
        return self

    def __exit__(self, *args: object) -> None:
        from plotnine.themes.theme import DEFAULT_RCPARAMS

        plt.close("all")
        DEFAULT_RCPARAMS.clear()
        DEFAULT_RCPARAMS.update(self._default_rc)
        mpl.rcParams.update(self._rc)


def _sized(plot: Any) -> Any:
    from plotnine import theme

    return plot + theme(figure_size=FIGURE_SIZE, dpi=DPI)


def ggplot_equals(plot: Any, name: str) -> bool:
    import pytest

    test_file = inspect.stack()[1][1]
    filenames = make_test_image_filenames(name, test_file)
    with _test_cleanup():
        _sized(plot).save(filenames.result, verbose=False, dpi=DPI)

    is_reference, reason = reference_environment()
    if not is_reference:
        if _state["update"]:
            raise pytest.UsageError(
                f"Refusing to update baselines: {reason}. "
                "Set {{ENV}}_IMAGE_TESTS=force to override."
            )
        pytest.skip(f"{reason} (the plot was drawn; the pixel comparison is skipped)")

    if _state["update"]:
        filenames.baseline.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filenames.result, filenames.baseline)

    if not filenames.baseline.exists():
        raise FileNotFoundError(f"Baseline image {filenames.baseline} is missing")

    shutil.copyfile(filenames.baseline, filenames.expected)
    err = compare_images(
        str(filenames.expected),
        str(filenames.result),
        TOLERANCE,
        in_decorator=True,
    )
    plot._err = err  # pyright: ignore[reportAttributeAccessIssue]
    return not err


def draw_test(self: Any) -> None:
    with _test_cleanup():
        fig = _sized(self).draw()
        fig.savefig(io.BytesIO(), dpi=DPI)  # text is laid out lazily


def assertrepr_compare(op: str, left: Any, right: Any) -> list[str] | None:
    from plotnine import ggplot

    if isinstance(left, ggplot) and isinstance(right, str) and op == "==":
        err = getattr(left, "_err", None)
        if err:
            return [
                "images not close: {actual:s} vs. {expected:s} (RMS {rms:.2f})".format(
                    **err
                )
            ]
