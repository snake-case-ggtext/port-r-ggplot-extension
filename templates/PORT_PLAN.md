# Port plan: {{r_package}} → {{package}}

## Upstream

| | |
|---|---|
| R package | {{r_package}} {{r_version}} |
| Source | {{r_url}} @ {{r_commit}} |
| License | {{r_license}} — decision: {{license_decision}} |
| Depends/Imports | {{r_imports}} |
| plotnine | 0.15.9 (sources cache @ v0.15.9) |
| plotparity adapter | `{{r_package}}` on branch `adapter-{{r_package}}` |

## Exports

One row per exported function or ggproto object. Status: `todo`, `case` (parity case written),
`impl` (implemented), `parity` (passes plotparity), `skip` (with the reason).

| R export | Kind (Geom/Stat/Position/Scale/element/helper) | plotnine target | Status | Notes |
|---|---|---|---|---|
| | | | todo | |

## R tests and examples

| R source | Becomes | Status |
|---|---|---|
| `tests/testthat/test-*.R` `expect_doppelganger(...)` | `parity/<group>/<id>.md` | todo |
| `tests/testthat/test-*.R` other expectations | `tests/test_*.py` | todo |
| roxygen `@examples` | `parity/<group>/<id>.md` | todo |

## Open questions
