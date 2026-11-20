# Patterns from the ggtext port

What we chose, what we backed out of, and why. Read this before designing the port's API and before
any change that touches plotnine or matplotlib internals.

## Favoured

**API**
- **plotnine is the only entry point.** The public API is geoms, stats, theme elements and the like.
  ggtext first also shipped matplotlib helpers (`ggtext.text(ax, ...)`, `set_title(ax, ...)`) and
  functions that converted existing artists in place (`richify`, `make_rich`). They were all removed:
  they doubled the API surface, the tests and the docs, and invited monkey patching.
- **Python names, R aliases.** snake_case parameters (`label_color`, `box_size`), with R spellings
  (`label.colour`, `colour`, `hjust`, `angle`) accepted and translated in `__init__`/`setup_data`.
- **Points as units**, with R's mm and grid units converted at the boundary. Defaults follow R; where
  Python convention wins (ggtext treats `\n` as a line break, R as a space), the R behaviour stays one
  argument away (`newline="space"`).
- **Every deliberate difference is written down**: in `docs/differences.md`, and as an `Adapted:` line
  in the parity case or test it affects.

**Implementation**
- **Subclass, don't wrap.** `RichText(Text)` overrides two methods. The ggtext geoms subclass
  plotnine's `geom_text` and reuse its aesthetics, parameters and `adjust_text` support.
- **Changes are scoped to objects you created.** Swapping an artist's class to a rich subclass was
  fine because ggtext made the subclass. Per-instance wrappers (one figure's layout engine) are small
  picklable classes, never closures.
- **Read plotnine's source, not its docs or your memory.** Several design decisions came from reading
  `themeable.py` and `ggplot.draw` (see `plotnine-map.md`, "Theme elements").

**Testing and tooling**
- **One deterministic image environment.** Baselines are made with Linux, matplotlib 3.11 and DejaVu
  fonts at 640×480/72 dpi, tolerance 2 (`tests/image_compare.py`). Elsewhere the plot is still drawn
  but the pixel comparison is skipped, so platforms with different FreeType versions don't fail.
- **Parity with R is a separate check from Python regression tests.** plotparity compares with R;
  pytest image baselines catch the port changing against itself.
- **Examples are documentation and tests.** Each `examples/NN_*.py` writes its images to
  `${ENV}_EXAMPLES_OUT` when set (tests) or `docs/images/` (gallery), and `tests/test_examples.py` runs
  them with warnings as errors.
- **Expected warnings are asserted** with `pytest.warns(..., match=...)`, not filtered globally.
- **pytest-randomly, strict pyrefly with a baseline, ruff defaults, prek hooks.** Every commit passes
  all of them.
- **Small commits, each green.** Unrelated changes (a regenerated gallery, a tooling fix) go in their
  own commits.

## Avoided

- **Monkey patching matplotlib or plotnine classes.** ggtext started by adding `set_richtext` to every
  matplotlib `Text`, so plotnine's `text.set(**element.properties)` would accept a `richtext`
  property. It changed a core class for every user and leaked a `richtext=` keyword into plain
  matplotlib. It was replaced by a wrapper on plotnine's `theme.apply`, which is smaller but still a
  patch. If a patch is truly unavoidable:
  - patch the narrowest place, on the plotnine side rather than matplotlib's;
  - install it once, idempotently, on import, and make it a no-op for plots that don't use the port;
  - don't make it toggleable if the feature can't work without it;
  - test that the patched class behaves as before for other code, and that the patch is installed;
  - document it in the design notes, with the plotnine hook that would remove it.
- **Hooks that rely on element objects surviving theme merging.** An overridden
  `element_markdown.setup()` never runs once `theme_bw()` has merged the element away. Only the
  properties dict survives.
- **Copies of plotnine internals without a test that catches drift.** ggtext keeps a list of which
  artists each text themeable styles. Each entry has a test, and plotnine is pinned to `<0.16`.
- **Asking the user to add a ggtext-specific theme object** (`+ ggtext_theme()`) to avoid patching.
  It works with no patching at all, but every plot then needs it after any complete theme, and
  forgetting it fails with an opaque matplotlib error. Weigh this trade-off case by case.
- **Closures stored on figures or artists.** They break pickling.
