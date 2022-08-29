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
                ui.Button("Add 3D Model", clicked_fn=self.addFont3DModel)
                

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

    def addFont3DModel(self):
        print("add font 3d model")
        # load robot
        self.stage = omni.usd.get_context().get_stage()
        font_prim = self.stage.GetPrimAtPath("/World/font3d")
        if not font_prim.IsValid():
            font_prim = self.stage.DefinePrim("/World/font3d")
        
        font_model_path = os.path.join(EXTENSION_ROOT, "temp", "test1.obj")
        print("add robot at path: ", font_model_path)
        success_bool = font_prim.GetReferences().AddReference(font_model_path)
    
    def generateFire(self):
        print("generate fire!")

        # constant
        self.fg = FlowGenerator()
        # self.fg.setEmitterPositions(self.mg.outlinePoints)
        # print("outlinePoints", self.mg.outlinePoints)
        self.fg.generateFireAtPoint([0, 0, 0])
