import logging
from ..plugin_base import PluginBase


class DebugPlugin(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def schedule(self):
		self.logger.info(f"DebugPlugin '{self.name}' scheduling task.")
	def receive(self, msg):
		self.logger.info(f"DebugPlugin '{self.name}' received message: {msg}")
	def reconfigure(self, config):
		self.logger.info(f"DebugPlugin '{self.name}' reconfigured with: {config}")