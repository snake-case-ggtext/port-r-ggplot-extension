---
name: port-r-ggplot-extension
description: Port an R ggplot2 extension package to Python as a plotnine extension that matches R's output, checked with plotparity. Use when asked to port, translate or re-implement a ggplot2 extension (geoms, stats, theme elements, guides) for plotnine/Python, given a git URI (remote or local path) of the R package.
---

# Port an R ggplot2 extension to plotnine

The goal is a Python package whose plots match the R package's, judged by
[plotparity](https://github.com/snake-case-ggtext/plotparity). R's behaviour is the spec. This
skill distils the ggtext port (R `ggtext` → Python `ggtext`); its notes are in `reference/`:

| File | Read it when |
|---|---|
| `reference/plotnine-map.md` | mapping ggproto objects to plotnine classes, and where to read plotnine |
| `reference/matplotlib-artists.md` | the port needs its own matplotlib artist |
| `reference/patterns.md` | before designing the API, and before any change touching plotnine/matplotlib internals |
| `reference/porting-tests.md` | turning testthat tests and roxygen examples into pytest tests and parity cases |

plotparity's own docs are the source of truth for its formats. Read them in the plotparity clone
(step 1): `skills/plotparity/SKILL.md`, `docs/writing-cases.md`, `docs/writing-adapters.md`, `README.md`.
They run plotparity through `uvx`. In this workflow pixi is the only package manager: plotparity is
installed into the port's pixi environment, so every `plotparity …`/`$PP …` command in those docs
becomes `pixi run parity …`.

## Inputs

Ask for anything missing before starting:

- **R package source**: a git URI. A remote URL is cloned; a local path that is a git repo is read in place.
- **Python package name**: defaults to the R package name.
- **Destination**: the directory the port repo is created in.
- Optional: a ref (tag/commit) of the R package; defaults to its default branch.

## 1. Fetch sources once

Every source lives in one cache shared by all ports, so nothing is cloned twice:

```bash
SOURCES=${PORT_SOURCES:-$HOME/coding/snake_case/sources}
mkdir -p "$SOURCES"
```

For each source (`name`, `uri`, optional `ref`), with plain git:

```bash
if git -C "$uri" rev-parse --show-toplevel >/dev/null 2>&1; then
  path=$(git -C "$uri" rev-parse --show-toplevel)       # local repo: use in place, read-only
elif [ -d "$SOURCES/$name/.git" ]; then
  path="$SOURCES/$name"; git -C "$path" fetch --tags --quiet origin
else
  path="$SOURCES/$name"; git clone --quiet "$uri" "$path"
fi
[ -n "$ref" ] && [ "$path" = "$SOURCES/$name" ] && git -C "$path" switch --detach --quiet "$ref"
touch "$SOURCES/SOURCES.md"                               # one row per source: name, URI, commit, path
{ grep -v "^| $name |" "$SOURCES/SOURCES.md"
  echo "| $name | $uri | $(git -C "$path" rev-parse HEAD) | $path |"; } > "$SOURCES/SOURCES.md.new"
mv "$SOURCES/SOURCES.md.new" "$SOURCES/SOURCES.md"
```

Never switch branches in a local repo the user passed in. If its checkout isn't the ref you need,
ask. Fetch:

| name | uri | ref |
|---|---|---|
| the R package | the input URI | the input ref |
| `plotnine` | `https://github.com/has2k1/plotnine` | `v0.15.9` (the version the env pins) |
| `plotparity` | `https://github.com/snake-case-ggtext/plotparity` | default branch |
| `ggplot2` (only when needed) | `https://github.com/tidyverse/ggplot2` | the version the R package needs |

Read plotnine from this clone, not from memory or site-packages: it is the exact code the port
runs on.

## 2. Inventory and license gate

Read the R package's `DESCRIPTION`, `LICENSE`, `NAMESPACE`, `R/` (every `ggproto()` call and
`element_*`/`theme` function), roxygen `@examples` (`man/*.Rd` or `R/*.R`), `tests/testthat/`
(including `_snaps/`) and vignettes.

