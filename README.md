# Woodwork CAD

procedural cad for woodwork projects

NOTE: inline SVG in markdown output files renders in vscode, but not in github

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

* better shading of dovetailed ends
* assembly and plan/elevations
* dadoes/rebates
* mortises & tennons
* mitred cuts
