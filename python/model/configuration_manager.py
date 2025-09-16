import os
import json
import logging
# from dotenv import load_dotenv
# from model import PlaylistManager, RefreshInfo

logger = logging.getLogger(__name__)

class ConfigurationManager:
	# Base path for the project directory
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))

	# File paths relative to the script's directory
	config_file = os.path.join(BASE_DIR, "config", "device.json")

	# File path for storing the current image being displayed
	current_image_file = os.path.join(BASE_DIR, "static", "images", "current_image.png")

	# Directory path for storing plugin instance images
	plugin_image_dir = os.path.join(BASE_DIR, "static", "images", "plugins")

	def read_plugins_list(self):
		"""Reads the plugin-info.json config JSON from each plugin folder. Excludes the base plugin."""
		# Iterate over all plugin folders
		plugins_list = []
		for plugin in sorted(os.listdir(os.path.join(self.BASE_DIR, "plugins"))):
			plugin_path = os.path.join(self.BASE_DIR, "plugins", plugin)
			if os.path.isdir(plugin_path) and plugin != "__pycache__":
				# Check if the plugin-info.json file exists
				plugin_info_file = os.path.join(plugin_path, "plugin-info.json")
				if os.path.isfile(plugin_info_file):
					logger.debug(f"Reading plugin info from {plugin_info_file}")
					with open(plugin_info_file) as f:
						plugin_info = json.load(f)
					plugins_list.append(plugin_info)
		return plugins_list
