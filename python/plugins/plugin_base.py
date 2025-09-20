import datetime

from python.task.basic_task import BasicTask
from python.task.messages import BasicMessage
from ..model.configuration_manager import PluginConfigurationManager, SettingsConfigurationManager
from ..model.schedule import SchedulableBase

class PluginExecutionContext:
	def __init__(self, sb: SchedulableBase, scm: SettingsConfigurationManager, pcm: PluginConfigurationManager, schedule_ts: datetime, _display:BasicTask):
		if sb is None:
			raise ValueError("sb is None")
		if scm is None:
			raise ValueError("scm is None")
		if pcm is None:
			raise ValueError("pcm is None")
		if schedule_ts is None:
			raise ValueError("schedule_ts is None")
		if _display is None:
			raise ValueError("_display is None")
		self.sb = sb
		self.pcm = pcm
		self.scm = scm
		self.schedule_ts = schedule_ts
		self._display = _display

	def send_display_message(self, msg: BasicMessage):
		self._display.send(msg)

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
	def receive(self, msg):
		pass
	def reconfigure(self, config):
		pass