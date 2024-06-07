from contextlib import contextmanager
from math import atan2, cos, degrees, sin
from typing import Any, Iterator, List, Tuple


class SVGCanvas:
    def __init__(
        self,
        maxx: int = 200,
        maxy: int = 150,
        w0: int = 200,
        h0: int = 150,
        pad: int = 20,
    ) -> None:
        # svg coords
        self.pad = pad
        self.w2 = w0 - 2 * self.pad
        self.h2 = h0 - 2 * self.pad

        # pixels
        self.maxx = maxx
        self.maxy = maxy
        if self.maxx / self.maxy > w0 / h0:
            self.w1: float = self.maxx
            self.h1: float = h0 * self.w1 / w0
        else:
            self.h1 = self.maxy
            self.w1 = w0 * self.h1 / h0

        self.result = ""

    # document

    def _write(self, xml: str) -> None:
        self.result += xml + "\n"

    def write(self, tag: str, content: str = "", **attrs: Any) -> None:
        attrs_str = " ".join(
            '{}="{}"'.format(k.replace("_", "-"), v) for k, v in attrs.items()
        )
        if content:
            self._write(f"<{tag} {attrs_str}>{content}</{tag}>")
        else:
            self._write(f"<{tag} {attrs_str} />")

    @contextmanager
    def document(
        self,
        width: int,
        viewbox: Tuple[float, float, float, float],
    ) -> Iterator[None]:
        viewbox_str = " ".join(map(str, viewbox))
        self._write(
            f'<svg width="{width}" viewBox="{viewbox_str}" xmlns="http://www.w3.org/2000/svg">'
        )
        yield
        self._write("</svg>")

    # pixels to coords

    def _x(self, x: float) -> float:
        return self.pad + x * self.w2 / self.w1

    def _y(self, y: float) -> float:
        return self.pad + y * self.h2 / self.h1

    def _center(
        self, x: float, y: float, width: float, height: float
    ) -> Tuple[float, float]:
        return x + width / 2, y + height / 2

    # drawing

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        colour: str,
        stroke_width: float = 0.4,
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

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        colour: str,
        stroke_width: float = 0.2,
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

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        colour: str,
        fill: str = "white",
        stroke_width: float = 0.2,
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

    def text(
        self,
        x: float,
        y: float,
        text_anchor: str = "middle",
        fill: str = "black",
        content: str = "text",
        style: str = "font-family: monospace; font-size: 4px",
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

    def polyline(
        self,
        colour: str,
        points: List[Tuple[float, float]],
        stroke_width: float = 0.2,
        stroke_dasharray: Any = 2,
        fill: str = "none",
        **attrs: Any,
    ) -> None:
        self.write(
            "polyline",
            fill=fill,
            stroke_width=stroke_width,
            stroke_dasharray=stroke_dasharray,
            stroke=colour,
            points=" ".join("{},{}".format(*p) for p in points),
            **attrs,
        )

    def dimension(
        self,
        label: str,
        position: str,
        colour: str,
        start: float,
        stop: float,
    ) -> None:
        _x = self._x
        _y = self._y

        if position == "top":
            self._dimension(
                label,
                colour,
                [(_x(start), 14), (_x(start), 15), (_x(stop), 15), (_x(stop), 14)],
                x=_x((start + stop) / 2),
                y=_y(0) - 7,
            )

        elif position == "left":
            self._dimension(
                label,
                colour,
                [(14, _y(start)), (15, _y(start)), (15, _y(stop)), (14, _y(stop))],
                transform=f"rotate(-90) translate(-{_y((start+stop)/2)}, 12)",
            )

        elif position == "bottom":
            self._dimension(
                label,
                colour,
                [
                    (_x(start), _y(self.maxy) + 5),
                    (_x(start), _y(self.maxy) + 4),
                    (_x(stop), _y(self.maxy) + 4),
                    (_x(stop), _y(self.maxy) + 5),
                ],
                x=_x((start + stop) / 2),
                y=_y(self.maxy) + 10,
            )

        elif position == "right":
            self._dimension(
                label,
                colour,
                [
                    (_x(self.maxx) + 6, _y(start)),
                    (_x(self.maxx) + 5, _y(start)),
                    (_x(self.maxx) + 5, _y(stop)),
                    (_x(self.maxx) + 6, _y(stop)),
                ],
                transform=(
                    f"rotate(90) translate({_y((start+stop)/2)}, -{_x(self.maxx)+10})"
                ),
            )

    def _dimension(
        self,
        label: str,
        colour: str,
        points: List[Tuple[float, float]],
        x: float = 0,
        y: float = 0,
        transform: str = "",
    ) -> None:
        self.polyline(colour, points)
        self.text(x, y, transform=transform, content=label)

    def arrow(self, colour: str, x1: float, y1: float, x2: float, y2: float) -> None:
        _x = self._x
        _y = self._y
        angle = atan2((y2 - y1), (x2 - x1))
        dx, dy = cos(angle), sin(angle)
        self.line(_x(x1), _y(y1), _x(x2), _y(y2), colour, stroke_dasharray=1)
        self.polyline(
            colour,
            [(-1, -0.5), (0, 0), (-1, 0.5)],
            stroke_dasharray="",
            transform=f"translate({_x(x2)-dx}, {_y(y2)-dy}) scale(1.5) rotate({degrees(angle)})",
            fill=colour,
        )


@contextmanager
def print_svg(width: int, height: int) -> Iterator[SVGCanvas]:
    canvas = SVGCanvas()
    with canvas.document(width, (0, 0, width, height)):
        yield canvas
    print(canvas.result)
