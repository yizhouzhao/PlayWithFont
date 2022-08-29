import omni
import carb
from pxr import Sdf, Gf, UsdGeom

class FluidGenerator():
    def __init__(self, flow_type = "Water", layer = 1) -> None:
        self.particle_positions = []
        self.flow_type = flow_type
        self.layer = layer

        # stage
        self.stage = omni.usd.get_context().get_stage()

    def setPartclePositions(self, points, scale = 10):
        self.particle_positions = [p + [0.0] for p in points]

        for i, point in enumerate(self.particle_positions):
            flow_prim = self.stage.GetPrimAtPath(f"/World/x{i}")
            if not flow_prim.IsValid():
                omni.kit.commands.execute(
                            "CreatePrim",
                            prim_path=f"/World/x{i}",
                            prim_type="Cube", # Xform
                            select_new_prim=False,
                        )

                flow_prim = self.stage.GetPrimAtPath(f"/World/x{i}")
            
            flow_prim.GetAttribute("xformOp:translate").Set((point[0] / scale, point[1] / scale, point[2] / scale))
