import omni
import omni.ext
import omni.ui as ui

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
                ui.Button("Debug", clicked_fn=self.debug)

    def on_shutdown(self):
        print("[omni.flaming.font] omni.flaming.font shutdown")

    
    def debug(self):
        print("clicked!")

        from .font.font_create import MeshGenerator
        self.mg = MeshGenerator('font/fonts/LXGWClearGothic-Book.ttf', height = 48, text = "卡", extrude=768) # 尔直播
        self.mg.generateMesh(mesh_file = "test2.obj")
        print("mesh generated")


# main
print("hello")