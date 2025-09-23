import unittest
import os
import tempfile

from ..model.configuration_manager import ConfigurationManager

class TestConfigurationManager(unittest.TestCase):
	def test_enum_plugins(self):
		cm = ConfigurationManager()
		list = cm.enum_plugins()
		self.assertIsNotNone(list)
		self.assertEqual(len(list), 2)  # Adjust based on expected number of plugins
		info0 = list[0].get('info', None)
		self.assertIsNotNone(info0, 'info0 failed')
		self.assertEqual(info0['id'], 'clock')
		self.assertEqual(info0['class'], 'Clock')
		info1 = list[1].get('info', None)
		self.assertIsNotNone(info1, 'info1 failed')
		self.assertEqual(info1['id'], 'debug')
		self.assertEqual(info1['class'], 'DebugPlugin')

	def test_load_plugins(self):
		cm = ConfigurationManager()
		infos = cm.enum_plugins()
		plugins = cm.load_plugins(infos)
		self.assertIsNotNone(plugins)
		self.assertEqual(len(plugins), 2)  # Adjust based on expected number of loaded plugins
		plugin = plugins.get('debug', None)
		self.assertIsNotNone(plugin, 'plugin debug failed')
		self.assertEqual(plugin.id, 'debug')
		self.assertEqual(plugin.name, 'Debug Plugin')

	def test_load_save_plugin_state(self):
		with tempfile.TemporaryDirectory() as tempdir:
			# Use a temporary directory for storage to avoid side effects
			cm = ConfigurationManager(storage_path=tempdir)
			cm.ensure_folders()
			pcm = cm.plugin_manager('debug')
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