# Woodwork CAD

[![PyPI - Version](https://img.shields.io/pypi/v/woodwork-cad.svg)](https://pypi.org/project/woodwork-cad)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/woodwork-cad.svg)](https://pypi.org/project/woodwork-cad)

-----

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [License](#license)

## Overview

Procedural cad for my woodwork projects.

see [projects/output/board_test.md](projects/output/board_test.md) for basic operations.

The goal is to have a python script to perform woodwork operations (cut, rip, 
resaw) on inputs (boards) to create outputs (smaller boards) which can then be 
joined into pieces (boxes etc.)

Each script generates a markdown document with embedded svg diagrams and notes
  - starting boards
  - cut to size
  - plan, elevation
  - 3D render

The code should be object oriented (literally) and represent real world 
operations and use type checking to avoid errors where units are mixed up 
(adding pixels to lengths etc.)


## Installation & usage

```console
pip install woodwork-cad
```

Or use `hatch` to create virtual environment and install dependencies

```bash
hatch env create
```

Run `hatch run make` to rebuild all projects and generate markdown files in `projects/output/`.


## Unit testing

There are some "unit tests" in `geometry_test.md` for visualizing basic cases.

All generated output `.md` and `.svg` files are included in the repo so that
regressions can be detected.

Comparing svg file changes visually
```bash
git show main:projects/output/art_tote/fig-1.svg > projects/output/art_tote/fig-1~main.svg
xdg-open projects/output/art_tote/fig-1~main.svg & disown
xdg-open projects/output/art_tote/fig-1.svg & disown
```

## Performance profiling / optimization

```bash
pip install gprof2dot

python -m cProfile -o profile.pstats projects/art_tote.py
gprof2dot -f pstats profile.pstats | dot -Tsvg -o art_tote.svg
```

## To do

* more cut/joint types
  * dadoes/rebates
  * mortises & tenons https://en.wikipedia.org/wiki/Mortise_and_tenon
  * blind dovetail etc. https://en.wikipedia.org/wiki/Dovetail_joint
* shading of left side (visible when mitred/rotated)
* exploded view

* bugs:
  - 2nd board hex_box1-strips/fig-4.svg is missing the top shading stripe (when
     pins/tails swapped)
  - (not exactly a bug) painters z-order algorithm makes for some weird overlaps
    in assemblies
  - Assembly.add_walls isn't working for first side with mitred profiles?


## License

`woodwork-cad` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
