from collections.abc import Iterator
from dataclasses import dataclass
from operator import attrgetter

from woodwork_cad.board import Board
from woodwork_cad.faces import Face, rotate_faces
from woodwork_cad.geometry import Point, Point3d, Points, Vector3d
from woodwork_cad.operations import draw_dimension_ex
from woodwork_cad.svg import SVGCanvas


@dataclass
class Dimension:
    index: int
    dimension: str
    position: str
    pad: float = 10
    subassembly: int = -1


class Assembly:
    def __init__(self) -> None:
        self.origin: Point3d = Point3d(0.0, 0.0, 0.0)
        self.boards: list[Board] = []
        self.positions: list[Vector3d] = []
        self.angles: list[float] = []

        self.subassemblies: list[Assembly] = []

    def add_board(self, board: Board, position: Vector3d, angle: float) -> None:
        self.boards.append(board)
        self.positions.append(position)
        self.angles.append(angle)

    def add_walls(self, angle: float, sides: list[Board]) -> None:
        rotate_y = 0.0
        o = sides[0].profile.origin
        offset = Vector3d(-o.x, -o.y, -o.z)
        for side in sides:
            self.add_board(side, offset, rotate_y)

            # don't actually want to rotate any faces at this point, so pass in
            # empty list, but we want the rotated mate point as the next offset
            origin2d: list[Point3d] = []  # set in rotate_faces
            list(
                rotate_faces(
                    [],
                    side.profile.origin,
                    rotate_y,
                    offset,
                    side.profile.mate,
                    origin2d,
                )
            )

            offset = Vector3d(origin2d[1].x, origin2d[1].y, origin2d[1].z)

            rotate_y += angle

    def add_subassembly(self, offset: Vector3d, assembly: "Assembly") -> None:
        assembly.origin = Point3d(offset.x, offset.y, offset.z)
        self.subassemblies.append(assembly)

    def draw(self, canvas: SVGCanvas, x: float, y: float, *dimensions: Dimension) -> None:
        for face in sorted(self.faces, key=attrgetter("_key")):
            face.draw(canvas, x, y)

        self.draw_dimensions(canvas, x, y, *dimensions)

    def draw_dimensions(self, canvas: SVGCanvas, x: float, y: float, *dimensions: Dimension) -> None:
        for dimension in dimensions:
            if dimension.subassembly == -1:
                assembly = self
            else:
                assembly = self.subassemblies[dimension.subassembly]

            assembly.draw_dimension(
                canvas,
                x,
                y,
                dimension.index,
                dimension.dimension,
                dimension.position,
                dimension.pad,
            )

    def draw_dimension(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        index: int,
        dimension: str,
        position: str,
        pad: float = 10,
    ) -> None:
        board = self.boards[index]
        offset = self.positions[index]
        rotate_y = self.angles[index]

        start, end, arrow_start, arrow_end, text = board.get_dimension(dimension, position, pad)

        face = Face([start, end, arrow_end, arrow_start])

        face = next(
            rotate_faces(
                [face],
                board.profile.origin,
                rotate_y,
                Vector3d(
                    offset.x + self.origin.x,
                    offset.y + self.origin.y,
                    offset.z + self.origin.z,
                ),
                board.profile.mate,
                [],
            )
        )

        start, end, arrow_end, arrow_start = face.points

        draw_dimension_ex(canvas, x, y, start, end, arrow_start, arrow_end, text, dimension, position)

    @property
    def faces(self) -> Iterator[Face]:
        for side, offset, rotate_y in zip(self.boards, self.positions, self.angles, strict=False):
            x1, x2 = side.profile.interpolate(side.T)
            yield from rotate_faces(
                side.get_faces(x1, x2),
                side.profile.origin,
                rotate_y,
                Vector3d(
                    offset.x + self.origin.x,
                    offset.y + self.origin.y,
                    offset.z + self.origin.z,
                ),
                side.profile.mate,
                [],
            )

        for assembly in self.subassemblies:
            yield from assembly.faces

    def get_corners(self, x: float, y: float) -> Points:
        return [Point(p.x + x, y - p.z) for p in self.positions[1:] + self.positions[:1]]
