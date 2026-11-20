# Differences from R {{r_package}}

{{package}} follows R {{r_package}} closely, but uses Python conventions where they clash.
R spellings still work as aliases. Every row here should also appear as an `Adapted:` comment in
the parity case or test that it affects.

| R {{r_package}} | {{package}} | Why |
|---|---|---|
| `label.colour`, `box.size` (dotted names) | `label_color`, `box_size` (dotted and `colour` spellings accepted as aliases) | snake_case |
| sizes in mm / `grid::unit()` | points (`mm * 72.27 / 25.4`) | matplotlib works in points |
| `NA` to remove a fill or outline | `"none"` (`None` keeps the default) | matplotlib colours |
