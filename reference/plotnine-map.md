# ggplot2 → plotnine map

Paths are relative to the plotnine clone at `v0.15.9` (`$SOURCES/plotnine/plotnine/`). Read the
file before subclassing; this page only says where to look and what caught us out.

## ggproto object → plotnine class

| ggplot2 (R) | plotnine | File | Override |
|---|---|---|---|
| `Geom` | `geom` | `geoms/geom.py` | `DEFAULT_AES`, `REQUIRED_AES`, `DEFAULT_PARAMS`, `setup_data`, `draw_panel` or `draw_group`, `draw_legend` |
| `Stat` | `stat` | `stats/stat.py` | `REQUIRED_AES`, `DEFAULT_PARAMS`, `DEFAULT_AES`, `CREATES`, `setup_params`, `compute_group`/`compute_panel` |
| `Position` | `position` | `positions/position.py` | `setup_params`, `compute_layer`/`compute_panel` |
| `Scale*` | `scale_*` | `scales/scale.py`, `scales/scale_identity.py` | prefer an existing scale; R's `scale_discrete_identity(aesthetics = ...)` maps to the `scale_*_identity` classes |
| `Coord` | `coord` | `coords/coord.py` | `transform`, `setup_panel_params` |
| `Facet` | `facet` | `facets/facet.py` | rarely needed |
| `Guide` | `guide` | `guides/guide.py`, `guides/guide_legend.py` | legends are matplotlib offsetboxes |
| `element_*` (theme) | `element_text`/`element_rect`/`element_line` | `themes/elements/` | see "Theme elements" |
| `theme()` slot | themeable class | `themes/themeable.py` | read `apply_figure`/`apply_ax` of the slot |
| the build pipeline | `ggplot.draw` | `ggplot.py` (`draw`, `_build`), `layer.py` | read, don't override |
| layout (`gtable`) | `PlotnineLayoutEngine` | `_mpl/layout_manager/_engine.py`, `_layout_items.py` | read, don't override |

Look for a close existing geom before writing one from scratch: `geoms/geom_text.py`,
`geom_polygon.py`, `geom_ribbon.py`, `geom_path.py` and `geom_rect.py` cover most drawing needs.

## Geoms

- `draw_group(data, panel_params, coord, ax, params)` is a static method and gets one group's rows.
  `draw_panel` gets a whole panel; override it only when groups interact, as in paint order or
  overlap.
- Call `data = coord.transform(data, panel_params)` before drawing. `panel_params.x.range` and
  `.y.range` give the panel limits, for converting data positions to panel fractions (npc).
- Add artists with `ax.add_artist(...)` (or `ax.add_collection(...)`) in data coordinates
  (`ax.transData`). Pass `params["zorder"]` and `params.get("raster", False)`, and clip to the
  panel with `artist.set_clip_path(ax.patch)`.
- `draw_legend(data, da, lyr)` draws the legend key into a `DrawingArea`. Without it the layer gets
  a blank key.
- Aliases for R argument names: translate them in the geom's `__init__` (for params) and in
  `setup_data` (for aesthetics mapped at the plot level). ggtext maps `hjust`→`ha`,
  `label.colour`→`label_color`, and so on.
- Missing values: drop the row (plotnine warns "Removed N rows containing missing values"), and
  treat R's `NA` for a colour as `"none"` (no fill or outline), not as "use the default".

## Theme elements

- Every text themeable styles its artists with `artist.set(**element.properties)`
  (`themes/themeable.py`, `apply_figure`/`apply_ax`). Any key you put in `properties` must be a
  property the artist has.
- **Theme merging discards element objects.** `theme_bw() + theme(plot_title=my_element())` merges
  `my_element`'s properties dict into the existing `plot_title` element, and `my_element` itself is
  gone (`themeable.merge`, `Themeables.update`). Anything that relies on the element object
  surviving (an overridden `setup`, `isinstance` checks, element methods) breaks in the common
  case. Only the properties dict survives.
- `theme.apply()` applies themeables from general to specific (`text` before `plot_title`). Artists
  that themeables style live in `theme.targets` (`themes/targets.py`), except tick labels, which
  come from each axes.
- A theme added after a complete theme survives; a complete theme (`theme_bw()`) replaces
  everything before it.

## Layout

- plotnine's layout engine measures every artist's `get_window_extent()` *before* it places the
  panels, then positions the panels. An artist whose size depends on the panel size, such as text
  wrapped to the panel width, is measured against the wrong panels on the first pass. ggtext runs
  the layout twice for such figures.
- Compositions (`p1 | p2`, `p1 / p2`) put several plots in one figure. `figure.get_layout_engine()`
  exposes `.plot` or `.composition.plotspecs`, so you can find which plot an artist belongs to.

## Units and conversions

| R | plotnine/matplotlib |
|---|---|
| sizes and line widths in mm (`size`, `linewidth`, `label.size`) | points: `mm * 72.27 / 25.4` (ggplot2's `.pt`, ≈ 2.85). **plotnine's own geoms don't do this:** they scale `size` by `SIZE_FACTOR = sqrt(pi)` ≈ 1.77 (`_utils/__init__.py`, used in `geom_path.py`, `geom_point.py`). A geom that inherits plotnine's sizing draws thinner lines than R. Decide per aesthetic which convention the port follows, and write it down in `docs/differences.md` |
| `grid::unit(x, "pt")` | points, same number |
| `grid::unit(x, "in")` | `x * 72.27` points (grid's points are 1/72.27 in) |
| `grid::unit(x, "npc")` | fraction of the panel (or of the figure, for figure-level artists) |
| text `size` (mm, in `geom_text`) | plotnine's `geom_text` takes `size` as a font size in points; R's is mm (× `.pt` for points). Check the geom you subclass |
| `hjust`/`vjust` in [0, 1] | `ha`/`va` names; ggtext accepts numbers too and resolves `"inward"`/`"outward"` per row |
| colour `NA` | `"none"` |

## Inspecting built data

ggplot2's `layer_data(p, i)` in plotnine:

```python
from copy import deepcopy
q = deepcopy(p); q._setup(); q._build()
q.layers[i].data      # 0-based; the data after stats, positions and scales
```

`_setup` and `_build` are private: use them in tests and in parity debugging only, never in the
package.
