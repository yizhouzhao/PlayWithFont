# scene utilities
import omni
from omni.physx.scripts import utils, physicsUtils, deformableUtils

from pxr import Gf, UsdLux

def toggle_ground_plane(add_ground = True):
    stage = omni.usd.get_context().get_stage()
    ground_prim = stage.GetPrimAtPath("/World/groundPlane")
    if add_ground:
        if not ground_prim:
            physicsUtils.add_ground_plane(stage, "/World/groundPlane", "Y", 750.0, Gf.Vec3f(0.0), Gf.Vec3f(0.3))
    else:
        if ground_prim:
            omni.kit.commands.execute("DeletePrims", paths=["/World/groundPlane"])

 # light intensity
def change_light_intensity(intensity:float = 1000):
    stage = omni.usd.get_context().get_stage()
    light_prim = stage.GetPrimAtPath("/World/defaultLight")

    if not light_prim:
        # Create basic DistantLight
        omni.kit.commands.execute(
            "CreatePrim",
            prim_path="/World/defaultLight",
            prim_type="DistantLight",
            select_new_prim=False,
            attributes={UsdLux.Tokens.angle: 1.0, UsdLux.Tokens.intensity: 1000},
            create_default_xform=True,
        )

        light_prim = stage.GetPrimAtPath("/World/defaultLight")

    light_prim.GetAttribute("intensity").Set(float(intensity))

                        