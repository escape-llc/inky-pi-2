import datetime

from ..task.basic_task import BasicTask
from ..task.message_router import MessageRouter
from ..task.messages import BasicMessage
from ..model.configuration_manager import PluginConfigurationManager, SettingsConfigurationManager
from ..model.schedule import SchedulableBase

class PluginExecutionContext:
	def __init__(self, sb: SchedulableBase, scm: SettingsConfigurationManager, pcm: PluginConfigurationManager, resolution, schedule_ts: datetime, router:MessageRouter):
		if sb is None:
			raise ValueError("sb is None")
		if scm is None:
			raise ValueError("scm is None")
		if pcm is None:
			raise ValueError("pcm is None")
		if schedule_ts is None:
			raise ValueError("schedule_ts is None")
		if router is None:
			raise ValueError("router is None")
		self.sb = sb
		self.pcm = pcm
		self.scm = scm
		self.resoluion = resolution
		self.schedule_ts = schedule_ts
		self.router = router

class PluginBase:
	def __init__(self, id, name):
		self.id = id
		self.name = name
	def timeslot_start(self, pec: PluginExecutionContext):
		pass
	def timeslot_end(self, pec: PluginExecutionContext):
		pass
	def schedule(self, pec: PluginExecutionContext):
		pass
	def receive(self, msg: BasicMessage):
		pass
	def reconfigure(self, config):
		pass