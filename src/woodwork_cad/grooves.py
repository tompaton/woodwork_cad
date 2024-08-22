from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class Groove:
    y1: float
    y2: float
    depth: float
    face: bool


@dataclass(order=True)
class Flat:
    z: float
    y1: float
    y2: float


@dataclass
class Side:
    y: float
    z1: float
    z2: float


class Grooves:
    def __init__(self, grooves: list[Groove] | None = None) -> None:
        self._grooves: list[Groove] = grooves or []

    def add(self, y: float, height: float, depth: float, *, face: bool = True) -> None:
        self._grooves.append(Groove(y, y + height, depth, face))

    def select(self, min_y: float, max_y: float, offset_y: float = 0) -> "Grooves":
        return Grooves(
            [
                Groove(
                    max(groove.y1, min_y) + offset_y,
                    min(groove.y2, max_y) + offset_y,
                    groove.depth,
                    groove.face,
                )
                for groove in self._grooves
                if groove.y1 < max_y and groove.y2 > min_y
            ]
        )

    def flats(self, W: float, T: float, *, face: bool) -> Iterable[Flat]:
        y0 = 0.0
        for groove in self._grooves:
            if groove.face == face:
                yield Flat(0.0 if face else T, y0, groove.y1)
                yield Flat(
                    groove.depth if face else T - groove.depth,
                    groove.y1,
                    groove.y2,
                )
                y0 = groove.y2
        yield Flat(0.0 if face else T, y0, W)

    def sides(self, T: float, *, top: bool, face: bool) -> Iterable[Side]:
        for groove in self._grooves:
            if top:
                if groove.face and face:
                    yield Side(groove.y2, 0.0, groove.depth)
                if not groove.face and not face:
                    yield Side(groove.y2, T - groove.depth, T)
            else:
                if groove.face and face:
                    yield Side(groove.y1, 0.0, groove.depth)
                if not groove.face and not face:
                    yield Side(groove.y1, T - groove.depth, T)
