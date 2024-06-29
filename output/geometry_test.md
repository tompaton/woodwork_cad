# Geometry test

## line_intersection

![Figure 1](geometry_test/fig-1.svg)

## is_inside

![Figure 2](geometry_test/fig-2.svg)

## test for sutherland-hodgman

![Figure 3](geometry_test/fig-3.svg)

## clip_polygon (sutherland-hodgman)
this fails when the clip polygon is not convex

![Figure 4](geometry_test/fig-4.svg)

## clip_polygon2 - union (Greiner and Hormann)

![Figure 5](geometry_test/fig-5.svg)

## clip_polygon2 - difference (Greiner and Hormann)
this is now the simplest, but clip polygon still can't be coincident...

![Figure 6](geometry_test/fig-6.svg)

## clip_polygon2 - reversed-diff (Greiner and Hormann)

![Figure 7](geometry_test/fig-7.svg)

## clip_polygon2 - intersection (Greiner and Hormann)
polygons can't be coincident, so make clip region a little larger and it works

![Figure 8](geometry_test/fig-8.svg)

## dot product, cross product
(1, 0, 0) x (0, 1, 0) = (0, 0, 1)

(0, 1, 0) x (1, 0, 0) = (0, 0, -1)

(0.5, 0.5, 0) x (0, 1, 0) = (0.0, 0.0, 0.5)

(0, 1, 0) x (0.5, 0.5, 0) = (0.0, 0.0, -0.5)

(0, 1, 0) x (0, 0, 1) = (1, 0, 0)

(0, 0, 1) x (0, 1, 0) = (-1, 0, 0)


![Figure 9](geometry_test/fig-9.svg)

