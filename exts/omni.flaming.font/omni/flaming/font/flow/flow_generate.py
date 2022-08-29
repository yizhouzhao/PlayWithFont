import omni
from pxr import Sdf, Gf, UsdGeom

from .param import FIRE_CONFIG

class FlowGenerator():
    def __init__(self, flow_type = "Fire") -> None:
        self.emitter_positions = []
        self.flow_type = flow_type

        if self.flow_type == "Fire":
            self.flow_config = FIRE_CONFIG

        self._enable_flowusd_api()

    def _enable_flowusd_api(self):
        manager = omni.kit.app.get_app().get_extension_manager()
        self._api_was_enabled = manager.is_extension_enabled("omni.flowusd")
        if not self._api_was_enabled:
            manager.set_extension_enabled_immediate("omni.flowusd", True)

        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/enabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/rayTracedReflectionsEnabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/rayTracedTranslucencyEnabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/pathTracingEnabled", value=True)


    def setEmitterPositions(self, points):
        """
        Add emitter postioins
        ::params: 
            points: list of (x, y, z)
        """ 
        self.emitter_positions = points
    
    def generateFireAtPoint(self, point, flow_path_str = "/World/Xform", radius = 10.0, emitter_only = False):
        """
        Generate fire at point with size
        """
        
        self.stage = omni.usd.get_context().get_stage()
        flow_prim = self.stage.GetPrimAtPath(flow_path_str)
        if not flow_prim.IsValid():
            flow_prim = omni.kit.commands.execute(
                        "CreatePrim",
                        prim_path=flow_path_str,
                        prim_type="Xform",
                        select_new_prim=False,
                    )
        

        # get constant
        vel_vec = Gf.Vec3f(*self.flow_config["velocity"])
        buoyancyPerTemp = self.flow_config["buoyancyPerTemp"]
        forceScale = self.flow_config["forceScale"]

        # omni.kit.commands.execute("FlowCreatePreset", path="/World/Xform", layer=1, menu_item="FireEffect", emitter_only=False)
        # omni.kit.commands.execute("FlowCreatePreset", path="/World/Xform_01", layer=1, menu_item="FireEffect", emitter_only=True)
    
        path = flow_path_str
        stage = omni.usd.get_context().get_stage()
        flowSimulate_prim_path = omni.usd.get_stage_next_free_path(stage, path + "/flowSimulate", False)
        flowOffscreen_prim_path = omni.usd.get_stage_next_free_path(stage, path + "/flowOffscreen", False)
        flowRender_prim_path = omni.usd.get_stage_next_free_path(stage, path + "/flowRender", False)

        successful, (emitter, simulate, offscreen, renderer, advection) = omni.kit.commands.execute("FlowCreateBasicEffect", path=path, layer=1)
        print("successful", successful, emitter.GetPath().pathString)

        _, smoke = omni.kit.commands.execute("FlowCreatePrim", prim_path=flowSimulate_prim_path + "/advection/smoke", type_name="FlowAdvectionChannelParams")
        _, vorticity = omni.kit.commands.execute("FlowCreatePrim", prim_path=flowSimulate_prim_path + "/vorticity", type_name="FlowVorticityParams")

        (success, colormap) = omni.kit.commands.execute("FlowCreatePrim", prim_path=flowOffscreen_prim_path + "/colormap", type_name="FlowRayMarchColormapParams")


        if success and colormap:
            rgbaPoints = []
            rgbaPoints.append(Gf.Vec4f(0.0154, 0.0177, 0.0154, 0.004902))
            rgbaPoints.append(Gf.Vec4f(0.03575, 0.03575, 0.03575, 0.504902))
            rgbaPoints.append(Gf.Vec4f(0.03575, 0.03575, 0.03575, 0.504902))
            rgbaPoints.append(Gf.Vec4f(1, 0.1594, 0.0134, 0.8))
            rgbaPoints.append(Gf.Vec4f(13.53, 2.99, 0.12599, 0.8))
            rgbaPoints.append(Gf.Vec4f(78, 39, 6.1, 0.7))
            colormap.CreateAttribute("rgbaPoints", Sdf.ValueTypeNames.Float4Array, False).Set(rgbaPoints)

        
        emitter.CreateAttribute("temperature", Sdf.ValueTypeNames.Float, False).Set(2.0)
        emitter.CreateAttribute("coupleRateTemperature", Sdf.ValueTypeNames.Float, False).Set(10.0)
        emitter.CreateAttribute("velocity", Sdf.ValueTypeNames.Float3, False).Set(vel_vec)

        advection.CreateAttribute("buoyancyPerTemp", Sdf.ValueTypeNames.Float, False).Set(buoyancyPerTemp)

        smoke.CreateAttribute("fade", Sdf.ValueTypeNames.Float, False).Set(2.0)

        vorticity.CreateAttribute("forceScale", Sdf.ValueTypeNames.Float, False).Set(forceScale)

        if emitter_only:
            omni.kit.commands.execute("DeletePrims", paths=[flowSimulate_prim_path])
            omni.kit.commands.execute("DeletePrims", paths=[flowOffscreen_prim_path])
            omni.kit.commands.execute("DeletePrims", paths=[flowRender_prim_path])

        ###### flaming font ####################
        emitter.CreateAttribute("radius", Sdf.ValueTypeNames.Float, False).Set(radius)

