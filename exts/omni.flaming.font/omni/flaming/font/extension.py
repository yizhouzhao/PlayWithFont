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
from .flow.flow_generate import FlowGenerator
from .fluid.fluid_generate import FluidGenerator

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
                ui.Button("Generate Fluid", clicked_fn=self.generateFluid)
                ui.Button("Add 3D Model", clicked_fn=self.addFont3DModel)
                

    def on_shutdown(self):
        print("[omni.flaming.font] omni.flaming.font shutdown")

    
    def generateFont(self):
        print("generateFont!")

        from .font.font_create import MeshGenerator
        font_file = os.path.join(EXTENSION_ROOT, 'fonts', 'LXGWClearGothic-Book.ttf')
    
        mesh_file = os.path.join(EXTENSION_ROOT, "temp", "test1.obj")
        self.mg = MeshGenerator(font_file, height = 48, text = "Hello", extrude=768) 
        self.mg.generateMesh(create_obj = False)
        # self.mg.saveMesh(mesh_file)
        
        print("mesh polygons", self.mg.offsets)
        print("mesh generated")

    def addFont3DModel(self, scale = 10):
        print("add font 3d model")
        # load robot
        self.stage = omni.usd.get_context().get_stage()
        font_prim = self.stage.GetPrimAtPath("/World/font3d")
        if not font_prim.IsValid():
            font_prim = self.stage.DefinePrim("/World/font3d")
        
        font_model_path = os.path.join(EXTENSION_ROOT, "temp", "test1.obj")
        print("add robot at path: ", font_model_path)
        success_bool = font_prim.GetReferences().AddReference(font_model_path)

        font_prim.GetAttribute("xformOp:scale").Set((scale, scale,  scale))
    
    def generateFire(self, sample_gap: int = 5):
        print("generate fire!")

        # constant
        self.flow_generator = FlowGenerator()

        all_points, is_outline = self.mg.getOutlinePoints(max_step=50)
        self.flow_generator.setEmitterPositions(all_points)
        print("outlinePoints", len(self.flow_generator.emitter_positions), self.flow_generator.emitter_positions[0])


        # create xform at point
        stage = omni.usd.get_context().get_stage()
        flow_prim = stage.GetPrimAtPath("/World/Flow")
        if not flow_prim.IsValid():
            omni.kit.commands.execute(
                        "CreatePrim",
                        prim_path="/World/Flow",
                        prim_type="Xform", # Xform
                        select_new_prim=False,
                    )

        has_emitter = False
        sample_step = sample_gap

        import time
        begin = time.time()
        for i in range(len(self.flow_generator.emitter_positions)):
            if is_outline[i] or sample_step == 0: # is_outline[i] or 
                pos = self.flow_generator.emitter_positions[i] 
                self.flow_generator.generateFireAtPoint(pos + [0.0], flow_path_str = f"/World/Flow/Xform_{i}", \
                    radius = 5.0, emitter_only=has_emitter)
                has_emitter = True

                sample_step = sample_gap
            else:
                sample_step -= 1

        print("time elapse:", time.time() - begin)

    def generateFluid(self):
        print("generateFluid")

        grid_points = self.mg.getGridPointsInside(grid_size = 10)
        print("grid_points", grid_points)

        self.fluid_generator = FluidGenerator()
        self.fluid_generator.setPartclePositions(grid_points)