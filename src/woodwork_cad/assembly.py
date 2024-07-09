from operator import attrgetter
from typing import Iterator, List

from .board import Board
from .faces import Face, rotate_faces
from .geometry import Point3d, Points, Vector3d
from .svg import SVGCanvas


class Assembly:
    def __init__(self) -> None:
        self.origin: Point3d = Point3d(0.0, 0.0, 0.0)
        self.boards: List[Board] = []
        self.positions: List[Vector3d] = []
        self.angles: List[float] = []

        self.subassemblies: List["Assembly"] = []

    def add_board(self, board: Board, position: Vector3d, angle: float) -> None:
        self.boards.append(board)
        self.positions.append(position)
        self.angles.append(angle)

    def add_walls(self, angle: float, sides: List[Board]) -> None:
        rotate_y = 0.0
        o = sides[0].profile.origin
        offset = Vector3d(-o.x, -o.y, -o.z)
        for side in sides:
            self.add_board(side, offset, rotate_y)

            # don't actually want to rotate any faces at this point, so pass in
            # empty list, but we want the rotated mate point as the next offset
            origin2d: List[Point3d] = []  # set in rotate_faces
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

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        for face in sorted(self.faces, key=attrgetter("_key")):
            face.draw(canvas, x, y)

    @property
    def faces(self) -> Iterator[Face]:
        for side, offset, rotate_y in zip(self.boards, self.positions, self.angles):
            x1, x2 = side.profile.interpolate(side.T)
            yield from rotate_faces(
                side._get_faces(x1, x2),
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

    def draw_plan(self, canvas: SVGCanvas, x: float, y: float) -> Points:
        corners: Points = []
        for side, position, angle in zip(self.boards, self.positions, self.angles):
            p = side.draw_plan(canvas, x + position.x, y + position.z, angle)
            canvas.circle(p.x, p.y, 2, "red")
            corners.append(p)

        return corners
