import importlib
from pathlib import Path
import os
import json
import logging
import shutil
from typing import Any
from PIL import ImageFont

from ..utils.file_utils import path_to_file_url
from .schedule_manager import ScheduleManager

logger = logging.getLogger(__name__)

def _internal_load(file_path):
	if os.path.isfile(file_path):
		try:
			with open(file_path, 'r') as fx:
				data = json.load(fx)
				return data
		except Exception as e:
			logger.error(f"Error loading file '{file_path}': {e}")
			return None
	return None

def _internal_save(file_path, data):
	try:
		with open(file_path, 'w') as fx:
			json.dump(data, fx, indent=2)
#			logger.debug(f"File '{file_path}' saved successfully.")
	except Exception as e:
		logger.error(f"Error saving file '{file_path}': {e}")

class DatasourceConfigurationManager:
	"""
	Manage settings, state, etc. for a datasource.
	Rooted at the "datasources/<datasource_id>" folder in storage.
	"""
	def __init__(self, root_path, datasource_id):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if datasource_id == None:
			raise ValueError("datasource_id cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.datasource_id = datasource_id
		self.ROOT_PATH = os.path.join(root_path, self.datasource_id)
	def ensure_folders(self):
		try:
			os.makedirs(self.ROOT_PATH, exist_ok=True)
			logger.debug(f"Created: {self.ROOT_PATH}")
		except Exception as e:
			logger.error(f"Error: {self.ROOT_PATH}: {e}")
	def load_settings(self):
		"""Loads the state for a given datasource from its JSON file."""
		plugin_state_file = os.path.join(self.ROOT_PATH, "settings.json")
		state = _internal_load(plugin_state_file)
		return state

class PluginConfigurationManager:
	"""
	Manage settings, state, etc. for a plugin.
	Rooted at the "plugins/<plugin_id>" folder in storage.
	"""
	def __init__(self, root_path, plugin_id):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if plugin_id == None:
			raise ValueError("plugin_id cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.plugin_id = plugin_id
		self.ROOT_PATH = os.path.join(root_path, self.plugin_id)
#		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")

	def ensure_folders(self):
		try:
			os.makedirs(self.ROOT_PATH, exist_ok=True)
			logger.debug(f"Created: {self.ROOT_PATH}")
		except Exception as e:
			logger.error(f"Error: {self.ROOT_PATH}: {e}")

	def load_state(self):
		"""Loads the state for a given plugin from its JSON file."""
		plugin_state_file = os.path.join(self.ROOT_PATH, "state.json")
		state = _internal_load(plugin_state_file)
		return state

	def save_state(self, state):
		"""Saves the state for a given plugin to its JSON file."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"Directory {self.ROOT_PATH} does not exist. Call ensure_folders() first.")
		plugin_state_file = os.path.join(self.ROOT_PATH, "state.json")
		_internal_save(plugin_state_file, state)

	def delete_state(self):
		if not os.path.exists(self.ROOT_PATH):
			return
		plugin_state_file = os.path.join(self.ROOT_PATH, "state.json")
		if not os.path.isfile(plugin_state_file):
			return
		try:
			os.remove(plugin_state_file)
		except Exception as e:
			logger.error(f"Error deleting file '{plugin_state_file}': {e}")

	def load_settings(self):
		"""Loads the state for a given plugin from its JSON file."""
		plugin_state_file = os.path.join(self.ROOT_PATH, "settings.json")
		state = _internal_load(plugin_state_file)
		return state

	def settings_path(self):
		"""Returns the path to the settings.json file for this plugin."""
		return os.path.join(self.ROOT_PATH, "settings.json")

	def save_settings(self, state):
		"""Saves the state for a given plugin to its JSON file."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"Directory {self.ROOT_PATH} does not exist. Call ensure_folders() first.")
		if state is None:
			raise ValueError("state must not be None")
		plugin_state_file = os.path.join(self.ROOT_PATH, "settings.json")
		_internal_save(plugin_state_file, state)

class SettingsConfigurationManager:
	"""
	Manage system-level settings, e.g. system, display (not plugins).
	Rooted at the "settings" folder in storage.
	"""
	def __init__(self, root_path):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.ROOT_PATH = root_path
#		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")

	def load_settings(self, settings: str):
		"""Loads the state for a given settings from its JSON file."""
		settings_file = self.settings_path(settings)
		state = _internal_load(settings_file)
		return state

	def settings_path(self, settings: str):
		"""Returns the path to the JSON file for this settings."""
		return os.path.join(self.ROOT_PATH, f"{settings}-settings.json")

FONT_FAMILIES = {
	"Dogica": [{
		"font-weight": "normal",
		"file": "dogicapixel.ttf"
	},{
		"font-weight": "bold",
		"file": "dogicapixelbold.ttf"
	}],
	"Jost": [{
		"font-weight": "normal",
		"file": "Jost.ttf"
	},{
		"font-weight": "bold",
		"file": "Jost-SemiBold.ttf"
	}],
	"Napoli": [{
		"font-weight": "normal",
		"file": "Napoli.ttf"
	}],
	"DS-Digital": [{
		"font-weight": "normal",
		"file": os.path.join("DS-DIGI", "DS-DIGI.TTF")
	}]
}
class StaticConfigurationManager:
	"""
	Rooted at the "static" folder; manages static resources like fonts and render assets.
	"""
	def __init__(self, root_path):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.ROOT_PATH = root_path
#		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")
	def enum_fonts(self):
		fonts_list = []
		for font_family, variants in FONT_FAMILIES.items():
			for variant in variants:
				fonts_list.append({
					"font_family": font_family,
					"url": path_to_file_url(os.path.join(self.ROOT_PATH, "fonts", variant["file"])),
					"font_weight": variant.get("font-weight", "normal"),
					"font_style": variant.get("font-style", "normal"),
				})
		return fonts_list
	def get_font(self, font_name: str, font_size=50, font_weight="normal"):
		if font_name in FONT_FAMILIES:
			font_variants = FONT_FAMILIES[font_name]

			font_entry = next((entry for entry in font_variants if entry["font-weight"] == font_weight), None)
			if font_entry is None:
				font_entry = font_variants[0]  # Default to first available variant

			if font_entry:
				font_path = os.path.join(self.ROOT_PATH, "fonts", font_entry["file"])
				return ImageFont.truetype(font_path, font_size)
		raise ValueError(f"Font not found: font_name={font_name}, font_weight={font_weight}")

class ConfigurationManager:
	"""Manage the paths used for configuration and working storage."""
	def __init__(self, root_path=None, storage_path=None, nve_path=None):
		# Root path is the python directory
		# Storage path is where working storage is hosted
		# NVE path (Non-Volatile Environment) is the source used to initialize Storage
		if root_path != None:
			self.ROOT_PATH = root_path
#			logger.debug(f"Provided root_path: {self.ROOT_PATH}")
		else:
			# NOTE: this is based on the current folder structure and location of this file
			self.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
			pobj = Path(self.ROOT_PATH)
			self.ROOT_PATH = str(pobj.parent)
#			logger.debug(f"Calculated root_path: {self.ROOT_PATH}")

		self.static_path = os.path.join(self.ROOT_PATH, "static")
#		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")
		# File path for storing the current image being displayed
#		self.current_image_file = os.path.join(self.ROOT_PATH, "static", "images", "current_image.png")
		# Directory path for storing plugin instance images
#		self.plugin_image_dir = os.path.join(self.ROOT_PATH, "static", "images", "plugins")
#		logger.debug(f"plugin_image_dir: {self.plugin_image_dir} storage: {self.STORAGE_PATH}")

		# Storage path is for storage; MUST BE external to the ROOT_PATH
		if storage_path != None:
			# points directly to ".storage" folder
			self.STORAGE_PATH = storage_path
#			logger.debug(f"Provided storage_path: {self.STORAGE_PATH}")
		else:
			# sibling ".storage" folder with ROOT_PATH
			pobj = Path(self.ROOT_PATH)
			self.STORAGE_PATH = os.path.join(pobj.parent, ".storage")
#			logger.debug(f"Calculated storage_path: {self.STORAGE_PATH}")

		if nve_path != None:
			self.NVE_PATH = nve_path
#			logger.debug(f"Provided nve_path: {nve_path}")
		else:
			self.NVE_PATH = os.path.join(self.ROOT_PATH, "storage")
#			logger.debug(f"Calculated nve_path: {self.NVE_PATH}")

		self.storage_plugins = os.path.join(self.STORAGE_PATH, "plugins")
		self.storage_ds = os.path.join(self.STORAGE_PATH, "datasources")
		self.storage_schedules = os.path.join(self.STORAGE_PATH, "schedules")
		self.storage_settings = os.path.join(self.STORAGE_PATH, "settings")
		self.storage_schemas = os.path.join(self.STORAGE_PATH, "schemas")
		# Load environment variables from a .env file if present
		# load_dotenv()

	def duplicate(self):
		return ConfigurationManager(root_path=self.ROOT_PATH, storage_path=self.STORAGE_PATH, nve_path=self.NVE_PATH)

	def hard_reset(self):
		"""Deletes all storage folders and recreates them."""
		if os.path.exists(self.STORAGE_PATH):
			try:
				for item in os.listdir(self.STORAGE_PATH):
					item_path = os.path.join(self.STORAGE_PATH, item)
					if os.path.isfile(item_path):
							os.remove(item_path)  # Remove files
					elif os.path.isdir(item_path):
							shutil.rmtree(item_path)
				logger.info(f"HardReset '{self.STORAGE_PATH}' all contents deleted successfully.")
			except OSError as e:
				logger.error(f"HardReset: {self.STORAGE_PATH} : {e.strerror}")
		else:
			logger.debug(f"HardReset '{self.STORAGE_PATH}' does not exist.")

		self.ensure_folders()
		self._reset_storage()
		self._reset_plugins()

	def _reset_storage(self):
		"""Copy the NVE storage tree to the STORAGE_PATH. Deploy settings to the STORAGE_PATH."""
		if not os.path.exists(self.STORAGE_PATH):
			raise ValueError(f"STORAGE_PATH {self.STORAGE_PATH}")
		if not os.path.exists(self.NVE_PATH):
			raise ValueError(f"NVE_PATH {self.NVE_PATH}")
		try:
			# base files: schedules and schemas
			shutil.copytree(self.NVE_PATH, self.STORAGE_PATH, dirs_exist_ok=True)
			# extract settings: system, display
			settings_files = os.listdir(self.storage_schemas)
			for file in settings_files:
				schema_path = os.path.join(self.storage_schemas, file)
				basename = Path(schema_path).stem
				settings_path = os.path.join(self.storage_settings, f"{basename}-settings.json")
				settings = {}
				with open(schema_path) as f:
					schema = json.load(f)
					defx = schema.get("default", None)
					if defx is not None:
						settings = defx
				with open(settings_path, 'w') as fx:
					json.dump(settings, fx, indent=2)

			logger.info(f"ResetStorage '{self.STORAGE_PATH}' all contents copied successfully.")
		except OSError as e:
				logger.error(f"ResetStorage: {self.STORAGE_PATH} : {e.strerror}")
		pass

	def _reset_plugins(self):
		plugins = self.enum_plugins()
		for pinfo in plugins:
			info = pinfo["info"]
			plugin_id = info.get("id")
			pcm = self.plugin_manager(plugin_id)
			pcm.ensure_folders()
			psettings = info.get("settings", None)
			if psettings == None:
				continue
			settings = psettings.get("default", None)
			if settings == None:
				continue
			pcm.save_settings(settings)

	def ensure_folders(self):
		"""Ensures that necessary directories exist.  Does not consider files."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"ROOT_PATH {self.ROOT_PATH} does not exist.")
		if not os.path.exists(self.NVE_PATH):
			raise ValueError(f"NVE_PATH {self.NVE_PATH} does not exist.")
		directories = [
			self.STORAGE_PATH,
			self.storage_plugins,
			self.storage_ds,
			self.storage_settings,
		]
		for directory in directories:
			if not os.path.exists(directory):
				try:
					os.makedirs(directory)
					logger.debug(f"EnsureFolders Created: {directory}")
				except Exception as e:
					logger.error(f"EnsureFolders {directory}: {e}")
			else:
				logger.debug(f"EnsureFolders exists: {directory}")

	def plugin_manager(self, plugin_id):
		"""Returns a PluginConfigurationManager for the given plugin_id."""
		if plugin_id == None:
			raise ValueError("plugin_id cannot be None")
		manager = PluginConfigurationManager(self.storage_plugins, plugin_id)
		manager.ensure_folders()
		return manager

	def datasource_manager(self, datasource_id):
		"""Returns a DatasourceConfigurationManager for the given datasource_id."""
		if datasource_id == None:
			raise ValueError("datasource_id cannot be None")
		manager = DatasourceConfigurationManager(self.storage_ds, datasource_id)
		manager.ensure_folders()
		return manager

	def schedule_manager(self):
		"""Create a ScheduleManager bound to the schedule storage folder."""
		manager = ScheduleManager(self.storage_schedules)
		return manager

	def settings_manager(self):
		"""Create a SettingsConfigurationManager bound to settings storage folder."""
		manager = SettingsConfigurationManager(self.storage_settings)
		return manager

	def static_manager(self):
		"""Create a StaticConfigurationManager bound to the root path."""
		manager = StaticConfigurationManager(self.static_path)
		return manager

	def _collect_info(self, folder: str, info_file_name: str):
		# Iterate over all XXX folders
		item_list = []
		path = os.path.join(self.ROOT_PATH, folder)
		logger.debug(f"collect_info: {path}")
		for item in sorted(os.listdir(path)):
			item_path = os.path.join(self.ROOT_PATH, folder, item)
			if os.path.isdir(item_path) and item != "__pycache__":
				# Check if the XXX-info.json file exists
				info_file = os.path.join(item_path, info_file_name)
				if os.path.isfile(info_file):
					logger.debug(f"plugin info {info_file}")
					with open(info_file) as f:
						item_info = json.load(f)
					item_list.append({ "info":item_info, "path":item_path })
		return item_list

	def enum_plugins(self):
		"""Reads the plugin-info.json config JSON from each plugin folder. Excludes the base plugin."""
		# Iterate over all plugin folders
		plugins_list = self._collect_info("plugins", "plugin-info.json")
		return plugins_list

	def enum_datasources(self):
		"""Reads the datasource-info.json config JSON from each datasource folder. Excludes the base datasource."""
		# Iterate over all plugin folders
		datasources_list = self._collect_info("datasources", "datasource-info.json")
		return datasources_list

	def _resolve(self, info_path:str, info) -> Any|None:
		info_id = info.get("id")
		info_file = info.get("file")
		info_module = info.get("module")
		info_class = info.get("class")
		module_path = os.path.join(info_path, info_file)
		if not os.path.exists(module_path):
			logger.error(f"No module path '{module_path}' for '{info_id}', skipping.")
			return None
		try:
			module = importlib.import_module(info_module)
			item_class = getattr(module, info_class, None)
			return item_class
		except ImportError as e:
			logger.error(f"Failed to import module '{info_module}': {e}")
			return None

	def load_plugins(self, infos):
		"""Take the result of enum_plugins() and instantiate the plugin objects."""
		plugin_map = {}
		for info in infos:
			plugin_info = info["info"]
			plugin_path = info["path"]
			plugin_id = plugin_info.get("id")
			plugin_name = plugin_info.get("name")
			if plugin_info.get("disabled", False):
				logger.info(f"Plugin '{plugin_name}' (ID: {plugin_id}) is disabled; skipping load.")
				continue
			plugin_class = self._resolve(plugin_path, plugin_info)
			if plugin_class:
				# Create an instance of the plugin class and add it to the plugin_classes dictionary
				plugin_map[plugin_id] = plugin_class(plugin_id, plugin_name)
			pass
		return plugin_map
	
	def load_datasources(self, infos):
		"""Take the result of enum_datasources() and instantiate the datasource objects."""
		datasource_map = {}
		for info in infos:
			info_info = info["info"]
			info_path = info["path"]
			info_id = info_info.get("id")
			info_name = info_info.get("name")
			if info_info.get("disabled", False):
				logger.info(f"Item '{info_name}' (ID: {info_id}) is disabled; skipping load.")
				continue
			ds_class = self._resolve(info_path, info_info)
			if ds_class:
				# Create an instance of the item class and add it to the dictionary
				datasource_map[info_id] = ds_class(info_id)
			pass
		return datasource_map

	def load_blueprints(self, infos):
		"""Take the result of enum_X() and resolve the blueprints."""
		blueprint_map = {}
		for info in infos:
			info_info = info["info"]
			info_path = info["path"]
			info_id = info_info.get("id")
			info_name = info_info.get("name")
			if info_info.get("disabled", False):
				logger.info(f"'{info_name}' (ID: {info_id}) is disabled; skipping load.")
				continue
			blueprint_info = info_info.get("blueprint", None)
			if blueprint_info is None:
				continue
			blueprint_class = self._resolve(info_path, blueprint_info)
			if blueprint_class:
				# Create an instance of the blueprint class and add it to the blueprint_classes dictionary
				blueprint_map[info_id] = blueprint_class
			pass
		return blueprint_map