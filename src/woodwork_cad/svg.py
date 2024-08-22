from collections.abc import Iterator
from contextlib import contextmanager
from math import atan2, cos, degrees, sin, sqrt
from pathlib import Path
from typing import Any

from woodwork_cad.geometry import (
    Point,
    Point3d,
    Points,
    Points3d,
    get_camera,
    set_camera,
    to2d,
)


class SVGCanvas:
    def __init__(self) -> None:
        self.result = ""
        self.min_y: float | None = None
        self.max_y: float | None = None

    def _min_max_y(self, *ys) -> None:
        if ys:
            self.min_y = min(self.min_y or ys[0], *ys)
            self.max_y = max(self.max_y or ys[0], *ys)

    def write(self, tag: str, content: str = "", **attrs: Any) -> None:
        attrs_str = " ".join('{}="{}"'.format(k.replace("_", "-"), v) for k, v in attrs.items())
        if content:
            self.result += f"<{tag} {attrs_str}>{content}</{tag}>\n"
        else:
            self.result += f"<{tag} {attrs_str} />\n"

    def svg_document(self, width: int, height: int, zoom: float = 1.0) -> str:
        # auto calculate height
        auto_height = abs(self.max_y or 0) + abs(self.min_y or 0)
        min_y = min(0, self.min_y or 0)
        viewbox_str = f"{0:.1f} {min_y:.1f} {width:.1f} {height or auto_height:.1f}"
        return (
            f'<svg width="{int(width * zoom)}" viewBox="{viewbox_str}" xmlns="http://www.w3.org/2000/svg">\n'
            f"{self.result}</svg>\n"
        )

    # drawing

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        colour: str,
        stroke_width: float = 1,
        fill: str = "none",
        **attrs: Any,
    ) -> None:
        self.write(
            "rect",
            x=x,
            y=y,
            width=width,
            height=height,
            style=f"fill: {fill}; stroke: {colour}; stroke-width: {stroke_width};",
            **attrs,
        )
        self._min_max_y(y, y + height)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        colour: str,
        stroke_width: float = 1,
        **attrs: Any,
    ) -> None:
        self.write(
            "line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            stroke=colour,
            stroke_width=stroke_width,
            **attrs,
        )
        self._min_max_y(y1, y2)

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        colour: str,
        fill: str = "white",
        stroke_width: float = 1,
        **attrs: Any,
    ) -> None:
        self.write(
            "circle",
            cx=round(cx, 1),
            cy=round(cy, 1),
            r=r,
            stroke=colour,
            fill=fill,
            stroke_width=stroke_width,
            **attrs,
        )
        self._min_max_y(cy - r, cy + r)

    def text(
        self,
        x: float,
        y: float,
        text_anchor: str = "middle",
        fill: str = "black",
        content: str = "text",
        style: str = "",
        **attrs: Any,
    ) -> None:
        self.write(
            "text",
            style=style,
            text_anchor=text_anchor,
            x=x,
            y=y,
            fill=fill,
            content=content,
            **attrs,
        )
        self._min_max_y(y)

    def polyline(
        self,
        colour: str,
        points: Points,
        *,
        stroke_width: float = 1,
        stroke_dasharray: Any = "",
        fill: str = "none",
        closed: bool = False,
        **attrs: Any,
    ) -> None:
        self.write(
            "polygon" if closed else "polyline",
            fill=fill,
            stroke_width=stroke_width,
            stroke_dasharray=stroke_dasharray,
            stroke=colour,
            points=" ".join(f"{p.x:.1f},{p.y:.1f}" for p in points),
            **attrs,
        )
        self._min_max_y(*(p.y for p in points))

    def polyline3d(
        self,
        colour: str,
        points: Points3d,
        x: float = 0.0,
        y: float = 0.0,
        **kwargs: Any,
    ) -> None:
        return self.polyline(colour, [to2d(p, offset_x=x, offset_y=y) for p in points], **kwargs)

    def vertical_arrow(
        self,
        x: float,
        y: float,
        corner_top: Point3d,
        corner_bottom: Point3d,
        arrow_top: Point3d,
        arrow_bottom: Point3d,
        text: str,
        *,
        left: bool = False,
    ) -> None:
        self.polyline3d("silver", [corner_bottom, arrow_bottom], x, y, stroke_dasharray=2)
        self.polyline3d("silver", [corner_top, arrow_top], x, y, stroke_dasharray=2)
        self.polyline3d("gray", [arrow_top, arrow_bottom], x, y, stroke_dasharray=2)
        p1 = to2d(arrow_top, x, y)
        p2 = to2d(arrow_bottom, x, y)
        self.arrow(p1.x, p1.y, p2.x, p2.y)
        self.arrow(p2.x, p2.y, p1.x, p1.y)

        top2 = to2d(arrow_top, x, y)
        bottom2 = to2d(arrow_bottom, x, y)
        x2 = (top2.x + bottom2.x) / 2
        y2 = (top2.y + bottom2.y) / 2
        w = 5 * (len(text) + 3)
        self.rect(x2 - 5, y2 - w / 2, 10, w, "none", fill="rgba(255,255,255,0.75)")
        self.text(
            0,
            0,
            content=text,
            style="font-size:12px",
            transform=f"translate({x2+3} {y2}) rotate(-90)" if left else f"translate({x2-3} {y2}) rotate(90)",
        )

    def horizontal_arrow(
        self,
        x: float,
        y: float,
        corner_left: Point3d,
        corner_right: Point3d,
        arrow_left: Point3d,
        arrow_right: Point3d,
        text: str,
    ) -> None:
        self.polyline3d("silver", [corner_right, arrow_right], x, y, stroke_dasharray=2)
        self.polyline3d("silver", [corner_left, arrow_left], x, y, stroke_dasharray=2)
        self.polyline3d("gray", [arrow_left, arrow_right], x, y, stroke_dasharray=2)
        p1 = to2d(arrow_left, x, y)
        p2 = to2d(arrow_right, x, y)
        self.arrow(p1.x, p1.y, p2.x, p2.y)
        self.arrow(p2.x, p2.y, p1.x, p1.y)

        left2 = to2d(arrow_left, x, y)
        right2 = to2d(arrow_right, x, y)
        x2 = (left2.x + right2.x) / 2
        y2 = (left2.y + right2.y) / 2
        w = 5 * (len(text) + 3)
        self.rect(x2 - w / 2, y2 - 5, w, 10, "none", fill="rgba(255,255,255,0.75)")
        self.text(x2, y2 + 3, content=text, style="font-size:12px")

    def arrow(self, x1: float, y1: float, x2: float, y2: float, colour: str = "gray") -> None:
        angle = atan2((y2 - y1), (x2 - x1))
        dx, dy = cos(angle), sin(angle)
        self.polyline(
            colour,
            [Point(-4, -2), Point(0, 0), Point(-4, 2)],
            transform=f"translate({x2-dx}, {y2-dy}) rotate({degrees(angle)})",
        )