**Stop and ask about the license** before reading `R/` in detail. Many ggplot2 extensions are GPL.
Either the port takes the R package's license and may translate its code, or the port keeps its
own license and is written only from documentation, examples, tests and rendered output
(clean room). Record the decision in `PORT_PLAN.md`.

## 3. Scaffold the port repo

A regular git repo with one pixi environment, defined in `pyproject.toml`: Python 3.13, plotnine
0.15.9, matplotlib 3.11.2, R with ggplot2 and ragg, the dev tools, and plotparity (an editable
install of the local clone, so adapter edits take effect immediately). There is no uv or venv:

```bash
SKILL_DIR=<this skill's directory>
PKG=<python package> RPKG=<R package> RURL=<R package URL> LICENSE=<SPDX id from step 2>
R_SOURCE=<path of the R package from step 1> PLOTPARITY=<path of plotparity from step 1>
PORT=<destination>/$PKG

mkdir -p "$PORT" && cp -r "$SKILL_DIR/templates/." "$PORT" && cd "$PORT"
mv "src/{{package}}" "src/$PKG"
grep -rlF '{{' --exclude=PORT_PLAN.md . | xargs sed -i \
  -e "s|{{package}}|$PKG|g" -e "s|{{r_package_lower}}|$(echo "$RPKG" | tr '[:upper:]' '[:lower:]')|g" \
  -e "s|{{r_package}}|$RPKG|g" -e "s|{{r_url}}|$RURL|g" -e "s|{{license}}|$LICENSE|g" \
  -e "s|{{r_source_path}}|$R_SOURCE|g" -e "s|{{plotparity_path}}|$PLOTPARITY|g" \
  -e "s|{{ENV}}|$(echo "$PKG" | tr '[:lower:]-' '[:upper:]_')|g"
grep -rn '{{' --exclude=PORT_PLAN.md .   # must print nothing
```

(On macOS use `sed -i ''`.) Then:

```bash
git init -b main
pixi install
pixi run Rscript -e 'library(ggplot2)'     # R works inside pixi
```

Install the R package into the pixi env. If conda-forge has it, uncomment
`r-<pkg>` in `pyproject.toml` and run `pixi install` again. Otherwise run
`pixi run install-r-upstream`, which runs `remotes::install_local` on the clone. Then:

```bash
pixi run parity init --adapter "$RPKG" --package "$PKG"   # parity.toml, parity/cases.toml, .gitignore
# run the port in the pixi env, not a plotparity-managed uv env:
sed -i "/^package = /a python = \".pixi/envs/default/bin/python\"" parity.toml
# load the R package before each case's R block:
sed -i "s/^packages = \[\"ggplot2\"\]/packages = [\"ggplot2\", \"$RPKG\"]/" parity/cases.toml
pixi run prek install
pixi run test && pixi run lint
git add -A && git commit -m "Scaffold the $PKG port of R $RPKG"
```

Then fill in `PORT_PLAN.md` from step 2: the upstream table and one row per export.

## 4. One pass over the R tests and examples

Go through `tests/testthat/` and the `@examples` once, following `reference/porting-tests.md`:

- every `expect_doppelganger()` and every `@examples` plot becomes a plotparity case
  (`pixi run parity new-case parity/<group>/<id>.md --package $PKG`, then replace its placeholder
  ggtext plot). The R block is copied verbatim; the Python block is the API you intend the port to have.
- every other expectation becomes a pytest test.

List the port's public names in `parity.toml` as `api = ["geom_foo", "stat_foo", ...]` (the plotnine
targets in `PORT_PLAN.md`). Without it, a name the port doesn't export yet is reported as a
`case_error` (infrastructure, exit 2) instead of `missing_api` (a port failure, exit 1).

