# Porting R tests and examples

Go through the R package's `tests/testthat/` and roxygen `@examples` once. Each item becomes either
a **plotparity case** (anything that draws a plot to compare with R) or a **pytest test** (anything
that checks a value).

| R | Python |
|---|---|
| `expect_doppelganger("title", p)` (vdiffr) | plotparity case; optionally also a pytest image baseline |
| a plot in `@examples`, a vignette or the README | plotparity case |
| `test_that("desc", { ... })` | `def test_desc():` in `tests/test_<file>.py` |
| `expect_equal(x, y)`, `expect_identical` | `assert x == y`; `np.testing.assert_allclose` or `pd.testing.assert_frame_equal` for numbers and frames |
| `expect_error(f(), "msg")` | `with pytest.raises(PlotnineError, match="msg"):` (or the error type the port raises) |
| `expect_warning(f(), "msg")` | `with pytest.warns(PlotnineWarning, match="msg"):` |
| `expect_silent(f())` | run `f()` under `warnings.catch_warnings(); warnings.simplefilter("error")` |
| `layer_data(p, i)` | `q = deepcopy(p); q._setup(); q._build(); q.layers[i - 1].data` (tests only) |
| `ggplot_build(p)$data` | the same, for every layer |
| snapshot of a printed object | assert the specific values; don't port the snapshot text |

## plotparity cases

Create each with `pixi run parity new-case parity/<group>/<id>.md --package <pkg>`, then replace
the generated blocks: its placeholder plot uses ggtext's `geom_richtext`. See
`docs/writing-cases.md` in the plotparity clone for the full format. In short:

- The front matter holds `id` (the file stem), `expect` and `data`. `data` becomes `df` in both R
  and Python, so cases don't need `data.frame()`/`pd.DataFrame()` calls.
- The R block is copied from the R source unchanged, apart from moving inline data into `data`.
- The Python block is the API you want the port to have, written before the port exists. It is the
  spec for step 6, not a description of the current code.
- Set `source:` to where the case came from: `tests/testthat/test-geom-foo.R::"rotated labels"`, or
  `?geom_foo example 2`.
- Don't set fonts or themes: plotparity pins DejaVu Sans and the theme on both sides.
- Group cases by feature (`parity/geom_foo/`, `parity/stat_foo/`). That makes `[splits]` globs
  in `parity.toml` simple.

Render the R references once (`pixi run parity references parity`) and commit `parity/_references/`.

## pytest tests

Start each ported test with where it came from and what was adapted:

```python
def test_rotated_labels():
    # Port of tests/testthat/test-geom-foo.R::"rotated labels"
    # Adapted: label.size in mm -> points (MM); R's NA outline -> "none".
    ...
```

Unit constants used across tests:

```python
MM = 72.27 / 25.4   # R mm (sizes, line widths) to points
IN = 72.27          # grid inches to points
```

- Prefer asserting on built data (`layer_data` above) and on artist properties (colours, paths,
  extents) over pixels. They fail with a readable message and don't depend on fonts.
- Pixel tests use `tests/image_compare.py`: mark the module `pytestmark = pytest.mark.image` and
  write `assert p == "name"`. Create baselines with `pixi run pytest --update-baselines`, review
  them, and commit them. They run in the reference environment only (Linux, matplotlib 3.11) and
  are drawn but skipped elsewhere.
- Expected warnings are asserted with `pytest.warns`, never filtered globally.

## When R's behaviour is unclear

Run it, in the same pixi env:

```bash
pixi run Rscript -e 'library(ggplot2); library(<pkg>); p <- <plot>; print(layer_data(p))'
pixi run Rscript -e 'testthat::test_local(Sys.getenv("R_UPSTREAM"))'   # the upstream test suite
```

Under a clean-room license decision, run and observe R, but don't read the R package's source.
