# port-r-ggplot-extension

A Claude Code skill for porting an R ggplot2 extension package to Python as a
[plotnine](https://github.com/has2k1/plotnine) extension. R's output is treated as the spec, and
the port is checked against it with [plotparity](https://github.com/snake-case-ggtext/plotparity).

The workflow comes from the ggtext port (R `ggtext` to Python `ggtext`).

## What it does

Given the git URI of an R package (a remote URL or a local repo), the skill:

1. **Fetches sources.** The R package, plotnine (pinned to `v0.15.9`), plotparity and,
   when needed, ggplot2 are cloned into one shared cache (`$PORT_SOURCES`, by default
   `~/coding/snake_case/sources`). Each source's commit is recorded in `SOURCES.md`.
2. **Takes an inventory and checks the license.** It reads `DESCRIPTION`, `NAMESPACE`, the
   `ggproto()` objects, examples, tests and vignettes. Before it reads the R code in detail, it
   stops and asks whether the port takes the R package's license (and may translate its code) or
   is written clean-room.
3. **Scaffolds the port repo** from `templates/`. The repo has one pixi environment (Python 3.13,
   plotnine, matplotlib, R with ggplot2, dev tools, and an editable plotparity install), plus
   plotparity config, pre-commit hooks and a `PORT_PLAN.md`.
4. **Converts the R tests and examples.** Each visual test and each `@examples` plot becomes a
   plotparity case, split into dev and holdout sets. Every other expectation becomes a pytest
   test. R reference images are rendered once and committed.
5. **Writes a plotparity adapter** for the extension if plotparity doesn't have one yet. A human
   reviews the adapter's `profile.toml` before the parity loop starts.
6. **Implements the port** with plotnine objects only (geoms, stats, positions, scales, theme
   elements). Names are snake_case, R spellings are accepted as aliases, and there is no monkey
   patching. Each deliberate difference from R is listed in `docs/differences.md`.
7. **Runs the parity loop** (`parity loop init/iterate/holdout/finish`). During a loop only the
   port changes; the cases, references, tolerances and adapter stay fixed.
8. **Finishes with examples, docs and small commits.** Each commit passes tests and lint and adds
   no new parity findings.

## Repo layout

| Path | Contents |
|---|---|
| `SKILL.md` | The skill: inputs, the eight steps, and known issues |
| `reference/plotnine-map.md` | Mapping ggproto objects to plotnine classes |
| `reference/matplotlib-artists.md` | Writing custom matplotlib artists |
| `reference/patterns.md` | API design and working with plotnine/matplotlib internals |
| `reference/porting-tests.md` | Turning testthat tests and roxygen examples into pytest tests and parity cases |
| `templates/` | The port repo scaffold (`{{package}}`-style placeholders are filled in at step 3) |

## Usage

Install the skill where Claude Code can find it (for example `~/.claude/skills/`), then ask
Claude to port an extension, for example:

> Port https://github.com/wilkelab/ggridges to plotnine.

The skill asks for any missing inputs: the R package URI, the Python package name (defaults to
the R name), the destination directory and, optionally, a git ref.

## Requirements

- git
- [pixi](https://pixi.sh). It is the only package manager the workflow uses; it provides Python,
  R and plotparity inside the port's environment.