Then give each case to a split in `parity.toml` (`[splits] dev = [...]`, `holdout = [...]`). About
a quarter goes to holdout, and the holdout cases should cover features the dev cases also cover.
Render the R references once and commit them: `pixi run parity references parity`. From then on use
`pixi run parity run --no-render-r`, so a missing reference fails instead of re-rendering.

## 5. plotparity adapter

plotparity compares through one adapter per extension, under
`src/plotparity/adapters/<name>/` in plotparity itself. If the extension has none, write it in the
plotparity clone:

```bash
git -C "$PLOTPARITY" switch -c "adapter-$RPKG"
```

Follow `docs/writing-adapters.md` and use the closest existing adapter as a model: `ggridges` for
geoms that draw shapes, `ggtext` for text. Check the adapter with `pixi run parity validate` against
the references, and write mutations for `pixi run parity selftest`. **A human reviews `profile.toml` (checks,
tolerances, severities) before the port loop starts.** Commit on the adapter branch; the user opens
the PR to plotparity. The pixi env installs plotparity from this clone in editable mode, so
adapter edits take effect immediately.

## 6. Implement

Follow `reference/plotnine-map.md` and `reference/patterns.md`. In short:

- The public API is plotnine objects only: geoms, stats, positions, scales, theme elements. No
  functions that draw on or mutate matplotlib objects directly.
- Subclass the closest plotnine class, and the closest matplotlib artist if one is needed.
- Python names (snake_case) and units (points), with R spellings accepted as aliases. Every
  deliberate difference goes in `docs/differences.md` and in an `Adapted:` comment in the
  affected case or test.
- No monkey patching. If something really can't be done otherwise, see `reference/patterns.md` first.

## 7. Parity loop

Follow `skills/plotparity/SKILL.md` in the plotparity clone. The loop:

```bash
pixi run parity loop init    --name <loop> --goal "<what you're porting>" --from .
pixi run parity loop iterate --name <loop> --note "<what changed, which finding it addresses>"
pixi run parity loop holdout --name <loop>
pixi run parity loop finish  --name <loop> --summary "<outcome; anything plotparity missed>"
```

Only the port changes during a loop. The cases, references, `parity.toml`, `known_differences.toml`,
tolerances and the adapter are fixed. If a finding looks like the harness's fault, report it with
evidence; don't work around it.

## 8. Examples, docs and commits

- `examples/NN_name.py` scripts are documentation: a few plots showing the main features. They
  aren't a second copy of the parity cases. `pixi run gallery` runs them and writes
  `docs/images/` and `docs/gallery.md`; `tests/test_examples.py` runs them in the test suite.
- The README gives install and usage instructions. `docs/differences.md` lists the differences
  from R. Design notes name any plotnine or matplotlib internals the port relies on, and the test
  that would catch them changing.
- Small commits that each pass `pixi run test` and `pixi run lint`, and add no new findings to
  `pixi run parity run --no-render-r` (cases for features not ported yet fail until they are).
  Keep unrelated changes (a regenerated gallery, a tooling fix) in their own commits.

## Known issues

- **R references fail with "A system font called `DejaVu Sans` already exists".** plotparity
  registers its pinned DejaVu TTFs in R, and systemfonts refuses when fontconfig already has a
  DejaVu Sans (most Linux machines, and conda's font packages). The template's pixi activation sets
  `FONTCONFIG_FILE` to `tools/fontconfig/fonts.conf`, which lists no font directories, so R only
  sees the registered fonts. matplotlib doesn't use fontconfig. Keep it until plotparity handles
  the clash itself.
- **`pixi run install-r-upstream` installs only Depends/Imports/LinkingTo** from source. Packages
  the R tests need (testthat, vdiffr) come prebuilt from conda-forge. Add other Suggests the same way
  (`r-<name>` in `[tool.pixi.dependencies]`) rather than compiling them.
