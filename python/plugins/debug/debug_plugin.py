import logging

from ...model.configuration_manager import PluginConfigurationManager
from ...model.schedule import SchedulableBase
from ..plugin_base import PluginBase


class DebugPlugin(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def schedule(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		self.logger.info(f"'{self.name}' timeslot '{sb.title}'.")
	def receive(self, msg):
		self.logger.info(f"'{self.name}' received message: {msg}")
	def reconfigure(self, config):
		self.logger.info(f"'{self.name}' reconfigured with: {config}")