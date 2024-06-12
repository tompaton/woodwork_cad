.PHONY: woodwork_cad all

all: woodwork_cad
	python src/box1.py > output/box1.md

	python src/hex-box1a.py > output/hex-box1a.md
	python src/hex-box1a.py --strips > output/hex-box1a-strips.md
	python src/hex-box1a.py --strips --mitre > output/hex-box1a-strips-overlap-mitre.md

woodwork_cad: src/woodwork_cad/svg.py src/woodwork_cad/board.py
	ruff check . && mypy .

