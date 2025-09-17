import unittest
import os
import tempfile

from python.model.configuration_manager import ConfigurationManager

class TestConfigurationManager(unittest.TestCase):
	def test_enum_plugins(self):
		# This is a placeholder test. Actual implementation would depend on the filesystem and plugin structure.
		cm = ConfigurationManager()
		list = cm.enum_plugins()
		self.assertIsNotNone(list)
		self.assertEqual(len(list), 1)  # Adjust based on expected number of plugins
		info0 = list[0].get('info', None)
		self.assertIsNotNone(info0, 'info0 failed')
		self.assertEqual(info0['id'], 'debug')  # Adjust based on expected plugin IDs
		self.assertEqual(info0['class'], 'DebugPlugin')  # Adjust based on expected plugin names

	def test_load_plugins(self):
		cm = ConfigurationManager()
		infos = cm.enum_plugins()
		plugins = cm.load_plugins(infos)
		self.assertIsNotNone(plugins)
		self.assertEqual(len(plugins), 1)  # Adjust based on expected number of loaded plugins
		plugin = plugins.get('debug', None)  # Adjust based on expected plugin IDs
		self.assertIsNotNone(plugin, 'plugin debug failed')
		self.assertEqual(plugin.id, 'debug')  # Adjust based on expected plugin names
		self.assertEqual(plugin.name, 'Debug Plugin')  # Adjust based on expected plugin names

	def test_load_save_plugin_state(self):
		with tempfile.TemporaryDirectory() as tempdir:
			# Use a temporary directory for storage to avoid side effects
			cm = ConfigurationManager(storage_path=tempdir)
			cm.ensure_folders()
			pcm = cm.plugin_storage_manager('debug')
			self.assertIsNotNone(pcm)
			pcm.ensure_folders()
			state = pcm.load_state()
			self.assertIsNotNone(state)
			self.assertEqual(state, {}, 'Initial state should be empty')

			test_state = {'key': 'value'}
			pcm.save_state(test_state)

			loaded_state = pcm.load_state()
			self.assertIsNotNone(loaded_state)
			self.assertEqual(loaded_state, test_state, 'Loaded state should match saved state')

if __name__ == "__main__":
    unittest.main()