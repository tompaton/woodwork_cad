from dataclasses import dataclass
from typing import Iterator, List, Optional


from .svg import SVGCanvas


class Defect:
    def offset(self, offset_x: float, offset_y: float) -> "Defect":
        raise NotImplementedError

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        raise NotImplementedError

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        raise NotImplementedError


class Defects:
    def __init__(self, defects: Optional[List[Defect]] = None) -> None:
        self._defects = defects or []

    def __iter__(self) -> Iterator[Defect]:
        yield from self._defects

    def add(self, defect: Defect) -> None:
        self._defects.append(defect)

    def extend(self, other: "Defects") -> None:
        self._defects.extend(other._defects)

    def select(self, offset_x: float, offset_y: float) -> "Defects":
        return Defects([defect.offset(offset_x, offset_y) for defect in self._defects])


@dataclass
class Hole(Defect):
    x: float
    y: float
    r: float = 5

    def offset(self, offset_x: float, offset_y: float) -> "Hole":
        return Hole(self.x + offset_x, self.y + offset_y, self.r)

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return (offset_x < self.x < offset_x + L) and (offset_y < self.y < offset_y + W)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.circle(x + self.x, y + self.y, self.r, "orange")


@dataclass
class Notch(Defect):
    x1: float
    y1: float
    x2: float
    y2: float

    def offset(self, offset_x: float, offset_y: float) -> "Notch":
        return Notch(
            self.x1 + offset_x,
            self.y1 + offset_y,
            self.x2 + offset_x,
            self.y2 + offset_y,
        )

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return not (
            self.x2 < offset_x
            or self.x1 > offset_x + L
            or self.y2 < offset_y
            or self.y1 > offset_y + W
        )

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.rect(
            x + self.x1, y + self.y1, self.x2 - self.x1, self.y2 - self.y1, "orange"
        )
