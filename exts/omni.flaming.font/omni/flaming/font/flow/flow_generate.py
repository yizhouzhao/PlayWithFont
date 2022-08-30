import omni
import carb
from pxr import Sdf, Gf, UsdGeom

from .param import FIRE_CONFIG

class FlowGenerator():
    def __init__(self, flow_type = "Fire", layer = 1) -> None:
        self.emitter_positions = []
        self.flow_type = flow_type
        self.layer = layer

        # stage
        self.stage = omni.usd.get_context().get_stage()

        if self.flow_type == "Fire":
            self.flow_config = FIRE_CONFIG

        self._enable_flowusd_api()

    def _enable_flowusd_api(self, target_blocks = 32768):
        """
        Enable omni.flowusd api and settings
        """
        manager = omni.kit.app.get_app().get_extension_manager()
        self._api_was_enabled = manager.is_extension_enabled("omni.flowusd")
        if not self._api_was_enabled:
            manager.set_extension_enabled_immediate("omni.flowusd", True)

        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/enabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/rayTracedReflectionsEnabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/rayTracedTranslucencyEnabled", value=True)
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/pathTracingEnabled", value=True)

        max_blocks = carb.settings.get_settings().get("rtx/flow/maxBlocks")
        # target_blocks = 262144
        if max_blocks < target_blocks:
            omni.kit.commands.execute("ChangeSetting", path="rtx/flow/maxBlocks", value=target_blocks)

    def setEmitterPositions(self, points, scale = 10):
        """
        Add emitter postioins
        ::params: 
            points: list of (x, y)
        """ 
        self.emitter_positions = [[p[0] / scale, p[1] / scale] for p in points] 
    
    def generateFireAtPoint(self, point, flow_path_str = "/World/Xform", radius = 10.0, emitter_only = False):
        """
        Generate fire at point with size
        """
        
        # create xform at point
        
        flow_xform = UsdGeom.Xform.Define(self.stage, flow_path_str)
        flow_xform_api = UsdGeom.XformCommonAPI(flow_xform)
        flow_xform_api.SetTranslate(translation=Gf.Vec3d(point[0], point[1], point[2]))

        # flow_prim = self.stage.GetPrimAtPath(flow_path_str)
        # if not flow_prim.IsValid():
        #     omni.kit.commands.execute(
        #                 "CreatePrim",
        #                 prim_path=flow_path_str,
        #                 prim_type="Xform", # Xform
        #                 select_new_prim=False,
        #             )

        #     flow_prim = self.stage.GetPrimAtPath(flow_path_str)
        
        # flow_prim.GetAttribute("xformOp:translate").Set((point[0], point[1], point[2]))

        # create flow
        path = flow_path_str
      
        # create flow with emitter
        if not emitter_only:
            flowSimulate_prim_path = omni.usd.get_stage_next_free_path(self.stage, path + "/flowSimulate", False)
            flowOffscreen_prim_path = omni.usd.get_stage_next_free_path(self.stage, path + "/flowOffscreen", False)
            flowRender_prim_path = omni.usd.get_stage_next_free_path(self.stage, path + "/flowRender", False)

            buoyancyPerTemp = self.flow_config["buoyancyPerTemp"]
            forceScale = self.flow_config["forceScale"]
            successful, (emitter, simulate, offscreen, renderer, advection) = omni.kit.commands.execute("FlowCreateBasicEffect", path=path, layer=self.layer)
            # print("successful", successful, emitter.GetPath().pathString)

            smoke = self.stage.DefinePrim(flowSimulate_prim_path + "/advection/smoke", "FlowAdvectionChannelParams")
            vorticity = self.stage.DefinePrim(flowSimulate_prim_path + "/vorticity", "FlowVorticityParams")
            
            colormap = self.stage.DefinePrim(flowOffscreen_prim_path + "/colormap", "FlowRayMarchColormapParams")

            if colormap:
                rgbaPoints = []
                rgbaPoints.append(Gf.Vec4f(0.0154, 0.0177, 0.0154, 0.004902))
                rgbaPoints.append(Gf.Vec4f(0.03575, 0.03575, 0.03575, 0.504902))
                rgbaPoints.append(Gf.Vec4f(0.03575, 0.03575, 0.03575, 0.504902))
                rgbaPoints.append(Gf.Vec4f(1, 0.1594, 0.0134, 0.8))
                rgbaPoints.append(Gf.Vec4f(13.53, 2.99, 0.12599, 0.8))
                rgbaPoints.append(Gf.Vec4f(78, 39, 6.1, 0.7))
                colormap.CreateAttribute("rgbaPoints", Sdf.ValueTypeNames.Float4Array, False).Set(rgbaPoints)

            advection.CreateAttribute("buoyancyPerTemp", Sdf.ValueTypeNames.Float, False).Set(buoyancyPerTemp)
            smoke.CreateAttribute("fade", Sdf.ValueTypeNames.Float, False).Set(2.0)
            vorticity.CreateAttribute("forceScale", Sdf.ValueTypeNames.Float, False).Set(forceScale)

        else:  # emitter_only == True
            flowEmitterSphere_prim_path = omni.usd.get_stage_next_free_path(self.stage, path + "/flowEmitterSphere", False)
            
            emitter = self.stage.DefinePrim(flowEmitterSphere_prim_path, "FlowEmitterSphere")
            # success, emitter = omni.kit.commands.execute("FlowCreatePrim", prim_path=flowEmitterSphere_prim_path, type_name="FlowEmitterSphere")
            emitter.CreateAttribute("layer", Sdf.ValueTypeNames.Int, False).Set(self.layer)

        # common property change
        emitter.CreateAttribute("temperature", Sdf.ValueTypeNames.Float, False).Set(2.0)
        emitter.CreateAttribute("coupleRateTemperature", Sdf.ValueTypeNames.Float, False).Set(10.0)
        emitter.CreateAttribute("velocity", Sdf.ValueTypeNames.Float3, False).Set(Gf.Vec3f(*self.flow_config["velocity"]))
    

        ###### flaming font ####################
        emitter.CreateAttribute("radius", Sdf.ValueTypeNames.Float, False).Set(radius)


    def shutdown(self):
        """
        Destructor
        """
        self.emitter_positions = None