@contextmanager
def print_svg(width: int, height: int = 0, zoom: float = 1.0) -> Iterator[SVGCanvas]:
    canvas = SVGCanvas()
    yield canvas
    print()
    print(canvas.svg_document(width, height, zoom))
    print()


class PrintToSVGFiles:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.figure = 0
        self.canvas: SVGCanvas | None = None
        self.width: int = 0
        self.height: int = 0
        self.zoom: float = 1.0
        self.default_camera: str = "below"
        self.camera: str = "below"
        self.old_camera: str = "below"

    def __call__(self, width: int, height: int = 0, zoom: float = 1.0, camera: str = "") -> "PrintToSVGFiles":
        self.width = width
        self.height = height
        self.zoom = zoom
        self.camera = camera or self.default_camera
        return self

    def __enter__(self) -> SVGCanvas:
        self.figure += 1
        self.canvas = SVGCanvas()

        self.old_camera = get_camera()
        set_camera(self.camera)
        return self.canvas

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.canvas is None:
            raise AssertionError

        set_camera(self.old_camera)
        f = Path(f"projects/output/{self.prefix}/fig-{self.figure}.svg")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(self.canvas.svg_document(self.width, self.height, self.zoom))
        print()
        print(f"![Figure {self.figure}]({f.relative_to('projects/output/')})")
        print()
        self.canvas = None


def polyline_bounds(corners: Points) -> tuple[float, float, Points]:
    min_hex_x = min(p.x for p in corners)
    min_hex_y = min(p.y for p in corners)
    hex_L = max(p.x for p in corners) - min_hex_x
    hex_W = max(p.y for p in corners) - min_hex_y
    return hex_L, hex_W, offset_points(-min_hex_x, -min_hex_y, corners)


def crop_points(points: Points, height: float) -> Points:
    return [p for p in points if -1 <= p.y <= height + 1]


def offset_points(offset_x: float, offset_y: float, points: Points) -> Points:
    return [Point(p.x + offset_x, p.y + offset_y) for p in points]


def shrink_points(corners: Points, delta: float) -> tuple[float, float, Points]:
    width, height = polyline_bounds(corners)[:2]
    cx, cy = width / 2, height / 2
    corners2: Points = []
    for p in corners:
        dx, dy = cx - p.x, cy - p.y
        length = sqrt(dx * dx + dy * dy)
        x1, y1 = dx / length, dy / length  # unit vector from corner to center
        corners2.append(Point(p.x + x1 * delta, p.y + y1 * delta))
    return polyline_bounds(corners2)
