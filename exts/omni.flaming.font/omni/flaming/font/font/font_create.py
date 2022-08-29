import numpy as np
from freetype import *

from .font_struct import *
from .font_util import *


class MeshGenerator():
    def __init__(self, fontFile, height:int, text:str, 
        bezierSteps = 4, extrude = 96, bevelRadius = 0, bevelSteps=4) -> None:
        self.fontFile = fontFile
        self.height = height
        self.text = text
        self.bezierSteps = bezierSteps
        self.extrude = extrude
        self.bevelRadius = bevelRadius
        self.bevelSteps = bevelSteps

    def generateMesh(self):
        # init font
        self.face = Face(self.fontFile)
        self.face.set_char_size(self.height << 6, self.height << 6, 96, 96)

        # init mesh
        self.mesh = Mesh()
        self.offset = 0

        self.previous = 0
        for c in self.text:
            self.AddCharacter(c)

    def saveMesh(self, mesh_file = "test0.obj"):
        self.mesh.saveOBJ(mesh_file)
        
    def AddCharacter(self, c):
        assert len(c) == 1, "Add character with one char only!"
        print("offset:", self.offset)
        self.face.load_char(c)
        if self.face.has_kerning:
            kerning = self.face.get_kerning(self.previous, c)
            self.offset += kerning.x

        v = Vectoriser(self.face.glyph.outline, self.bezierSteps, reverse=False)
        for contour_index in range(len(v.contourList)):
            contour = v.contourList[contour_index]

            if contour.clockwise:
                outer_contour_points = contour.pointList
                inner_contour_points_list = []
                for other_index in range(len(v.contourList)):
                    other_contour = v.contourList[other_index]
                    if (other_index != contour_index) and (not other_contour.clockwise) and \
                        other_contour.IsInside(contour):
                            inner_contour_points_list.append(other_contour.pointList)

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

        # # bevel steps
        # for i in range(self.bevelSteps):
        #     vectoriser1 = Vectoriser(self.face.glyph.outline, self.bezierSteps, reverse=False, size_factor = 1 + 0.1 * i)
        #     vectoriser2 = Vectoriser(self.face.glyph.outline, self.bezierSteps, reverse=False, size_factor = 1 + 0.1 * (i+1))
        #     # print("vectoriser12", len(vectoriser1.contourList))

        #     for contour_index in range(len(vectoriser1.contourList)):
        #         contour1 = vectoriser1.contourList[contour_index]
        #         contour2 = vectoriser2.contourList[contour_index]


        #         print("contour1.pointList", len(contour1.pointList))

        #         for j in range(len(contour1.pointList)):
        #             p1 = contour1.pointList[j]
        #             p2 = contour1.pointList[(j + 1) % len(contour1.pointList)]

        #             p3 = contour2.pointList[j]
        #             p4 = contour2.pointList[(j + 1) % len(contour2.pointList)]

        #             print("1234", p1, p2, p3, p4)

        #             bevelY = self.extrude + (self.bevelRadius * np.cos(np.pi * 0.5 * (i) / self.bezierSteps))
        #             nextBevelY =  self.extrude + (self.bevelRadius * np.cos(np.pi * 0.5 * (i+1) / self.bezierSteps))

        #             v1, v2, v3 = Vertex(), Vertex(), Vertex()

        #             v1.x = p1[0]+ self.offset
        #             v1.y = p1[1]
        #             v1.z = bevelY
        #             v2.x = p3[0] + self.offset
        #             v2.y = p3[1]
        #             v2.z = nextBevelY
        #             v3.x = p2[0]+ self.offset
        #             v3.y = p2[1]
        #             v3.z = bevelY
        #             self.mesh.addTriangle(v1, v2, v3)

        #             v1, v2, v3 = Vertex(), Vertex(), Vertex()

        #             v1.x = p3[0]+ self.offset
        #             v1.y = p3[1]
        #             v1.z = nextBevelY
        #             v2.x = p4[0] + self.offset
        #             v2.y = p4[1]
        #             v2.z = nextBevelY
        #             v3.x = p2[0]+ self.offset
        #             v3.y = p2[1]
        #             v3.z = bevelY
        #             self.mesh.addTriangle(v1, v2, v3)

        #             eBevelY = -(self.bevelRadius * np.cos(np.pi * 0.5 * (i) / self.bezierSteps))
        #             eNextBevelY = -(self.bevelRadius * np.cos(np.pi * 0.5 * (i+1) / self.bezierSteps))

        #             v1, v2, v3 = Vertex(), Vertex(), Vertex()

        #             v1.x = p1[0]+ self.offset
        #             v1.y = p1[1]
        #             v1.z = eBevelY
        #             v2.x = p2[0] + self.offset
        #             v2.y = p2[1]
        #             v2.z = eBevelY
        #             v3.x = p3[0]+ self.offset
        #             v3.y = p3[1]
        #             v3.z = eNextBevelY
        #             self.mesh.addTriangle(v1, v2, v3)

        #             v1, v2, v3 = Vertex(), Vertex(), Vertex()

        #             v1.x = p3[0]+ self.offset
        #             v1.y = p3[1]
        #             v1.z = eNextBevelY
        #             v2.x = p2[0] + self.offset
        #             v2.y = p2[1]
        #             v2.z = eBevelY
        #             v3.x = p4[0]+ self.offset
        #             v3.y = p4[1]
        #             v3.z = eNextBevelY
        #             self.mesh.addTriangle(v1, v2, v3)

        

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




