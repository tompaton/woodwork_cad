.PHONY: woodwork_cad projects all

all: woodwork_cad projects

projects:
	python projects/box1.py > projects/output/box1.md

	python projects/hex-box1.py > projects/output/hex-box1.md
	python projects/hex-box1.py --strips > projects/output/hex-box1-strips.md
	python projects/hex-box1.py --strips --mitre > projects/output/hex-box1-strips-overlap-mitre.md

	python projects/art_tote.py > projects/output/art_tote.md

woodwork_cad:
	python projects/geometry_test.py > projects/output/geometry_test.md
	python projects/board_test.py > projects/output/board_test.md

