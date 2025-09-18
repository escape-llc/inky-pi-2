import logging
import threading
from datetime import datetime, timedelta

from ..model.configuration_manager import ConfigurationManager
from .messages import StartEvent, StopEvent, QuitMessage, ConfigureOptions, ConfigureEvent
from .scheduler import Scheduler
from .timer_tick import TimerTick
from .basic_task import BasicTask, ExecuteMessage, QuitMessage

class Display(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)

	def execute(self, msg: ExecuteMessage):
		# Handle display messages here
		self.logger.info(f"'{self.name}' received message: {msg}")

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
#		elif isinstance(msg, ConfigureEvent):
#			if self.started.is_set() and not self.stopped.is_set():
#				if hasattr(self, 'scheduler') and self.scheduler:
#					self.scheduler.send(msg)
#				else:
#					self.logger.warning(f"'{self.name}' cannot load schedule; scheduler not initialized.")
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
				super().quitMsg(msg)
		else:
			super().quitMsg(msg)

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
