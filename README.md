# Woodwork CAD

procedural cad for woodwork projects

see [output/board_test.md](output/board_test.md) for basic operations.

## Usage

Create virtual environment and install dependencies
```
python -m venv venv
source venv/bin/activate
pip install mypy ruff
```

Run `make` to rebuild all projects and generate markdown files in `output/`.


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
