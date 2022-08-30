# deformable body
import omni
import carb

from pxr import Gf, UsdPhysics, Sdf, Usd, UsdGeom, PhysxSchema, Vt
from omni.physx.scripts import utils, physicsUtils, deformableUtils


class DeformableBodyGenerator():
    def __init__(self) -> None:

        # stage
        self.stage = omni.usd.get_context().get_stage()

    def setDeformableBodyToPrim(self, prim, simulation_resolution:int = 10):
        print("setDeformableBodyToPrim")

        # get all children
        def get_all_descendents(prim, output=[]):
            prim_children = prim.GetChildren()
            if prim_children:
                for child in prim_children:
                    output.append(child)
                    get_all_descendents(child, output)
            return output

        output = [prim]
        get_all_descendents(prim, output)

        # filter mesh
        mesh_prims = filter(lambda x: x.GetTypeName() == 'Mesh', output)

        # add deformable body to mesh
        for mesh in mesh_prims:
            print("mesh", mesh.GetPath())
            success = deformableUtils.add_physx_deformable_body(
                self.stage,
                mesh.GetPath(),
                collision_simplification=False,
                simulation_hexahedral_resolution=simulation_resolution,
                self_collision=False,
            )

            # Create a deformable body material and set it on the deformable body
            deformable_material_path = omni.usd.get_stage_next_free_path(self.stage, "/deformableBodyMaterial", True)
            deformableUtils.add_deformable_body_material(
                self.stage,
                deformable_material_path,
                youngs_modulus=10000.0,
                poissons_ratio=0.49,
                damping_scale=0.0,
                dynamic_friction=0.5,
            )
            physicsUtils.add_physics_material_to_prim(self.stage, mesh.GetPrim(), deformable_material_path)

            # Plane
            # physicsUtils.add_ground_plane(stage, "/groundPlane", "Z", 750.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))


            