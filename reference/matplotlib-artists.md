# Custom matplotlib artists

Most ports can draw with matplotlib's existing artists (`PathPatch`, `Polygon`, `PolyCollection`,
`LineCollection`, `Text`, `AnnotationBbox`). Write your own artist only when R draws something
those can't express, or when the shape's size must be measured by layout engines (as ggtext's rich
text is).

## Subclass the closest artist, override as little as possible

- Subclass the artist whose behaviour is closest, and override only what differs. ggtext's
  `RichText` subclasses `Text` and overrides only `_get_layout` (measuring) and `draw`, so every
  other `Text` method keeps working (`set_color`, `set_rotation`, `get_window_extent`, ...).
  Those properties become the defaults for the parts the markup doesn't change.
- Decorate `draw(self, renderer)` with `@matplotlib.artist.allow_rasterization`. Return early if
  `not self.get_visible()`, wrap drawing in `renderer.open_group(...)`/`close_group(...)`, and set
  `self.stale = False` at the end.
- Keep the artist's state in plain attributes and expose it as properties: a `set_<name>`/`get_<name>`
  pair makes `artist.set(name=...)`, `plt.setp` and `ArtistInspector` work.
- A subclass that keeps the parent's behaviour for plain input is easy to test: draw the same input
  with both classes and compare extents and pixels (ggtext's parity tests, `tests/test_artist.py`).

## Coordinates and clipping

- Data coordinates: `artist.set_transform(ax.transData)`. Sizes in points (line widths, padding,
  font sizes) are converted at draw time with `renderer.points_to_pixels(...)`. Never bake the dpi
  into the artist.
- For an offset in points from a data position, use `ax.transData + ScaledTranslation(dx/72, dy/72, fig.dpi_scale_trans)`,
  or work in display space inside `draw`.
- Clip to the panel with `artist.set_clip_path(ax.patch)` (plotnine geoms do this), or `clip_on=False`
  for artists that may stick out, such as labels outside the panel.
- `zorder` comes from the layer (`params["zorder"]`). Inside one artist, draw in R's paint order.

## Being measured

Layout engines (plotnine's, `constrained`, `tight`) and `savefig(bbox_inches="tight")` size things
through `artist.get_window_extent(renderer)` (and `get_tightbbox`). If an artist's drawn size differs
from its measured size, layouts overlap or leave gaps.

- Override `get_window_extent` (or the lower-level method it uses, as `Text._get_layout`) so the
  measurement and `draw` share one code path.
- `set_in_layout(False)` excludes an artist from layout on purpose.
- Measuring can happen before panels are placed (see `plotnine-map.md`, "Layout"). An artist whose size
  depends on the panel size needs a second layout pass.

## Pickling and copying

Figures get pickled and deep-copied (plotnine deep-copies plots; users pickle figures).

- Keep classes at module level. A class built at runtime needs a unique module-level name to be
  picklable (ggtext's `_rich_class_for`).
- Don't store closures or lambdas on artists or figures. When a method has to be wrapped per
  instance, use a small class with `__call__` (ggtext's `_ExecuteTwice`, `_RelayoutSetter`).
- Test it: `pickle.loads(pickle.dumps(fig))` and `fig.savefig(io.BytesIO())` with the artist present.

## Private matplotlib API

Avoid it. If there's no public alternative:

- Isolate it in one function, with version-specific branches (ggtext's `MPL_311` switch for
  `Text._get_layout`'s return format).
- Test on every matplotlib version the port supports (3.10 and 3.11 for ggtext), with tests that
  fail as soon as the private behaviour changes.
- List it in the design notes with the test that guards it.

## Backends

Draw only through renderer methods (`draw_path`, `draw_text`, `draw_image`, `draw_markers`) and
graphics contexts (`renderer.new_gc()`). Then Agg, PDF, SVG and Cairo all work. Test at least
`png`, `pdf` and `svg` saves.
