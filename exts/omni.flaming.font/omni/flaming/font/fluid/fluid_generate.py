import omni
import carb
import asyncio

from pxr import Gf, UsdPhysics, Sdf, Usd, UsdGeom, PhysxSchema, Vt, UsdShade
from omni.physx.scripts import utils, physicsUtils, particleUtils

from .param import PARTICLE_PROPERTY

class FluidGenerator():
    def __init__(self, fluid_path_root = "/World/fluid3d", flow_type = "Water", layer = 1) -> None:
        self.particle_positions = []
        self.flow_type = flow_type
        self.layer = layer
        self.fluid_path_root = fluid_path_root

        # stage
        PARTICLE_PROPERTY.set_partical_properties()

        # gpu
        self.enable_gpu()

    def enable_gpu(self):
        
        from omni.physx import  acquire_physx_interface
        physx = acquire_physx_interface()
        physx.overwrite_gpu_setting(1)
        physx.reset_simulation()




    def setPartclePositions(self, points, scale = 10, radius = 3.0, max_velocity = 50.0, color = Gf.Vec3f(1.0,0,0)):
        """
        Add particles at points
        """
        # stage
        self.stage = omni.usd.get_context().get_stage()

        self.particle_positions = [[p[0] / scale, p[1] / scale, 0] for p in points]

        # for i, point in enumerate(self.particle_positions):
        #     flow_prim = self.stage.GetPrimAtPath(f"/World/x{i}")
        #     if not flow_prim.IsValid():
        #         omni.kit.commands.execute(
        #                     "CreatePrim",
        #                     prim_path=f"/World/x{i}",
        #                     prim_type="Xform", # Xform
        #                     select_new_prim=False,
        #                 )

        #         flow_prim = self.stage.GetPrimAtPath(f"/World/x{i}")
            
        #     flow_prim.GetAttribute("xformOp:translate").Set((point[0] / scale, point[1] / scale, point[2] / scale))
        
        # fluid physical scene
        self.set_up_fluid_physical_scene() 

        # fluid root
        particleSystemStr = omni.usd.get_stage_next_free_path(self.stage, "/World/Fluid", False) # game_prim.GetPath().AppendPath("Fluid").pathString
        self.particleSystemPath = Sdf.Path(particleSystemStr)
        self.particleInstanceStr = f"{self.fluid_path_root}" # game_prim.GetPath().AppendPath("Particles").pathString

        # particle system
        self._fluidSphereDiameter = PARTICLE_PROPERTY._fluidSphereDiameter
        self._particleSystemSchemaParameters = PARTICLE_PROPERTY._particleSystemSchemaParameters
        self._particleSystemAttributes = PARTICLE_PROPERTY._particleSystemAttributes

        if not self.stage.GetPrimAtPath(self.particleSystemPath):
            self._particleSystem = particleUtils.add_physx_particle_system(
                    self.stage, self.particleSystemPath, **self._particleSystemSchemaParameters, simulation_owner=Sdf.Path(self.physicsScenePath.pathString)
                )
        else:
            self._particleSystem = PhysxSchema.PhysxParticleSystem.Get(self.stage, self.particleSystemPath)
        

        particleInstancePath = Sdf.Path(self.particleInstanceStr)
        # paricle instance
        positions_list = [Gf.Vec3f(*p) for p in self.particle_positions]
        velocities_list = [Gf.Vec3f(0, 0, 0) for _ in range(len(self.particle_positions))]
        protoIndices_list = [0 for _ in range(len(self.particle_positions))]

        positions = Vt.Vec3fArray(positions_list)
        velocities = Vt.Vec3fArray(velocities_list)
        
        particleUtils.add_physx_particleset_pointinstancer(
            stage=self.stage,
            path= particleInstancePath, # 
            positions=Vt.Vec3fArray(positions),
            velocities=Vt.Vec3fArray(velocities),
            particle_system_path=self.particleSystemPath,
            self_collision=True,
            fluid=True,
            particle_group=0,
            particle_mass=PARTICLE_PROPERTY._particle_mass,
            density=0.0,
            num_prototypes = 1,
        )

        ################### flaming font custom #######################################################
        particlePrototype0_sphere = UsdGeom.Sphere.Get(self.stage, Sdf.Path(particleInstancePath.pathString + "/particlePrototype0"))
        
        sphere_extent_attr = particlePrototype0_sphere.GetExtentAttr().Get()
        particlePrototype0_sphere.CreateExtentAttr([(i * radius for i in e) for e in sphere_extent_attr])

        particlePrototype0_sphere.CreateRadiusAttr(radius)

        # debug
        # print("sphere_extent_attr", sphere_extent_attr)
        # print("positions_list", len(positions_list), positions_list[:5])

        # enable isosurface
        self.enable_isosurface(max_velocity=max_velocity, color = color)

    def set_up_fluid_physical_scene(self):
        """
        Fluid / PhysicsScene
        """
        default_prim_path = self.stage.GetDefaultPrim().GetPath()
        if default_prim_path.pathString == '':
            # default_prim_path = pxr.Sdf.Path('/World')
            root = UsdGeom.Xform.Define(self.stage, "/World").GetPrim()
            self.stage.SetDefaultPrim(root)
            default_prim_path = self.stage.GetDefaultPrim().GetPath()

        # if self.stage.GetPrimAtPath("/World/physicsScene"):
        #     self.physicsScenePath = default_prim_path.AppendChild("physicsScene")
        #     return

        particleSystemStr = default_prim_path.AppendPath("Fluid").pathString
        self.physicsScenePath = default_prim_path.AppendChild("physicsScene")
        self.particleSystemPath = Sdf.Path(particleSystemStr)
        self.particleInstanceStr = default_prim_path.AppendPath("Particles").pathString
        
        return 


    def enable_isosurface(self, max_velocity = 50.0, color = Gf.Vec3f(1.0, 0.0, 0.0)):
        async def enable_isosurface_async():
            print("isosurface settings")
            particle_system = self._particleSystem
            
            mtl_created = []
            omni.kit.commands.execute(
                "CreateAndBindMdlMaterialFromLibrary",
                mdl_name="OmniSurfacePresets.mdl",
                mtl_name="OmniSurface_DeepWater",
                mtl_created_list=mtl_created,
                select_new_prim=False,
            )

            self.particle_material_path = mtl_created[0]
            await omni.kit.app.get_app().next_update_async()
            selection = omni.usd.get_context().get_selection()
            selection.set_selected_prim_paths([f"{self.particle_material_path}/Shader"], False)
            await omni.kit.app.get_app().next_update_async()
    

            omni.kit.commands.execute('ChangeProperty',
                prop_path=Sdf.Path(f'{self.particle_material_path}/Shader.inputs:specular_transmission_color'),
                value=color,
                prev=Gf.Vec3f(1.0, 1.0, 1.0)
                )

            await omni.kit.app.get_app().next_update_async()

            omni.kit.commands.execute('ChangeProperty',
                prop_path=Sdf.Path(f'{self.particle_material_path}/Shader.inputs:specular_transmission_scattering_color'),
                value=color / 1.5,
                prev=Gf.Vec3f(1.0, 1.0, 1.0)
                )

            await omni.kit.app.get_app().next_update_async()

            
            omni.kit.commands.execute(
                "BindMaterial", prim_path=self.particleSystemPath, material_path=self.particle_material_path
            )     
            

            # Create a pbd particle material and set it on the particle system
            particleUtils.add_pbd_particle_material(
                self.stage,
                self.particle_material_path,
                cohesion=0.01,
                viscosity=0.0091,
                surface_tension=0.0074,
                friction=0.1,
            )
            physicsUtils.add_physics_material_to_prim(self.stage, particle_system.GetPrim(), self.particle_material_path)

            # max velocity
            particle_system.CreateMaxVelocityAttr().Set(max_velocity)

            

            # add particle anisotropy
            anisotropyAPI = PhysxSchema.PhysxParticleAnisotropyAPI.Apply(particle_system.GetPrim())
            anisotropyAPI.CreateParticleAnisotropyEnabledAttr().Set(True)
            aniso_scale = 1.0 # 5.0
            anisotropyAPI.CreateScaleAttr().Set(aniso_scale)
            anisotropyAPI.CreateMinAttr().Set(1.0)
            anisotropyAPI.CreateMaxAttr().Set(2.0)

            # add particle smoothing
            smoothingAPI = PhysxSchema.PhysxParticleSmoothingAPI.Apply(particle_system.GetPrim())
            smoothingAPI.CreateParticleSmoothingEnabledAttr().Set(True)
            smoothingAPI.CreateStrengthAttr().Set(0.5)

            fluidRestOffset = self._particleSystemSchemaParameters["rest_offset"]
            # apply isosurface params
            isosurfaceAPI = PhysxSchema.PhysxParticleIsosurfaceAPI.Apply(particle_system.GetPrim())
            isosurfaceAPI.CreateIsosurfaceEnabledAttr().Set(True)
            isosurfaceAPI.CreateMaxVerticesAttr().Set(1024 * 1024)
            isosurfaceAPI.CreateMaxTrianglesAttr().Set(2 * 1024 * 1024)
            isosurfaceAPI.CreateMaxSubgridsAttr().Set(1024 * 4)
            isosurfaceAPI.CreateGridSpacingAttr().Set(fluidRestOffset * 1.5)
            isosurfaceAPI.CreateSurfaceDistanceAttr().Set(fluidRestOffset * 1.6)
            isosurfaceAPI.CreateGridFilteringPassesAttr().Set("")
            isosurfaceAPI.CreateGridSmoothingRadiusAttr().Set(fluidRestOffset * 2)

            isosurfaceAPI.CreateNumMeshSmoothingPassesAttr().Set(1)

            primVarsApi = UsdGeom.PrimvarsAPI(particle_system)
            primVarsApi.CreatePrimvar("doNotCastShadows", Sdf.ValueTypeNames.Bool).Set(True)

            self.stage.SetInterpolationType(Usd.InterpolationTypeHeld)

        asyncio.ensure_future(enable_isosurface_async())

    def shutdown(self):
        self.particle_positions = None