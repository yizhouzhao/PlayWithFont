import omni
import carb
import os
from pathlib import Path

EXTENSION_FOLDER_PATH = Path(
    omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
)

EXTENSION_ROOT = str(EXTENSION_FOLDER_PATH.resolve())
print("EXTENSION_ROOT: ", EXTENSION_ROOT) 