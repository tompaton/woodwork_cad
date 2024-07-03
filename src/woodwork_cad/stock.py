from collections import defaultdict
from typing import Dict, List

from .board import Board
from .svg import SVGCanvas


class StockPile:
    def __init__(self) -> None:
        self.boards: Dict[str, List[Board]] = defaultdict(list)
        self.cutlist: List[Board] = []

    def add(self, key, count, board: Board) -> None:
        for i in range(count):
            # TODO: copy defects, shade etc.
            board2 = Board(board.L, board.W, board.T, label=f"{key}-{i+1}")
            self.boards[key].append(board2)

    def take(self, key) -> Board:
        for board in self.boards[key]:
            if not board.label.endswith(" (used)"):
                board.label += " (used)"
                board.shade("rgba(224,255,224,0.25)")
                # TODO: copy defects, shade etc.
                board2 = Board(board.L, board.W, board.T)
                self.cutlist.append(board2)
                return board2

        msg = f"No boards remaining with key='{key}'"
        raise ValueError(msg)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        for key, boards in self.boards.items():
            for i, board in enumerate(self.boards[key]):
                board.draw_board(canvas, x + i * 20, y + i * 20)
            y += board.W + 20 * (i + 1)
