import os
from pathlib import Path

from pathvalidate import sanitize_filename
from ..model.configuration_manager import ConfigurationManager
from PIL import Image

def test_output_path_for(plugin: str) -> str:
	test_file_path = os.path.abspath(__file__)
	opath = Path(os.path.dirname(test_file_path)).parent.parent.joinpath(".test-output", plugin)
	folder = str(opath.resolve())
	if not os.path.exists(folder):
		os.makedirs(folder)
	return folder

def save_image(image:Image.Image, folder:str, ix:int, title:str):
	image_path = os.path.join(folder, sanitize_filename(f"im_{ix:03d}_{image.width}x{image.height}_{title}.png"))
	image.save(image_path)

def storage_path():
	test_file_path = os.path.abspath(__file__)
	test_directory = os.path.dirname(test_file_path)
	storage = os.path.join(test_directory, ".storage")
	return storage

def create_configuration_manager():
	storage = storage_path()
	cm = ConfigurationManager(storage_path=storage)
	return cm
