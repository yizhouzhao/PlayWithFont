# structures
import numpy as np
from freetype import Outline

from .font_util import *


FT_Curve_Tag_On = 0x01
FT_Curve_Tag_Conic = 0x00
FT_Curve_Tag_Cubic = 0x02


class Vectoriser():
    def __init__(self, outline: Outline, bezierSteps, reverse = False, size_factor = 1.0) -> None:
        self.outline = outline
        self.ftContourCount = len(outline.contours)
        self.contourFlag = outline.flags
        self.size_factor = size_factor

        self.ProcessContours(bezierSteps)

    def ProcessContours(self, bezierSteps):
        contourLength = 0
        startIndex = 0 
        endIndex = 0

        self.contourList = [] # list of Contour

        for i in range(self.ftContourCount):
            endIndex = self.outline.contours[i]
            contourLength =  (endIndex - startIndex) + 1

            tagList = self.outline.tags[startIndex: (endIndex + 1)]
            pointList = self.outline.points[startIndex: (endIndex + 1)]
            

            # new contour
            contour = Contour(pointList, tagList, contourLength, bezierSteps, self.size_factor)

            self.contourList.append(contour)
            startIndex = endIndex + 1


class Contour():
    def __init__(self, contourPoints, tags, n, bezierSteps, size_factor = 1.0) -> None:
        """
        contour: list of points
        """
        # variable
        self.minx = 65000.0
        self.miny = 65000.0
        self.maxx = -65000.0
        self.maxy = -65000.0

        self.size_factor = 1.0

        self.pointList = []

        #  Calculate contour direction
        signedArea = 0.0

        prev = np.array(contourPoints[-1])
        for i in range(n):
            cur = np.array(contourPoints[i])
            area = cur[0] * prev[1] - cur[1] * prev[0]
            signedArea += area

            prev = cur

        # If the final signed area is positive, it's a clockwise contour,
        # otherwise it's anti-clockwise.
        self.clockwise = signedArea > 0.0

        # if embolden contour
        # if size_factor != 1.0:
        #     contourPoints = shirnk_contour(contourPoints, step = size_factor - 1.0, is_exterior = self.clockwise)
        #     # else:
            #     contourPoints = shirnk_contour(contourPoints, step = 1.0 - size_factor)

        # init
        prev = None
        cur, next = np.array(contourPoints[-1]), np.array(contourPoints[0])

        for i in range(n):
            prev = cur
            cur = next
            next = np.array(contourPoints[(i + 1) % n])

            if n < 2 or (tags[i] & 0x03 == FT_Curve_Tag_On):
                self.AddPoint(cur)

            elif tags[i] & 0x03 == FT_Curve_Tag_Conic:
                prev2 = prev
                next2 = next
                if tags[(i - 1 + n) % n] & 0x03 == FT_Curve_Tag_Conic:
                    prev2 = (cur + prev) * 0.5
                    self.AddPoint(prev2)
                
                if tags[(i + 1) % n] & 0x03 == FT_Curve_Tag_Conic:
                    next2 = (cur + next) * 0.5

                self.evaluateQuadraticCurve(prev2, cur, next2, bezierSteps)

            elif tags[i] & 0x03 == FT_Curve_Tag_Cubic and \
                 tags[(i + 1) % n] & 0x03 == FT_Curve_Tag_Cubic:

                self.evaluateCubicCurve(prev, cur, next, np.array(contourPoints[(i + 2) % n]), bezierSteps)

      


    def AddPoint(self, point: np.array):
        if len(self.pointList) == 0 or \
            (not np.array_equal(point, self.pointList[-1]) and not np.array_equal(point, self.pointList[0])):
            self.pointList.append(point)

        self.minx = min(point[0], self.minx)
        self.miny = min(point[1], self.miny)
        self.maxx = max(point[0], self.maxx)
        self.maxy = max(point[1], self.maxy)

    def evaluateQuadraticCurve(self, A,  B,  C, bezierSteps):
        for i in range(bezierSteps):
            t = i / bezierSteps
            U = (1.0 - t) * A + t * B
            V = (1.0 - t) * B + t * C

            self.AddPoint((1.0 - t) * U + t * V)

    def evaluateCubicCurve(self, A, B, C, D, bezierSteps):
        for i in range(bezierSteps):
            t = i / bezierSteps
            U = (1.0 - t) * A + t * B
            V = (1.0 - t) * B + t * C
            W = (1.0 - t) * C + t * D

            M = (1.0 - t) * U + t * V
            N = (1.0 - t) * V + t * W

            self.AddPoint((1.0 - t) * M + t * N)

    def IsInside(self, big):
        if self.minx > big.minx and self.miny > big.miny \
            and self.maxx < big.maxx and self.maxy < big.maxy:
            return True
        
        return False

    # def change_contour_size(self, contour, size_factor):
    #     points = np.array(contour)
    #     polygon = Polygon(points)
    #     factor = size_factor - 1
    #     new_polygon = shrink_or_swell_shapely_polygon(polygon, factor = factor)

    #     return  list(new_polygon.exterior.coords)
        
class Vertex():
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.z = 0

        self.nx = 0
        self.ny = 0
        self.nz = 0
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z \
            and self.nx == other.nx and self.ny == other.ny and self.nz == other.nz
    
    def __sub__(self, other):
        r = Vertex()
        r.x = self.x - other.x
        r.y = self.y - other.y
        r.z = self.z - other.z
        return r

    def computeNormal(self, a, b, c):
        e1 = b - a
        e2 = c - a
        self.nx = e1.y * e2.z - e1.z * e2.y
        self.ny = e1.z * e2.x - e1.x * e2.z
        self.nz = e1.x * e2.y - e1.y * e2.x

        norm = np.sqrt(self.nx*self.nx + self.ny*self.ny + self.nz*self.nz)
        self.nx /= norm
        self.ny /= norm
        self.nz /= norm

class Mesh():
    def __init__(self) -> None:
        self.vertices = []
        self.indices = []

    def addVertex(self, v: Vertex):
        for index, item in enumerate(self.vertices):
            if item == v:
                return index + 1

        self.vertices.append(v)
        return len(self.vertices)

    def addTriangle(self, a:Vertex, b:Vertex, c:Vertex):
        a.computeNormal(a, b, c)
        c.nx = b.nx = a.nx
        c.ny = b.ny = a.ny 
        c.nz = b.nz = a.nz

        self.indices.append(self.addVertex(c))
        self.indices.append(self.addVertex(b))
        self.indices.append(self.addVertex(a))

    def print_mesh(self):
        print("Vertex Count: ", len(self.vertices))
        print("Index Count: ", len(self.indices))

    def saveOBJ(self, file_path, size = 0.01):
        with open(file_path, "w") as f:
            for i in range(len(self.vertices)):
                f.write(f"v {self.vertices[i].x * size} {self.vertices[i].y * size} {self.vertices[i].z * size}\n")

            for i in range(len(self.indices) // 3):
                f.write(f"f {self.indices[3 * i]} {self.indices[3 * i + 1]} {self.indices[3 * i + 2]}\n")



        