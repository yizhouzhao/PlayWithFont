import omni
import omni.ext
import omni.ui as ui
from pxr import Gf, Sdf

import os



################################ pip install dependencies ####################################
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

################################ flaming font import ####################################
from .param import EXTENSION_ROOT 
from .font.font_create import MeshGenerator
from .flow.flow_generate import FlowGenerator
from .fluid.fluid_generate import FluidGenerator
from .formable.deformable_generate import DeformableBodyGenerator

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

        # component
        self.mesh_generator = None
        self.flow_generator = None
        self.fluid_generator = None

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                self.input_text_ui = ui.StringField(height=20, style={ "margin_height": 2})
                self.input_text_ui.model.set_value("Los Ángeles")
                ui.Button("Generate Font Test", clicked_fn=self.generateFont)
                ui.Button("Generate Fire", clicked_fn=self.generateFire)
                ui.Button("Generate Fluid", clicked_fn=self.generateFluid)
                ui.Button("Generate Deformable Body", clicked_fn=self.generateDeformbable)
                ui.Spacer(height = 20)
                ui.Button("Add 3D Model", clicked_fn=self.addFont3DModel)
                
    def on_shutdown(self):
        print("[omni.flaming.font] omni.flaming.font shutdown")

        if self.fluid_generator:
            self.fluid_generator.shutdown()
        
        if self.flow_generator:
            self.flow_generator.shutdown()
        
        if self.mesh_generator:
            self.mesh_generator.shutdown()

    def generateFont(self):
        print("generateFont!")

        font_file = os.path.join(EXTENSION_ROOT, 'fonts', 'LXGWClearGothic-Book.ttf')
    
        input_text = self.input_text_ui.model.get_value_as_string()

        mesh_file = os.path.join(EXTENSION_ROOT, "temp", f"{input_text}.obj")
        self.mesh_generator = MeshGenerator(font_file, height = 48, text = input_text, extrude=768) 
        self.mesh_generator.generateMesh(create_obj = True)
        self.mesh_generator.saveMesh(mesh_file)
        
        print("mesh polygons", self.mesh_generator.offsets)
        print("mesh generated")

    def addFont3DModel(self, scale = 10):
        print("add font 3d model")

        self.stage = omni.usd.get_context().get_stage()

        input_text = self.input_text_ui.model.get_value_as_string()

        font_prim = self.stage.GetPrimAtPath(f"/World/font3d_{input_text}")
        if not font_prim.IsValid():
            font_prim = self.stage.DefinePrim(f"/World/font3d_{input_text}")
        
        font_model_path = os.path.join(EXTENSION_ROOT, "temp", f"{input_text}.obj")
        print("add robot at path: ", font_model_path)
        success_bool = font_prim.GetReferences().AddReference(font_model_path)

        font_prim.GetAttribute("xformOp:scale").Set((scale, scale,  scale))
    
    def generateFire(self, sample_gap: int = 5):
        print("generate fire!")

        # constant
        self.flow_generator = FlowGenerator()

        all_points, is_outline = self.mesh_generator.getOutlinePoints(max_step=50)
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

        grid_points = self.mesh_generator.getGridPointsInside(grid_size = 40)
        print("grid_points", len(grid_points), grid_points)

        self.fluid_generator = FluidGenerator()
        self.fluid_generator.setPartclePositions(grid_points, radius=3.0)

    def generateDeformbable(self):
        print("generateDeformbable")
        self.stage = omni.usd.get_context().get_stage()
        self.deformable_generator = DeformableBodyGenerator()

        selection = omni.usd.get_context().get_selection()
        if selection:
            paths = selection.get_selected_prim_paths()
            first_selected_prim = self.stage.GetPrimAtPath(paths[0])
            self.deformable_generator.setDeformableBodyToPrim(first_selected_prim)
