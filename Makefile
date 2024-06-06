.PHONY: woodwork_cad

woodwork_cad: src/woodwork_cad/svg.py src/woodwork_cad/board.py
	ruff check . && mypy .

output/box1.md: src/box1.py woodwork_cad
	python src/box1.py > output/box1.md

