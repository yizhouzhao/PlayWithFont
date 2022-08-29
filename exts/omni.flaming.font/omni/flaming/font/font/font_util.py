# util
from shapely import geometry
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

import triangle as tr
import numpy as np

def triangulate_contour(outer_contour_points, inner_contour_points_list):
    """
    Outer contour: outer contour
    Inner contour list list of inner line
    """
    outer_n = len(outer_contour_points)
    i = np.arange(outer_n)
    seg_outer = np.stack([i, i + 1], axis=1) % outer_n
    
    seg_list = [seg_outer.tolist()]
    hole_list = []
    for inner_points in inner_contour_points_list:
        inner_n = len(inner_points)

        inner_center = np.mean(inner_points, axis = 0).tolist()
        hole_list.append(inner_center)

        i = np.arange(inner_n)
        seg_inner = np.stack([i, i + 1], axis=1) % inner_n + sum([len(s) for s in seg_list])
        seg_list.append(seg_inner.tolist())

    if len(inner_contour_points_list)> 0:
        A = dict(vertices=np.vstack([outer_contour_points] + inner_contour_points_list), 
            segments = np.vstack(seg_list), 
            holes= hole_list)
    else:
        A = dict(vertices=np.vstack([outer_contour_points]), 
            segments = np.vstack(seg_list))

    B = tr.triangulate(A, 'qpa')

    return B




def intepolate_outline(outlines: list, max_step: float = 30):
    """
    Intepolate outline by a maximum step:
    """
    is_outline_list = []
    point_list = []
    for outline in outlines:
        for i in range(len(outline)):
            p1 = outline[i]
            p2 = outline[(i + 1) % len(outline)]

            outline_points = intepolate_two_points(p1, p2, max_step)

            point_list.extend(outline_points)
            is_outline_list.extend([True] + [False] * (len(outline_points) - 1))

    return point_list, is_outline_list

def intepolate_two_points(p1, p2, max_step: float):
    """
    Intepolate two points by a maximum step:
    """
    point1 = np.array(p1)
    point2 = np.array(p2)

    n = 1
    while np.linalg.norm(point1 - point2) / n >= max_step:
        n += 1

    point_list = []
    for i in range(n):
        p = (1 - i / n) * point1 + (i / n) * point2
        point_list.append(p.tolist())

    return point_list

    
def grid_points_inside_polygon(polygon: Polygon, grid_size: int):
    """
    Generate points inside the polygon
    """
    latmin, lonmin, latmax, lonmax = polygon.bounds
    
    # resolution_lat = int((latmax - latmin) / grid_size)
    # resolution_lon = int((lonmax - lonmin) / grid_size)
    # print("resolution_lat", resolution_lat, resolution_lon)
    # create prepared polygon
    prep_polygon = prep(polygon)

    # construct a rectangular mesh
    points = []
    for lat in np.arange(latmin, latmax, grid_size):
        for lon in np.arange(lonmin, lonmax, grid_size):
            points.append(Point((round(lat,4), round(lon,4))))

    return [(p.x, p.y) for p in filter(prep_polygon.contains, points)]