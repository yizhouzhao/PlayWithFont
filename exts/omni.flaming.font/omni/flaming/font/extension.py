import omni
import omni.ext
import omni.ui as ui
from pxr import Gf, Sdf

import os

try:
    import shapely
except:
    omni.kit.pipapi.install("shapely")
    import shapely
    
try:
    import freetype
except:
    omni.kit.pipapi.install("freetype-py")
    import freetype

try:
    import triangle
except:
    omni.kit.pipapi.install("triangle")
    import triangle


from .param import EXTENSION_ROOT 

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[omni.flaming.font] MyExtension startup")

        # enable flow in rendering
        omni.kit.commands.execute("ChangeSetting", path="rtx/flow/enabled", value=True)

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                ui.Label("Some Label")
                ui.Button("Generate Font Test", clicked_fn=self.generateFont)
                ui.Button("Generate Fire", clicked_fn=self.generateFire)

    def on_shutdown(self):
        print("[omni.flaming.font] omni.flaming.font shutdown")

    
    def generateFont(self):
        print("generateFont!")

        from .font.font_create import MeshGenerator
        font_file = os.path.join(EXTENSION_ROOT, 'fonts', 'LXGWClearGothic-Book.ttf')
    
        mesh_file = os.path.join(EXTENSION_ROOT, "temp", "test1.obj")
        self.mg = MeshGenerator(font_file, height = 48, text = "英伟达", extrude=768) 
        self.mg.generateMesh()
        self.mg.saveMesh(mesh_file)
        print("mesh generated")
    
    def generateFire(self):
        print("generate fire!")

        # constant
        vel_vec = Gf.Vec3f(10.0, 0.0, 0.0)
        buoyancyPerTemp =  6.0
        forceScale = 3.0

        # omni.kit.commands.execute("FlowCreatePreset", path="/World/Xform", layer=1, menu_item="FireEffect", emitter_only=False)
        # omni.kit.commands.execute("FlowCreatePreset", path="/World/Xform_01", layer=1, menu_item="FireEffect", emitter_only=True)
        



        path = "/World/Xform"
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

        emitter_only = True
        if emitter_only:
            omni.kit.commands.execute("DeletePrims", paths=[flowSimulate_prim_path])
            omni.kit.commands.execute("DeletePrims", paths=[flowOffscreen_prim_path])
            omni.kit.commands.execute("DeletePrims", paths=[flowRender_prim_path])

        ###### flaming font ####################
        emitter.CreateAttribute("radius", Sdf.ValueTypeNames.Float, False).Set(20.0)
# main
print("hello")