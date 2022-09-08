# params
from pxr import Gf


class PARTICLE_PROPERTY:
    @classmethod
    def set_partical_properties(cls, particel_scale = 10):

        PARTICLE_PROPERTY._fluidSphereDiameter = 0.24 * particel_scale
        PARTICLE_PROPERTY._particleSystemSchemaParameters = {
            "contact_offset": 0.3 * particel_scale,
            "particle_contact_offset": 0.25 * particel_scale,
            "rest_offset": 0.25 * particel_scale,
            "solid_rest_offset": 0,
            "fluid_rest_offset": 0.5 * PARTICLE_PROPERTY._fluidSphereDiameter + 0.03 * particel_scale,
            "solver_position_iterations": 10,
            "wind": Gf.Vec3f(0, 0, 0),
            "max_velocity": 40  ,
        }

        PARTICLE_PROPERTY._particleMaterialAttributes = {
            "friction": 0.34,
            "viscosity": 0.0,
            "vorticity_confinement": 0.5,
            "surface_tension": 0.74,
            "cohesion": 0.1,
            # "cfl_coefficient": 1.0,
        }

        PARTICLE_PROPERTY._particleSystemAttributes = {
                "cohesion": 0.0,
                "smoothing": 0.8,
                "anisotropyScale": 1.0,
                "anisotropyMin": 0.2,
                "anisotropyMax": 2.0,
                "surfaceTension": 0.74,
                "vorticityConfinement": 0.5,
                "viscosity": 0.0,
                "particleFriction": 0.34,
                "maxVelocity": 40,
            }
        PARTICLE_PROPERTY._particle_mass = 1e-6 * particel_scale*particel_scale
        PARTICLE_PROPERTY._particle_scale = (0.5, 0.5, 0.5) 
        
        PARTICLE_PROPERTY._cup_rest_offset = 0.0
        PARTICLE_PROPERTY._cup_contact_offset = 1.0
        PARTICLE_PROPERTY._cup_mass = 1

        PARTICLE_PROPERTY._gravityMagnitude = 100