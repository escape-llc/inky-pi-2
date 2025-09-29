from abc import abstractmethod
import datetime

from ..model.configuration_manager import PluginConfigurationManager, SettingsConfigurationManager
from ..model.schedule import SchedulableBase
from ..task.active_plugin import ActivePlugin
from ..task.message_router import MessageRouter
from ..task.messages import BasicMessage

class PluginExecutionContext:
	def __init__(self, sb: SchedulableBase, scm: SettingsConfigurationManager, pcm: PluginConfigurationManager, ap:ActivePlugin, resolution, schedule_ts: datetime, router:MessageRouter):
		if sb is None:
			raise ValueError("sb is None")
		if scm is None:
			raise ValueError("scm is None")
		if pcm is None:
			raise ValueError("pcm is None")
		if ap is None:
			raise ValueError("ap is None")
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
		self._ap = ap

	def future(self, token:str, cx:callable):
		self._ap.future(token,cx)
	def alarm_clock(self, wake_up_ts:datetime):
		self._ap.alarm_clock(wake_up_ts)

class PluginBase:
	def __init__(self, id, name):
		self.id = id
		self.name = name
	@abstractmethod
	def timeslot_start(self, pec: PluginExecutionContext):
		pass
	@abstractmethod
	def timeslot_end(self, pec: PluginExecutionContext):
		pass
	@abstractmethod
	def schedule(self, pec: PluginExecutionContext):
		pass
	@abstractmethod
	def receive(self, pec: PluginExecutionContext, msg: BasicMessage):
		pass
	@abstractmethod
	def reconfigure(self, pec: PluginExecutionContext, config):
		pass