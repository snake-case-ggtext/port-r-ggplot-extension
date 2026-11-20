"""Shared fixtures and image-test hooks for the {{package}} test suite."""

from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

import {{package}}  # noqa: F401  (imports the package once for every test)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def fig():
    return plt.figure(figsize=(6, 4), dpi=100)


@pytest.fixture
def fig_ax():
    f, ax = plt.subplots(figsize=(6, 4), dpi=100)
    return f, ax


@pytest.fixture
def renderer(fig: Figure):
    return _agg_canvas(fig).get_renderer()


def _agg_canvas(fig: Figure) -> FigureCanvasAgg:
    """The figure's canvas; the suite runs on the Agg backend (see the top of this file)."""
    canvas = fig.canvas
    assert isinstance(canvas, FigureCanvasAgg)
    return canvas


def render_rgba(fig: Figure) -> np.ndarray:
    """Draw *fig* with Agg and return the RGBA pixels."""
    canvas = _agg_canvas(fig)
    canvas.draw()
    return np.asarray(canvas.buffer_rgba()).copy()


def pixels_in_bbox(img: np.ndarray, bbox: Bbox, pad: int = 2) -> np.ndarray:
    """The pixels of *img* inside a display-space *bbox* (y up)."""
    h = img.shape[0]
    x0 = max(int(bbox.x0) - pad, 0)
    x1 = min(int(np.ceil(bbox.x1)) + pad, img.shape[1])
    y0 = max(int(h - np.ceil(bbox.y1)) - pad, 0)
    y1 = min(int(h - bbox.y0) + pad, h)
    return img[y0:y1, x0:x1]


def has_color(region: np.ndarray, rgb: tuple[int, int, int], tol: int = 60) -> bool:
    """Whether any pixel in *region* is close to *rgb* (0-255 ints)."""
    diff = np.abs(region[..., :3].astype(int) - np.asarray(rgb)[None, None, :])
    return bool((diff.max(axis=-1) < tol).any())


# --- image comparison hooks (see tests/image_compare.py) ---------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Write result images as the new baselines (image tests)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "image: image-comparison tests (assert plot == 'name')"
    )
    from . import image_compare

    image_compare.set_update(config.getoption("--update-baselines"))


def pytest_assertrepr_compare(op: str, left: Any, right: Any) -> list[str] | None:
    from .image_compare import assertrepr_compare

    return assertrepr_compare(op, left, right)


@pytest.fixture(autouse=True)
def _image_env(request: pytest.FixtureRequest):
    """For ``image`` tests only: enable ``assert plot == "name"``."""
    if request.node.get_closest_marker("image") is None:
        yield
        return
    from plotnine import ggplot

    from . import image_compare

    mp = pytest.MonkeyPatch()
    mp.setattr(ggplot, "__eq__", image_compare.ggplot_equals, raising=False)
    mp.setattr(ggplot, "draw_test", image_compare.draw_test, raising=False)
    try:
        yield
    finally:
        mp.undo()
