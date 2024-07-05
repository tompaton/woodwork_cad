from contextlib import contextmanager
from math import sqrt
from pathlib import Path
from typing import Any, Iterator, Optional, Tuple

from .geometry import Points, Points3d, to2d


class SVGCanvas:
    def __init__(self) -> None:
        self.result = ""
        self.min_y: Optional[float] = None
        self.max_y: Optional[float] = None

    def _min_max_y(self, *ys) -> None:
        if ys:
            self.min_y = min(self.min_y or ys[0], *ys)
            self.max_y = max(self.max_y or ys[0], *ys)

    def write(self, tag: str, content: str = "", **attrs: Any) -> None:
        attrs_str = " ".join(
            '{}="{}"'.format(k.replace("_", "-"), v) for k, v in attrs.items()
        )
        if content:
            self.result += f"<{tag} {attrs_str}>{content}</{tag}>\n"
        else:
            self.result += f"<{tag} {attrs_str} />\n"

    def svg_document(self, width: int, height: int, zoom: float = 1.0) -> str:
        # auto calculate height
        auto_height = (self.max_y or 0) + (self.min_y or 0)
        viewbox_str = " ".join(
            map(str, (0, min(0, (self.min_y or 0)), width, height or auto_height))
        )
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
            cx=cx,
            cy=cy,
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
            points=" ".join("{},{}".format(*p) for p in points),
            **attrs,
        )
        self._min_max_y(*(y for x, y in points))

    def polyline3d(self, colour: str, points: Points3d, **kwargs: Any) -> None:
        return self.polyline(colour, [to2d(p) for p in points], **kwargs)


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
        self.canvas: Optional[SVGCanvas] = None
        self.width: int = 0
        self.height: int = 0
        self.zoom: float = 1.0

    def __call__(
        self, width: int, height: int = 0, zoom: float = 1.0
    ) -> "PrintToSVGFiles":
        self.width = width
        self.height = height
        self.zoom = zoom
        return self

    def __enter__(self) -> SVGCanvas:
        self.figure += 1
        self.canvas = SVGCanvas()
        return self.canvas

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        assert self.canvas is not None
        f = Path(f"output/{self.prefix}/fig-{self.figure}.svg")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(self.canvas.svg_document(self.width, self.height, self.zoom))
        print()
        print(f"![Figure {self.figure}]({f.relative_to('output/')})")
        print()
        self.canvas = None


def polyline_bounds(corners: Points) -> Tuple[float, float, Points]:
    min_hex_x = min(x for x, y in corners)
    min_hex_y = min(y for x, y in corners)
    hex_L = max(x for x, y in corners) - min_hex_x
    hex_W = max(y for x, y in corners) - min_hex_y
    return hex_L, hex_W, offset_points(-min_hex_x, -min_hex_y, corners)


def crop_points(points: Points, height: float) -> Points:
    return [(x, y) for x, y in points if -1 <= y <= height + 1]


def offset_points(offset_x: float, offset_y: float, points: Points) -> Points:
    return [(x + offset_x, y + offset_y) for x, y in points]


def shrink_points(corners: Points, delta: float) -> Tuple[float, float, Points]:
    width, height = polyline_bounds(corners)[:2]
    cx, cy = width / 2, height / 2
    corners2: Points = []
    for x, y in corners:
        dx, dy = cx - x, cy - y
        length = sqrt(dx * dx + dy * dy)
        x1, y1 = dx / length, dy / length  # unit vector from corner to center
        corners2.append((x + x1 * delta, y + y1 * delta))
    return polyline_bounds(corners2)
