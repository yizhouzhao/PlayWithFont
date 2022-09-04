import os
import time
import asyncio

#　omni import 
import omni
import omni.ext
import omni.ui as ui
from omni.physx.scripts import physicsUtils

import carb

# usd import
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdPhysics, PhysxSchema, UsdShade





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
from .param import EXTENSION_ROOT, FONT_TYPES 
from .font.font_create import MeshGenerator
from .flow.flow_generate import FlowGenerator
from .fluid.fluid_generate import FluidGenerator
from .formable.deformable_generate import DeformableBodyGenerator


################################# flaming font ui #######################################
from  .ui.style import julia_modeler_style
from .ui.custom_ui_widget import *
from .ui.custom_color_widget import CustomColorWidget

from omni.kit.window.popup_dialog import MessageDialog

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
        self.mesh_generator: MeshGenerator = None
        self.mesh_generator_cache = {}

        self.flow_type = "Fire"
        self.flow_generator = None

        self.fluid_generator = None

        # stage
        self.stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.y)
        
        # build windows
        self.build_setup_layout_window()

    def build_setup_layout_window(self):
        # window
        
        self._window = ui.Window("omni.flaming.font", width=300)
        with self._window.frame:
            self._window.frame.style = julia_modeler_style
            with ui.ScrollingFrame():
                with ui.VStack(height=0):
                    # ui.Button("Debug", clicked_fn = self.debug)
                    with ui.CollapsableFrame("CREATE FONT"):
                        with ui.VStack(height=0, spacing=4):
                            ui.Line(style_type_name_override="HeaderLine")
                            ui.Spacer(height = 2)
                            
                            self.input_text_ui = CustomStringField("Input text:") 
                            self.font_type_ui = CustomComboboxWidget(label="Font type:", options=FONT_TYPES)
                            self.font_height_ui = CustomSliderWidget(min=10, max=100, label="Font size:", default_val=52,
                                tooltip = "Font 3D text model size.")
                            self.font_extrude_ui = CustomSliderWidget(min=100, max=1000, label="Font extrude:", default_val=768, 
                                tooltip = "Extrude value for 3D model.")
                            # self.font_bezier_ui = CustomSliderWidget(min=1, max=4, label="Bezier step:", default_val=3, 
                            #     tooltip = "Bezier step to make the font model, heigher value gets smoother contours.")
                           
                            ui.Button("Generate 3D Text", height = 40, name = "load_button", clicked_fn=self.generateFont)
                    
                    with ui.CollapsableFrame("EFFECT"):
                        with ui.VStack(height=0, spacing=4):
                            ui.Line(style_type_name_override="HeaderLine")
                            ui.Spacer(height = 2)

                            with ui.CollapsableFrame("FLOW"):
                                with ui.VStack(height=0, spacing=4):
                                    ui.Line(style_type_name_override="HeaderLine")
                                    ui.Spacer(height = 2)
                            
                                    
                                    CustomFlowSelectionGroup(on_select_fn = self.set_flow_type)
                                    self.flow_density_ui = CustomSliderWidget(min=0.01, max=0.99, num_type = "float", label="Flow density:", default_val=0.2, 
                                        tooltip = "Flow emitter density")
                             
                                    self.flow_radius_ui = CustomSliderWidget(min=1.0, max=10, num_type = "float", label="Flow radius:", default_val=5.0, 
                                        tooltip = "Flow emitter size.")
                                    self.flow_coolingrate_ui = CustomSliderWidget(min=0.0, max=2.0, num_type = "float", label="Cooling rate:", default_val=1.5, 
                                        tooltip = "Advection cooling rate.")
                      
                                    ui.Button("Generate Flow", clicked_fn=self.generateFlow, height = 40, 
                                        style = {"background_color": "sienna"}, name = "load_button",)

                            
                            with ui.CollapsableFrame("FLUID"):
                                with ui.VStack(height=0, spacing=4):
                                    ui.Line(style_type_name_override="HeaderLine")
                                    ui.Spacer(height = 2)

                                    self.fluid_offset_ui = CustomSliderWidget(min=10, max=100, label="Particle offset:", default_val=40,
                                        tooltip = "Fluid particle offset. Higher value results in lower density.")
                                    self.fluid_radius_ui = CustomSliderWidget(min=1, max=10, label="Particle radius:", default_val=5,
                                        tooltip = "Fluid particle size.")
                                    self.fluid_color_ui = CustomColorWidget(0.774, 0.94, 1.0, label="Ground color:")
                       

                                    ui.Button("Generate Fluid", clicked_fn=self.generateFluid, height = 40, 
                                        style = {"background_color": "darkslateblue"}, name = "load_button")
                  
                            with ui.CollapsableFrame("DEFORMABLE BODY"):
                                with ui.VStack(height=0, spacing=4):
                                    ui.Line(style_type_name_override="HeaderLine")
                                    ui.Spacer(height = 2)
                                    self.deformable_resolution_ui = CustomSliderWidget(min=5, max=20, label="Resolution:", default_val=15, 
                                            tooltip = "Resolution for the deformable body. Larger resolution results in more partitions.")
                                    ui.Button("Generate Deformable Body", height = 40, 
                                        style = {"background_color": "DarkSlateGray"}, name = "load_button", clicked_fn=self.generateDeformbable)
                            
                            # ui.Spacer(height = 20)
                            # ui.Button("Add 3D Model", clicked_fn=self.addFont3DModel)

                    with ui.CollapsableFrame("SCENE UTILITY"):
                        with ui.VStack(height=0, spacing=4):
                            ui.Line(style_type_name_override="HeaderLine")

                            # eco mode
                            CustomBoolWidget(label ="Eco mode:", default_value=False, tooltip = "Turn on/off eco mode in the render setting.", on_checked_fn = self.toggle_eco_mode)
                            # open a new stage
                            ui.Button("New scene", height = 40, name = "load_button", clicked_fn=self.new_scene, style={ "margin": 4}, tooltip = "open a new empty stage")
                            # ground plan
                            ui.Line(style={"color":"gray", "margin_height": 2, "margin_width": 20})
                            self.ground_color_ui = CustomColorWidget(0.86, 0.626, 0.273, label="Ground color:")
                            ui.Button("Add/Remove ground plane", height = 40, name = "load_button", clicked_fn=self.toggle_ground_plane, style={ "margin": 4}, tooltip = "Add or remove the ground plane")

                            self.gravity_mangitude_ui = CustomSliderWidget(min=0, max=1000, num_type = "int", label="Gravity magnitude:", default_val=981, 
                                        tooltip = "Gravity cm/s^2", on_slide_fn=self.set_up_physical_scene)
                            # light intensity
                            ui.Line(style={"color":"gray", "margin_height": 8, "margin_width": 20})
                            CustomSliderWidget(min=0, max=3000, label="Light intensity:", default_val=1000, on_slide_fn = self.change_light_intensity)

                    # PATH group
                    ui.Spacer(height = 10)
                    ui.Line(style_type_name_override="HeaderLine")
                    with ui.CollapsableFrame("PATH", collapsed = True):
                        with ui.VStack(height=0, spacing=0):
                            ui.Line(style_type_name_override="HeaderLine") 
                            ui.Spacer(height = 12)

                            CustomPathButtonWidget(label="Font folder:", path=os.path.join(EXTENSION_ROOT, "fonts"))
                            CustomPathButtonWidget(label="Model folder:", path=os.path.join(EXTENSION_ROOT, "model"))
         
    ####################### scene utility #################################################

    def new_scene(self):
        """
        Start a new scene
        """
        # clear memory
        self.on_shutdown() 

        # new scene
        omni.kit.window.file.new()

        # ecologist.
        #     
    
    def toggle_eco_mode(self, eco_mode = True):
        """
        Turn on/off eco mode when rendering
        """
        omni.kit.commands.execute("ChangeSetting", path="/rtx/ecoMode/enabled", value=eco_mode)



    def toggle_ground_plane(self):
        """
        Add or remove ground plane 
        """
        stage = omni.usd.get_context().get_stage()
        ground_prim = stage.GetPrimAtPath("/World/groundPlane")
        if not ground_prim:
            # ground_colors = [float(s) for s in self.ground_color_ui.get_color_stringfield().split(",")]
            # ground_color_vec = Gf.Vec3f(*ground_colors)
            physicsUtils.add_ground_plane(stage, "/World/groundPlane", "Y", 1000, Gf.Vec3f(0.0), Gf.Vec3f(0.3))
            self.change_ground_color()
            
            # select ground
            selection = omni.usd.get_context().get_selection()
            selection.clear_selected_prim_paths()
            selection.set_prim_path_selected("/World/groundPlane", True, True, True, True)
        else:
            omni.kit.commands.execute("DeletePrims", paths=["/World/groundPlane"])

    def change_ground_color(self):
        """
        Change ground color from color ui
        """
        entityPlane = UsdGeom.Mesh.Get(omni.usd.get_context().get_stage(), "/World/groundPlane/CollisionMesh")
        ground_colors = [float(s) for s in self.ground_color_ui.get_color_stringfield().split(",")]
        ground_color_vec = Gf.Vec3f(*ground_colors)
        entityPlane.CreateDisplayColorAttr().Set([ground_color_vec])

    def change_light_intensity(self, intensity:float = 1000):
        """
        Change light intensity
        """
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


    def on_shutdown(self):
        print("[omni.flaming.font] omni.flaming.font clear memory")

        if self.fluid_generator:
            self.fluid_generator.shutdown()
        
        if self.flow_generator:
            self.flow_generator.shutdown()
        
        # if self.mesh_generator: 
        #     self.mesh_generator.shutdown() 

        for key, mg in self.mesh_generator_cache.items():
            mg.shutdown()

        # del self.mesh_generator_cache
        self.mesh_generator = None

    def generateFont(self):
        """
        Generate 3D Text from input
        """

        task_index = self.font_type_ui.model.get_item_value_model().get_value_as_int()
        task_type = FONT_TYPES[task_index]
        font_file = os.path.join(EXTENSION_ROOT, 'fonts', task_type)
        font_height = self.font_height_ui.model.get_value_as_int()
        font_extrude = self.font_extrude_ui.model.get_value_as_int()

        input_text = self.input_text_ui.model.get_value_as_string()

        mesh_file = os.path.join(EXTENSION_ROOT, "model", f"{input_text}.obj")
        self.mesh_generator = MeshGenerator(font_file, height = font_height, text = input_text, extrude=-font_extrude) 
        self.mesh_generator.generateMesh(create_obj = True)
        self.mesh_generator.saveMesh(mesh_file)

        # load 3d model into the scene
        self.addFont3DModel()

        # add information to cache
        self.mesh_generator_cache[input_text] = self.mesh_generator


    def addFont3DModel(self, scale = 10):
        """
        Load font 3d model into scene
        """
        

        self.stage = omni.usd.get_context().get_stage()

        input_text = self.input_text_ui.model.get_value_as_string()

        font_prim_path =  omni.usd.get_stage_next_free_path(self.stage, "/World/font3d", False)
        font_prim = self.stage.GetPrimAtPath(font_prim_path)
        if not font_prim.IsValid():
            successful, font_prim = omni.kit.commands.execute(
                "CreatePrimWithDefaultXform",
                prim_path=font_prim_path,
                prim_type="Xform",
                select_new_prim=True,
                create_default_xform=False,
            )
            font_prim = self.stage.GetPrimAtPath(font_prim_path)

        font_model_path = os.path.join(EXTENSION_ROOT, "model", f"{input_text}.obj")
        success_bool = font_prim.GetReferences().AddReference(font_model_path)

        font_prim.GetAttribute("xformOp:scale").Set((scale, scale,  scale))

        # add attribute
        font_prim.CreateAttribute("font:input_text",  Sdf.ValueTypeNames.String, False).Set(input_text)

    
    def generateFlow(self):
        """
        Generate Flow for 3D text
        """

        stage = omni.usd.get_context().get_stage()

        # select the correct font prim
        font_prim = self.findFontPrim4Selection()
        input_text = font_prim.GetAttribute("font:input_text").Get()
        font_prim_path_str = font_prim.GetPath().pathString

        # mesh generator
        self.mesh_generator = self.mesh_generator_cache[input_text]

        # flow generator
        # if not self.flow_generator:
        self.flow_generator = FlowGenerator()
        
        # set flow type
        self.flow_generator.set_flow_type(self.flow_type)

        # load flow property
        flow_radius = self.flow_radius_ui.model.get_value_as_float()
        flow_coolingrate = self.flow_coolingrate_ui.model.get_value_as_float()
        flow_density =  self.flow_density_ui.model.get_value_as_float()
        sample_gap = int(1 / flow_density)
        # flow_outline_step = self.font_height_ui.model.get_value_as_int()
        
        all_points, is_outline = self.mesh_generator.getOutlinePoints(max_step=50)
        self.flow_generator.setEmitterPositions(all_points)
        # print("outlinePoints", len(self.flow_generator.emitter_positions), self.flow_generator.emitter_positions[0])


        # create xform as root
        flow_prim_path_str = omni.usd.get_stage_next_free_path(stage, f"{font_prim_path_str}_Flow", False)

        omni.kit.commands.execute(
                    "CreatePrim",
                    prim_path=flow_prim_path_str,
                    prim_type="Xform", # Xform
                    select_new_prim=False,
                ) 

        # generate emitters
        has_emitter = False
        sample_step = sample_gap

        
        begin = time.time()
        for i in range(len(self.flow_generator.emitter_positions)):
            if is_outline[i] or sample_step == 0: # is_outline[i] or 
                pos = self.flow_generator.emitter_positions[i] 
                self.flow_generator.generateFlowAtPoint(pos + [0.0], flow_path_str = f"{flow_prim_path_str}/Xform_{i}", \
                    radius = flow_radius, coolingRate=flow_coolingrate, emitter_only=has_emitter)
                has_emitter = True

                sample_step = sample_gap
            else:
                sample_step -= 1

        print("time elapse:", time.time() - begin)

        # move flow to the correct position
        mat = omni.usd.utils.get_world_transform_matrix(font_prim) 
        new_mat = Gf.Matrix4d().SetScale(1.0) * Gf.Matrix4d().SetRotate(mat.ExtractRotation()) * Gf.Matrix4d().SetTranslate(mat.ExtractTranslation())
        print("new_mat", new_mat)
        omni.kit.commands.execute(
            "TransformPrimCommand",
            path=flow_prim_path_str, 
            new_transform_matrix=new_mat,
        ) 

        # select prim
        selection = omni.usd.get_context().get_selection()
        selection.clear_selected_prim_paths()
        selection.set_prim_path_selected(flow_prim_path_str, True, True, True, True)

        # show notification
        dialog = MessageDialog(
            message=f"Fluid effect generated for {font_prim.GetPath().pathString} \n Click `Play` to show effect.",
            disable_cancel_button=True,
            ok_handler=lambda dialog: dialog.hide()
        )
        dialog.show()

    def generateFluid(self):
        """
        Generate fluid for 3D text
        """
        stage = omni.usd.get_context().get_stage()

        # select the correct font prim
        font_prim = self.findFontPrim4Selection()
        input_text = font_prim.GetAttribute("font:input_text").Get()
        font_prim_path_str = font_prim.GetPath().pathString

        # create xform as root
        fluid_prim_path_str = omni.usd.get_stage_next_free_path(stage, f"{font_prim_path_str}_Fluid", False)

        # omni.kit.commands.execute(
        #             "CreatePrim",
        #             prim_path=flow_prim_path_str,
        #             prim_type="Xform", # Xform
        #             select_new_prim=False,
        #         ) 

        # mesh generator
        self.mesh_generator = self.mesh_generator_cache[input_text]
        
        # property
        fluid_offset = self.fluid_offset_ui.model.get_value_as_int()
        fluid_radius = self.fluid_radius_ui.model.get_value_as_int()
        fluid_colors = [float(s) for s in self.fluid_color_ui.get_color_stringfield().split(",")]
        fluid_color_vec = Gf.Vec3f(*fluid_colors)

        grid_points = self.mesh_generator.getGridPointsInside(grid_size = fluid_offset)
        print("grid_points", len(grid_points), grid_points)

        self.fluid_generator = FluidGenerator(fluid_path_root=fluid_prim_path_str)
        self.fluid_generator.setPartclePositions(grid_points, radius=fluid_radius, color = fluid_color_vec)

        # physcial scene
        self.set_up_physical_scene()

        # move fluid to the correct position
        mat = omni.usd.utils.get_world_transform_matrix(font_prim) 
        new_mat = Gf.Matrix4d().SetScale(1.0) * Gf.Matrix4d().SetRotate(mat.ExtractRotation()) * Gf.Matrix4d().SetTranslate(mat.ExtractTranslation())
        print("new_mat", new_mat)
        omni.kit.commands.execute(
            "TransformPrimCommand",
            path=fluid_prim_path_str, 
            new_transform_matrix=new_mat,
        ) 

        # select prim
        selection = omni.usd.get_context().get_selection()
        selection.clear_selected_prim_paths()
        selection.set_prim_path_selected(fluid_prim_path_str, True, True, True, True)

        # show notification
        dialog = MessageDialog(
            message=f"Fluid effect generated for {font_prim.GetPath().pathString}",
            disable_cancel_button=True,
            ok_handler=lambda dialog: dialog.hide()
        )
        dialog.show()
    

    def generateDeformbable(self):
        """
        Generate deformable body for one mesh
        """

        # select the correct font prim
        font_prim = self.findFontPrim4Selection()
        input_text = font_prim.GetAttribute("font:input_text").Get()
        
        if len(input_text) > 1:
            dialog = MessageDialog(
                message=f"More than one char selected. \n This may cause unexpected results for deformable body. \n Please input one char at one time.",
                disable_cancel_button=True,
                ok_handler=lambda dialog: dialog.hide()
            )
            dialog.show()
            carb.log_error("More than one char may cause unexpected results for deformable body. Please input one char at one time.")
            return 

        self.stage = omni.usd.get_context().get_stage()
        self.deformable_generator = DeformableBodyGenerator()

        deformable_resolution = self.deformable_resolution_ui.model.get_value_as_int()
        self.deformable_generator.setDeformableBodyToPrim(font_prim, deformable_resolution)
        
        # show notification
        dialog = MessageDialog(
            message=f"Deformable body generated for {font_prim.GetPath().pathString}",
            disable_cancel_button=True,
            ok_handler=lambda dialog: dialog.hide()
        )
        dialog.show()
        

    ######################################## utils ######################################
    def findFontPrim4Selection(self):
        """
        Find the root font prim from selection
        """

        def build_error_dialog():
            dialog = MessageDialog(
                message=f"Please select only one font mesh.",
                disable_cancel_button=True,
                ok_handler=lambda dialog: dialog.hide()
            )
            dialog.show()

        self.stage = omni.usd.get_context().get_stage()
        font_prim = None

        selection = omni.usd.get_context().get_selection()
        if selection:
            paths = selection.get_selected_prim_paths()

            if len(paths) != 1:
                build_error_dialog()
                raise Exception("Please select only one font mesh.")

            prim = self.stage.GetPrimAtPath(paths[0])
            while prim.IsValid():
                if prim.HasAttribute("font:input_text"):
                    font_prim = prim 
                    break
                prim = prim.GetParent()
            
        else:
            build_error_dialog()
            raise Exception("Please select one font mesh.")

        if not font_prim:
            build_error_dialog()
            raise Exception("No 3D font selected.")

        return font_prim

    def set_flow_type(self, flow_type):
        """
        Set up flow type
        """
        self.flow_type = flow_type

    def set_up_physical_scene(self, gravityMagnitude = 981):
        # Physics scene
        # _gravityMagnitude = PARTICLE_PROPERTY._gravityMagnitude  # IN CM/s2 - use a lower gravity to avoid fluid compression at 60 FPS
        _gravityDirection = Gf.Vec3f(0.0, -1.0, 0.0)
        physicsScenePath = Sdf.Path("/World").AppendChild("physicsScene")
        if self.stage.GetPrimAtPath("/World/physicsScene"):
            scene = UsdPhysics.Scene.Get(self.stage, physicsScenePath)
        else:
            scene = UsdPhysics.Scene.Define(self.stage, physicsScenePath)
        scene.CreateGravityDirectionAttr().Set(_gravityDirection)
        scene.CreateGravityMagnitudeAttr().Set(gravityMagnitude)
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        # physxSceneAPI.CreateEnableCCDAttr().Set(True)
        # physxSceneAPI.GetTimeStepsPerSecondAttr().Set(60)
        # physxSceneAPI.CreateEnableGPUDynamicsAttr().Set(True)
        # physxSceneAPI.CreateEnableEnhancedDeterminismAttr().Set(True)
    

    ###################################### debug ######################################
    def debug(self):
        print("debug")
        # url = "FireEffect"
               # change color
        async def change_color(color):
            # omni.kit.commands.execute("FlowCreatePreset", path="/World/Flow", layer=1, menu_item=url)
            self.stage = omni.usd.get_context().get_stage()
            self.particle_material_path = "/World/Looks/OmniSurface_DeepWater"
                        
            await omni.kit.app.get_app().next_update_async()

            omni.kit.commands.execute('ChangeProperty',
            prop_path=Sdf.Path("/World/Looks/OmniSurface_DeepWater/Shader" + ".inputs:specular_transmission_color"),
            value=color,
            prev=Gf.Vec3f(1.0, 1.0, 1.0),
            )

            print("changing color..............")

            await omni.kit.app.get_app().next_update_async()
        
        asyncio.ensure_future(change_color(Gf.Vec3f(1,0,0)))
