import logging

from ...model.configuration_manager import PluginConfigurationManager
from ...model.schedule import SchedulableBase
from ...task.messages import BasicMessage
from ..plugin_base import PluginBase, PluginExecutionContext


class DebugPlugin(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		self.logger.info(f"'{self.name}' timeslot.start '{sb.title}'.")
	def timeslot_end(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		self.logger.info(f"'{self.name}' timeslot.end '{sb.title}'.")
	def schedule(self, sb: SchedulableBase, pcm: PluginConfigurationManager):
		self.logger.info(f"'{self.name}' schedule '{sb.title}'.")
	def receive(self, pec: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")