import importlib
from pathlib import Path
import os
import json
import logging
import shutil

from .schedule_manager import ScheduleManager
# from dotenv import load_dotenv
# from model import PlaylistManager, RefreshInfo

logger = logging.getLogger(__name__)

class PluginConfigurationManager:
	def __init__(self, root_path, plugin_id):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if plugin_id == None:
			raise ValueError("plugin_id cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.plugin_id = plugin_id
		self.ROOT_PATH = os.path.join(root_path, self.plugin_id)
		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")

	def ensure_folders(self):
		try:
			os.makedirs(self.ROOT_PATH, exist_ok=True)
			logger.debug(f"Created: {self.ROOT_PATH}")
		except Exception as e:
			logger.error(f"Error: {self.ROOT_PATH}: {e}")

	def _internal_load(self, file_path):
		if os.path.isfile(file_path):
			try:
				with open(file_path, 'r') as fx:
					data = json.load(fx)
					return data
			except Exception as e:
				logger.error(f"Error loading file '{file_path}': {e}")
				return None
		return None

	def _internal_save(self, file_path, data):
		try:
			with open(file_path, 'w') as fx:
				json.dump(data, fx, indent=2)
			logger.debug(f"File '{file_path}' saved successfully.")
		except Exception as e:
			logger.error(f"Error saving file '{file_path}': {e}")

	def load_state(self):
		"""Loads the state for a given plugin from its JSON file."""
		plugin_state_file = os.path.join(self.ROOT_PATH, "state.json")
		state = self._internal_load(plugin_state_file)
		if state is not None:
			return state
		else:
			return {}

	def save_state(self, state):
		"""Saves the state for a given plugin to its JSON file."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"Directory {self.ROOT_PATH} does not exist. Call ensure_folders() first.")
		plugin_state_file = os.path.join(self.ROOT_PATH, "state.json")
		self._internal_save(plugin_state_file, state)

	def load_settings(self):
		"""Loads the state for a given plugin from its JSON file."""
		plugin_state_file = os.path.join(self.ROOT_PATH, "settings.json")
		state = self._internal_load(plugin_state_file)
		if state is not None:
			return state
		else:
			return {}

	def save_settings(self, state):
		"""Saves the state for a given plugin to its JSON file."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"Directory {self.ROOT_PATH} does not exist. Call ensure_folders() first.")
		plugin_state_file = os.path.join(self.ROOT_PATH, "settings.json")
		self._internal_save(plugin_state_file, state)

class ConfigurationManager:
	def __init__(self, root_path=None, storage_path=None):
		# Root path for the project directory
		if root_path != None:
			self.ROOT_PATH = root_path
			logger.debug(f"Provided root_path: {self.ROOT_PATH}")
		else:
			# NOTE: this is based on the current folder structure and location of this file
			self.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
			pobj = Path(self.ROOT_PATH)
			self.ROOT_PATH = pobj.parent
			logger.debug(f"Calculated root_path: {self.ROOT_PATH}")
		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")
		# File paths relative to the script's directory
#		self.config_file = os.path.join(self.ROOT_PATH, "config", "device.json")
		# File path for storing the current image being displayed
#		self.current_image_file = os.path.join(self.ROOT_PATH, "static", "images", "current_image.png")
		# Directory path for storing plugin instance images
#		self.plugin_image_dir = os.path.join(self.ROOT_PATH, "static", "images", "plugins")
#		logger.debug(f"plugin_image_dir: {self.plugin_image_dir} storage: {self.STORAGE_PATH}")
		# Root Path for plugin storage
		if storage_path != None:
			self.STORAGE_PATH = storage_path
			logger.debug(f"Provided storage_path: {storage_path}")
		else:
			pobj = Path(self.ROOT_PATH)
			self.STORAGE_PATH = os.path.join(pobj.parent, ".storage")
			logger.debug(f"Calculated storage_path: {self.STORAGE_PATH}")
		self.storage_plugins = os.path.join(self.STORAGE_PATH, "plugins")
		self.storage_schedules = os.path.join(self.STORAGE_PATH, "schedules")
		logger.debug(f"STORAGE_PATH: {self.STORAGE_PATH}")
		# Load environment variables from a .env file if present
		# load_dotenv()

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
				self.logger.info(f"HardReset '{self.STORAGE_PATH}' all contents deleted successfully.")
			except OSError as e:
					self.logger.error(f"HardReset: {self.STORAGE_PATH} : {e.strerror}")
		else:
			self.logger.debug(f"HardReset '{self.STORAGE_PATH}' does not exist.")

		self.ensure_folders()
		self._reset_plugins()

	def _reset_plugins(self):
		plugins = self.enum_plugins()
		for pinfo in plugins:
			info = pinfo["info"]
			plugin_id = info.get("id")
			pcm = self.plugin_storage_manager(plugin_id)
			pcm.ensure_folders()
			psettings = info.get("settings", None);
			if psettings == None:
				pcm.save_settings({})
				continue
			settings = psettings.get("default", None);
			if settings == None:
				pcm.save_settings({})
				continue
			pcm.save_settings(settings)

	def ensure_folders(self):
		"""Ensures that necessary directories exist."""
		if not os.path.exists(self.ROOT_PATH):
			raise ValueError(f"BASE_DIR {self.ROOT_PATH} does not exist.")
		directories = [
			self.STORAGE_PATH,
			self.storage_plugins,
			self.storage_schedules
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

	def plugin_storage_manager(self, plugin_id):
		"""Returns a PluginConfigurationManager for the given plugin_id."""
		if plugin_id == None:
			raise ValueError("plugin_id cannot be None")
		manager = PluginConfigurationManager(self.storage_plugins, plugin_id)
		manager.ensure_folders()
		return manager

	def schedule_manager(self):
		manager = ScheduleManager(self.storage_schedules)
		return manager

	def display_manager(self):
		# Placeholder for future display configuration management
		raise NotImplementedError("Display manager not implemented yet.")

	def application_manager(self):
		# Placeholder for future application configuration management
		raise NotImplementedError("Application manager not implemented yet.")

	def enum_plugins(self):
		"""Reads the plugin-info.json config JSON from each plugin folder. Excludes the base plugin."""
		# Iterate over all plugin folders
		plugins_list = []
		path = os.path.join(self.ROOT_PATH, "plugins")
		logger.debug(f"enum_plugins: {path}")
		for plugin in sorted(os.listdir(path)):
			plugin_path = os.path.join(self.ROOT_PATH, "plugins", plugin)
			if os.path.isdir(plugin_path) and plugin != "__pycache__":
				# Check if the plugin-info.json file exists
				plugin_info_file = os.path.join(plugin_path, "plugin-info.json")
				if os.path.isfile(plugin_info_file):
					logger.debug(f"plugin info {plugin_info_file}")
					with open(plugin_info_file) as f:
						plugin_info = json.load(f)
					plugins_list.append({ "info":plugin_info, "path":plugin_path })
		return plugins_list

	def load_plugins(self, infos):
		plugin_map = {}
		for info in infos:
			plugin_info = info["info"]
			plugin_path = info["path"]
			plugin_id = plugin_info.get("id")
			plugin_name = plugin_info.get("name")
			if plugin_info.get("disabled", False):
				logger.info(f"Plugin '{plugin_name}' (ID: {plugin_id}) is disabled; skipping load.")
				continue
			plugin_file = plugin_info.get("file")
			plugin_module = plugin_info.get("module")
			module_path = os.path.join(plugin_path, plugin_file)
			if not os.path.exists(module_path):
					logging.error(f"Could not find module path {module_path} for '{plugin_id}', skipping.")
					continue
			try:
				module = importlib.import_module(plugin_module)
				plugin_class = getattr(module, plugin_info.get("class"), None)

				if plugin_class:
					# Create an instance of the plugin class and add it to the plugin_classes dictionary
					plugin_map[plugin_id] = plugin_class(plugin_id, plugin_name)

			except ImportError as e:
				logging.error(f"Failed to import plugin module {plugin_module}: {e}")
			pass
		return plugin_map