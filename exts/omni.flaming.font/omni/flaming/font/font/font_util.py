# util
from shapely import geometry
from shapely.geometry import Polygon, Point
from shapely.ops import triangulate
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







def triangulate_within(polygon):
    return [triangle for triangle in triangulate(polygon) if triangle.covered_by(polygon)]

def shirnk_contour(contour:list, step, is_exterior = True, scale = 10000):
    """
    shrink contour: a list of points
    """
    polygon = Polygon(contour)
    new_contour = []

    center = np.mean(contour, axis = 0)
    print("center", center)
    for point in contour:
        center_to_point = (point[0] - center[0], point[1] - center[1])
        center_to_point_norm = np.sqrt(center_to_point[0] ** 2 + center_to_point[1] ** 2 + 1e-6)
        center_to_point = (center_to_point[0] / center_to_point_norm, center_to_point[1] / center_to_point_norm)
        print("center_to_point", center_to_point)
        new_point = Point(center_to_point[0] * step + point[0], center_to_point[1] * step + point[1])

        scale = scale * step
        if is_exterior:
            if not new_point.within(polygon):
                new_contour.append([center_to_point[0] * scale  + point[0], center_to_point[1] * scale + point[1]])
            else:
                new_contour.append([-center_to_point[0] * scale + point[0], -center_to_point[1] * scale + point[1]])
        else:
            if new_point.within(polygon):
                new_contour.append([center_to_point[0] * scale + point[0], center_to_point[1] * scale + point[1]])
            else:
                new_contour.append([-center_to_point[0] * scale + point[0], -center_to_point[1] * scale + point[1]])

        
    return new_contour
