from collections import defaultdict
from typing import Callable, Dict, List

from .board import Board
from .operations import process
from .svg import SVGCanvas


class StockPile:
    def __init__(self) -> None:
        self.boards: Dict[str, List[Board]] = defaultdict(list)
        self.cutlist: List[Board] = []
        self.offcuts: Dict[str, List[Board]] = defaultdict(list)

    def add(self, key: str, count: int, board: Board) -> None:
        for i in range(count):
            # TODO: copy defects, shade etc.
            board2 = Board(board.L, board.W, board.T, label=f"{key}-{i+1}")
            self.boards[key].append(board2)

    def put(self, key: str, board: Board) -> None:
        if key in self.boards:
            msg = f"Can't put back offcut with {key} (used by boards already)"
            raise ValueError(msg)

        self.offcuts[key].append(board)

    def take(self, key: str) -> Board:
        for board in self.boards[key]:
            if not board.label.endswith(" (used)"):
                # TODO: copy defects, shade etc.
                board2 = Board(board.L, board.W, board.T, label=board.label)
                self.cutlist.append(board2)
                board.label += " (used)"
                board.shade("rgba(224,255,224,0.25)")
                return board2

        if self.offcuts[key]:
            return self.offcuts[key].pop(0)

        msg = f"No boards remaining with key='{key}'"
        raise ValueError(msg)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        for key, boards in self.boards.items():
            for i, board in enumerate(self.boards[key]):
                board.draw_board(canvas, x + i * 20, y + i * 20)
            y += board.W + 20 * (i + 1)

    def mark_waste(self) -> None:
        for key, boards in self.offcuts.items():
            for board in boards:
                board.waste()

    def take_part(self, key: str, op: Callable, remainder_key: str) -> Board:
        board, remainder = process(op)(self.take(key))
        self.put(remainder_key, remainder)
        return board
