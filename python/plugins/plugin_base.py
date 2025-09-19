from ..model.configuration_manager import PluginConfigurationManager
from ..model.schedule import SchedulableBase

class PluginBase:
	def __init__(self, id, name):
		self.id = id
		self.name = name
	def timeslot_start(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		pass
	def timeslot_end(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		pass
	def schedule(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		pass
	def receive(self, msg):
		pass
	def reconfigure(self, config):
		pass