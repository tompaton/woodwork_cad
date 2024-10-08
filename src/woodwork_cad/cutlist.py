from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class Cut:
    op: str
    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    lx: float
    ly: float
    colour: str
    fill: str
    L: float = 0.0
    W: float = 0.0
    angle: float = 90.0


class Cuts:
    def __init__(self, cuts: list[Cut] | None = None) -> None:
        self._cuts: list[Cut] = cuts or []

    def __iter__(self) -> Iterator[Cut]:
        yield from self._cuts

    def add(
        self,
        op: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        lx: float = 0,
        ly: float = 0,
        L: float = 0,
        W: float = 0,
        angle: float = 90,
    ):
        if op == "cut":
            colour = "green"
        elif op == "rip":
            colour = "blue"
        else:
            colour = "rgba(255,0,0,0.25)"

        if op == "cut":
            fill = "rgba(0,255,0,0.25)"
        elif op == "rip":
            fill = "rgba(0,0,255,0.25)"
        else:
            fill = "rgba(255,0,0,0.25)"

        self._cuts.append(Cut(op, x1, y1, x2, y2, label, lx, ly, colour, fill, L, W, angle))
