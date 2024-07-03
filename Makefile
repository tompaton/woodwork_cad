.PHONY: woodwork_cad projects all

all: woodwork_cad projects

projects:
	python src/box1.py > output/box1.md

	python src/hex-box1.py > output/hex-box1.md
	python src/hex-box1.py --strips > output/hex-box1-strips.md
	python src/hex-box1.py --strips --mitre > output/hex-box1-strips-overlap-mitre.md

	python src/art_tote.py > output/art_tote.md

woodwork_cad:
	ruff check . && mypy .
	python src/geometry_test.py > output/geometry_test.md
	python src/board_test.py > output/board_test.md

