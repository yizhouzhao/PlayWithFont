import numpy as np
from freetype import *

from .font_struct import *
from .font_util import *


class MeshGenerator():
    def __init__(self, fontFile, height:int, text:str, 
        bezierSteps = 3, extrude = 96, bevelRadius = 0, bevelSteps=4) -> None:

        # properties
        self.fontFile = fontFile
        self.height = height
        self.text = text
        self.bezierSteps = bezierSteps
        self.extrude = extrude
        self.bevelRadius = bevelRadius
        self.bevelSteps = bevelSteps

        # records
        self.mesh = None
        self.outlines = []
        self.polygons = []
        self.offsets = []
    
    def shutdown(self):
        self.mesh = None
        self.outlines = None
        self.polygons = None
        self.offsets = None

    def generateMesh(self, create_obj = True):
        """
        Generate mesh front font data
        """
        # init font
        self.face = Face(self.fontFile)
        self.face.set_char_size(self.height << 6, self.height << 6, 96, 96)

        # init mesh
        self.mesh = Mesh()
        self.offset = 0

        self.previous = 0
        for c in self.text:
            self.AddCharacter(c, create_obj=create_obj)

    def saveMesh(self, mesh_file = "test0.obj"):
        self.mesh.saveOBJ(mesh_file)
        print("OBJ mesh save to path:", mesh_file)
        
    def AddCharacter(self, c, create_obj = True):
        """
        Add a single char to mesh
        """
        self.face.load_char(c)
        if self.face.has_kerning:
            kerning = self.face.get_kerning(self.previous, c)
            self.offset += kerning.x

        # outline
        v = Vectoriser(self.face.glyph.outline, self.bezierSteps, reverse=False)
        for contour_index in range(len(v.contourList)):
            contour = v.contourList[contour_index]

            self.outlines.append([[e[0] + + self.offset, e[1]] for e in contour.pointList])

            if contour.clockwise:
                outer_contour_points = contour.pointList
                inner_contour_points_list = []
                for other_index in range(len(v.contourList)):
                    other_contour = v.contourList[other_index]
                    if (other_index != contour_index) and (not other_contour.clockwise) and \
                        other_contour.IsInside(contour):
                            inner_contour_points_list.append(other_contour.pointList)

                self.polygons.append(Polygon(outer_contour_points, inner_contour_points_list))
                        # x axis offset
                self.offsets.append(self.offset)

                if create_obj:
                    delauney = triangulate_contour(outer_contour_points, inner_contour_points_list)
                    
                    for i in range(len(delauney["triangles"])):
                        triangle_vertex_indices = delauney["triangles"][i]
                        triangular_vertices = [delauney["vertices"][j] for j in triangle_vertex_indices]

                        v1, v2, v3 = Vertex(), Vertex(), Vertex()

                        v1.x = triangular_vertices[0][0] + self.offset
                        v1.y = triangular_vertices[0][1]
                        v1.z = -self.bevelRadius

                        v2.x = triangular_vertices[1][0] + self.offset
                        v2.y = triangular_vertices[1][1]
                        v2.z = -self.bevelRadius

                        v3.x = triangular_vertices[2][0] + self.offset
                        v3.y = triangular_vertices[2][1]
                        v3.z = -self.bevelRadius
                        
                        self.mesh.addTriangle(v1, v2, v3)
                        
                        v1, v2, v3 = Vertex(), Vertex(), Vertex()
                        
                        v1.x = triangular_vertices[0][0] + self.offset
                        v1.y = triangular_vertices[0][1]
                        v1.z = self.bevelRadius + self.extrude

                        v2.x = triangular_vertices[1][0] + self.offset
                        v2.y = triangular_vertices[1][1]
                        v2.z = self.bevelRadius + self.extrude

                        v3.x = triangular_vertices[2][0] + self.offset
                        v3.y = triangular_vertices[2][1]
                        v3.z = self.bevelRadius + self.extrude
                        
                        self.mesh.addTriangle(v3, v2, v1) # pay attention to the order

        if create_obj:
            # bridge 
            v = Vectoriser(self.face.glyph.outline, self.bezierSteps, reverse=False)
            for contour in v.contourList:
                for j in range(len(contour.pointList)):
                    p1 = contour.pointList[j]
                    p2 = contour.pointList[(j + 1) % len(contour.pointList)]
                    # p1 /= 64
                    # p2 /= 64

                    v1, v2, v3 = Vertex(), Vertex(), Vertex()

                    v1.x = p1[0]+ self.offset
                    v1.y = p1[1]
                    v1.z = 0.0
                    v2.x = p2[0] + self.offset
                    v2.y = p2[1]
                    v2.z = 0.0
                    v3.x = p1[0]+ self.offset
                    v3.y = p1[1]
                    v3.z = self.extrude
                    self.mesh.addTriangle(v1, v2, v3)

                    v1, v2, v3 = Vertex(), Vertex(), Vertex()
                    v1.x = p1[0] + self.offset
                    v1.y = p1[1]
                    v1.z = self.extrude
                    v2.x = p2[0] + self.offset
                    v2.y = p2[1]
                    v2.z = 0.0
                    v3.x = p2[0] + self.offset
                    v3.y = p2[1]
                    v3.z = self.extrude
                    self.mesh.addTriangle(v1, v2, v3)
                
        
        self.previous = c
        self.offset += self.face.glyph.advance.x 

    ######################################## utils ########################################
    def getOutlinePoints(self, max_step:float = 30):
        """
        Get outlines (list of points) for the mesh
        """
        return intepolate_outline(self.outlines, max_step=max_step)

    def getGridPointsInside(self, grid_size = 10):
        """
        Generate grid points insides the mesh polygons
        """
        
        point_list = []
        for i, polygon in enumerate(self.polygons):
            points = grid_points_inside_polygon(polygon, grid_size)
            point_list += [[p[0] + self.offsets[i], p[1]] for p in points]

        return point_list
        




