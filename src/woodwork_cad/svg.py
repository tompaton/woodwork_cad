from contextlib import contextmanager
from typing import Any, Iterator, List, Optional, Tuple


class SVGCanvas:
    def __init__(self) -> None:
        self.result = ""
        self.min_y: Optional[float] = None
        self.max_y: Optional[float] = None

    def _min_max_y(self, *ys) -> None:
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
        points: List[Tuple[float, float]],
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


@contextmanager
def print_svg(width: int, height: int = 0, zoom: float = 1.0) -> Iterator[SVGCanvas]:
    canvas = SVGCanvas()
    yield canvas
    # auto calculate height
    auto_height = (canvas.max_y or 0) + (canvas.min_y or 0)
    viewbox_str = " ".join(map(str, (0, 0, width, height or auto_height)))
    print()
    print(
        f'<svg width="{int(width * zoom)}" viewBox="{viewbox_str}" xmlns="http://www.w3.org/2000/svg">'
    )
    print(canvas.result + "</svg>")
    print()
    print()
