from typing import List

from .board import Board
from .faces import Face
from .geometry import Point3d, Points
from .svg import SVGCanvas


class Assembly:
    def __init__(self) -> None:
        self.boards: List[Board] = []
        self.positions: List[Point3d] = []
        self.angles: List[float] = []

        self.faces: List[Face] = []

    def add_walls(self, angle: float, sides: List[Board]) -> None:
        angle, da = 0, angle
        mate = (0.0, 0.0, 0.0)
        for side in sides:
            self.boards.append(side)
            self.positions.append(mate)
            self.angles.append(angle)

            # need to collect together all rotate faces
            mate = side.rotated_faces(rotate_y=angle, offset=mate, faces=self.faces)[1]

            angle += da

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        for face in sorted(self.faces):
            face.draw(canvas, x, y)

    def draw_plan(self, canvas: SVGCanvas, x: float, y: float) -> Points:
        corners: Points = []
        for side, position, angle in zip(self.boards, self.positions, self.angles):
            x1, y1, z1 = position
            x2, y2 = side.draw_plan(canvas, x + x1, y + z1, angle)
            canvas.circle(x2, y2, 2, "red")
            corners.append((x2, y2))

        return corners
