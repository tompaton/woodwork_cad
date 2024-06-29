from dataclasses import dataclass
from typing import Iterator, List, Optional


@dataclass
class Shade:
    y1: float
    y2: float
    colour: str


class Shades:
    def __init__(self, shades: Optional[List[Shade]] = None) -> None:
        self._shades: List[Shade] = shades or []

    def __iter__(self) -> Iterator[Shade]:
        yield from self._shades

    def add(self, y1: float, y2: float, colour: str) -> None:
        self._shades.append(Shade(y1, y2, colour))

    def extend(self, other: "Shades") -> None:
        self._shades.extend(other._shades)

    def select(self, min_y: float, max_y: float, offset_y: float = 0) -> "Shades":
        return Shades(
            [
                Shade(
                    max(s.y1, min_y) + offset_y, min(s.y2, max_y) + offset_y, s.colour
                )
                for s in self._shades
                if s.y1 < max_y and s.y2 > min_y
            ]
        )
