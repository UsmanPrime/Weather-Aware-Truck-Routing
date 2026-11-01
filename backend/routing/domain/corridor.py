"""Bounded discrete corridor grid; no interpolation across unknown weather cells."""

from math import ceil, cos, floor, radians

from .types import Coordinate


def corridor_grid(routes: list[list[list[float]]], max_cells: int = 96):
    points = [p for line in routes for p in line]
    if any(abs(p[1]) > 75 for p in points):
        raise ValueError("Corridor layer supports latitudes within 75 degrees of the equator.")
    if max(p[0] for p in points) - min(p[0] for p in points) > 180:
        raise ValueError("The corridor layer does not yet support antimeridian-crossing trips.")
    lon0, lat0 = points[0][0], sum(p[1] for p in points) / len(points)
    scale_x, scale_y = 111195 * cos(radians(lat0)), 111195

    def project(p):
        return (((p[0] - lon0 + 180) % 360 - 180) * scale_x, (p[1] - lat0) * scale_y)

    def unproject(x, y):
        return [round((x / scale_x + lon0 + 180) % 360 - 180, 6), round(y / scale_y + lat0, 6)]

    projected = [[project(p) for p in line] for line in routes]
    edges = [(a, b) for line in projected for a, b in zip(line[:-1], line[1:], strict=True)]
    xs, ys = [p[0] for line in projected for p in line], [p[1] for line in projected for p in line]
    width, spacing = 25000, 12000
    minx, maxx, miny, maxy = min(xs) - width, max(xs) + width, min(ys) - width, max(ys) + width

    def inside(x, y):
        for (ax, ay), (bx, by) in edges:
            dx, dy = bx - ax, by - ay
            ratio = (
                max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
                if dx or dy
                else 0
            )
            if (x - ax - ratio * dx) ** 2 + (y - ay - ratio * dy) ** 2 <= width**2:
                return True
        return False

    for _ in range(25):
        nx, ny = ceil((maxx - minx) / spacing) + 2, ceil((maxy - miny) / spacing) + 2
        if nx * ny > 2000:
            spacing *= 2
            continue
        cells = []
        for ix in range(floor(minx / spacing), ceil(maxx / spacing) + 1):
            for iy in range(floor(miny / spacing), ceil(maxy / spacing) + 1):
                x, y = ix * spacing, iy * spacing
                if inside(x, y):
                    corners = [
                        unproject(x + dx * spacing / 2, y + dy * spacing / 2)
                        for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
                    ]
                    cells.append(
                        {"id": len(cells), "position": unproject(x, y), "polygon": corners}
                    )
        if len(cells) <= max_cells and cells:
            return cells, spacing, width
        if not cells:
            # Extremely long trips may be undersampled by a coarse global grid; report honestly.
            raise ValueError("Trip corridor is too large for the bounded forecast grid.")
        spacing = ceil(spacing * 1.3 / 1000) * 1000
    raise ValueError("Unable to build a bounded corridor grid")


def cell_positions(cells: list[dict]) -> tuple[Coordinate, ...]:
    return tuple(Coordinate(latitude=c["position"][1], longitude=c["position"][0]) for c in cells)
