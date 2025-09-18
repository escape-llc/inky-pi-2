import logging
import threading
from datetime import datetime, timedelta

from ..model.configuration_manager import ConfigurationManager
from ..model.schedule import MasterSchedule, Schedule
from .messages import ExecuteMessageWithContent
from .timer_tick import TickMessage, TimerTick
from .basic_task import BasicTask, ExecuteMessage, QuitMessage

class StartOptions:
	def __init__(self, basePath:str = None, storagePath:str = None, hardReset:bool = False):
		self.basePath = basePath
		self.storagePath = storagePath
		self.hardReset = hardReset

class StartEvent(ExecuteMessage):
	def __init__(self, options:StartOptions = None, timerTask: callable = None):
		super().__init__()
		self.options = options
		self.timerTask = timerTask

class StopEvent(ExecuteMessage):
	def __init__(self):
		super().__init__()

class ConfigureOptions:
	def __init__(self, cm: ConfigurationManager):
		if cm is None:
			raise ValueError("cm cannot be None")
		self.cm = cm
class ConfigureEvent(ExecuteMessageWithContent[ConfigureOptions]):
	def __init__(self, content=None):
		super().__init__(content)

class Scheduler(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)
		self.schedules = []
		self.master_schedule:MasterSchedule = None
		self.cm:ConfigurationManager = None
		self.plugin_info = None
		self.plugin_map = None
		self.state = 'uninitialized'

	def execute(self, msg: ExecuteMessage):
		# Handle scheduling messages here
		self.logger.info(f"'{self.name}' received message: {msg}")
		if isinstance(msg, ConfigureEvent):
			self.cm = msg.content.cm
			try:
				plugin_info = self.cm.enum_plugins()
				plugins = self.cm.load_plugins(plugin_info)
				self.logger.info(f"Plugins loaded: {list(plugins.keys())}")
				self.plugin_info = plugin_info
				self.plugin_map = plugins
				sm = self.cm.schedule_manager()
				schedule_info = sm.load()
				sm.validate(schedule_info)
				self.master_schedule = schedule_info.get("master", None)
				self.schedules = schedule_info.get("schedules", [])
				self.logger.info(f"schedule loaded")
				self.state = 'loaded'
			except Exception as e:
				self.logger.error(f"Failed to load/validate schedules: {e}", exc_info=True)
				self.state = 'error'
		elif isinstance(msg, TickMessage):
			# Perform scheduled tasks
			if self.state != 'loaded':
				self.logger.warning(f"'{self.name}' waiting for configuration. Current state: {self.state}")
				return
			if self.master_schedule is None:
				self.logger.error(f"'{self.name}' has no schedule loaded.")
				return
			# for now; at some point there is another level of mapping from day->schedule
			now = datetime.now()
			for schedule in self.schedules:
				info = schedule.get("info", None)
				if info is not None and isinstance(info, Schedule):
					info.set_date_controller(lambda: msg.tick_ts)
					break
			current = self.master_schedule.evaluate(msg.tick_ts)
			self.logger.info(f"Current schedule {msg.tick_ts}[{msg.tick_number}]: {current}")
			if current:
				# Here you would trigger the actual task associated with the current schedule item
				self.logger.info(f"Selecting schedule: {current.name} ({current.schedule})")
				schedule = next((s for s in self.schedules if s.get("name", None) and s["name"] == current.schedule), None)
				if schedule and "info" in schedule and isinstance(schedule["info"], Schedule):
					# Execute the schedule's tasks
					target:Schedule = schedule["info"]
					timeslot = target.current(msg.tick_ts)
					self.logger.info(f"Current slot {timeslot}")
					if timeslot:
						self.logger.info(f"Selecting slot '{timeslot.title}'")
						# Placeholder for actual task execution logic
						if self.plugin_map.get(timeslot.plugin_name, None):
							self.logger.info(f"Executing plugin '{timeslot.plugin_name}' with args {timeslot.content}")
							# Here you would call the plugin's execute method or similar
							plugin = self.plugin_map[timeslot.plugin_name]
							try:
								plugin.execute(timeslot.content)
							except Exception as e:
								self.logger.error(f"Error executing plugin '{timeslot.plugin_name}': {e}", exc_info=True)
						else:
							self.logger.error(f"Plugin '{timeslot.plugin_name}' not found.")
			pass

class Display(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)

	def execute(self, msg: ExecuteMessage):
		# Handle display messages here
		self.logger.info(f"Display '{self.name}' received message: {msg}")

class Application(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.started = threading.Event()
		self.stopped = threading.Event()
		self.cm:ConfigurationManager = None

	def execute(self, msg: ExecuteMessage):
		# Handle Start and Stop events
		if isinstance(msg, StartEvent):
			try:
				self._handleStart(msg)
				self.logger.info(f"'{self.name}' started.")
				self.started.set()
			except Exception as e:
				self.logger.error(f"Failed to start '{self.name}': {e}", exc_info=True)
				self.stopped.set()
		elif isinstance(msg, StopEvent):
			try:
				self._handleStop()
			except Exception as e:
				self.logger.error(f"Failed to stop '{self.name}': {e}", exc_info=True)
			finally:
				self.stopped.set()
				self.logger.info(f"'{self.name}' stopped.")
		elif isinstance(msg, ConfigureEvent):
			if self.started.is_set() and not self.stopped.is_set():
				if hasattr(self, 'scheduler') and self.scheduler:
					self.scheduler.send(msg)
				else:
					self.logger.warning(f"'{self.name}' cannot load schedule; scheduler not initialized.")
		else:
			self.logger.warning(f"'{self.name}' received unknown message: {msg}")

	def quitMsg(self, msg: QuitMessage):
		self.logger.info(f"'{self.name}' quitting.")
		if self.started.is_set() and not self.stopped.is_set():
			try:
				self._handleStop()
				self.logger.info(f"'{self.name}' stopped during quit.")
			except Exception as e:
				self.logger.error(f"Failed to stop '{self.name}' during quit: {e}", exc_info=True)
			finally:
				self.stopped.set()

	def _handleStart(self, msg: StartEvent):
		if msg.options is not None:
			self.logger.info(f"'{self.name}' basePath: {msg.options.basePath}, storagePath: {msg.options.storagePath}")
		self.cm = ConfigurationManager(root_path=msg.options.basePath if msg.options is not None else None, storage_path=msg.options.storagePath if msg.options is not None else None)
		if msg.options is not None and msg.options.hardReset:
			self.logger.info(f"'{self.name}' hard reset configuration.")
			self.cm.hard_reset()
		else:
			self.cm.ensure_folders()
		self.logger.info(f"'{self.name}' start tasks.")
		self.scheduler = Scheduler("Scheduler")
		self.display = Display("Display")
		configure = ConfigureEvent(ConfigureOptions(cm=ConfigurationManager(root_path=self.cm.ROOT_PATH, storage_path=self.cm.STORAGE_PATH)))
		self.scheduler.send(configure)
		configure2 = ConfigureEvent(ConfigureOptions(cm=ConfigurationManager(root_path=self.cm.ROOT_PATH, storage_path=self.cm.STORAGE_PATH)))
		self.display.send(configure2)
		self.scheduler.start()
		self.display.start()
		self.timer = msg.timerTask([self.scheduler, self.display]) if msg.timerTask is not None else TimerTick([self.scheduler, self.display], interval=1, align_to_minute=True)
		self.timer.start()

	def _handleStop(self):
		self.timer.stop()
		self.timer.join(timeout=5)
		self.scheduler.send(QuitMessage())
		self.scheduler.join(timeout=5)
		self.display.send(QuitMessage())
		self.display.join(timeout=5)
