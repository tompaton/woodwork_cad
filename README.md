# Woodwork CAD

Procedural cad for my woodwork projects.

see [output/board_test.md](output/board_test.md) for basic operations.

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

## Usage

Create virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install mypy ruff
```

Run `make` to rebuild all projects and generate markdown files in `output/`.


## Unit testing

There are some "unit tests" in `geometry_test.md` for visualizing basic cases.

All generated output `.md` and `.svg` files are included in the repo so that
regressions can be detected.

Comparing svg file changes visually
```bash
git show main:output/art_tote/fig-1.svg > output/art_tote/fig-1~main.svg
xdg-open output/art_tote/fig-1~main.svg & disown
xdg-open output/art_tote/fig-1.svg & disown
```

## Performance profiling / optimization

```bash
pip install gprof2dot

python -m cProfile -o profile.pstats src/art_tote.py
gprof2dot -f pstats profile.pstats | dot -Tsvg -o art_tote.svg
```

## To do

* dadoes/rebates
* mortises & tennons
* mitred cuts
* shading of left side (visible when mitred/rotated)
* exploded view

* bugs:
  - 2nd board hex_box1-strips/fig-4.svg is missing the top shading stripe (when
     pins/tails swapped)
  - (not exactly a bug) painters z-order algorithm makes for some weird overlaps
    in assemblies
  - Assembly.add_walls isn't working for first side with mitred profiles?
