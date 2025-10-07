import logging
import threading
from datetime import datetime, timedelta

from ..model.configuration_manager import ConfigurationManager
from .messages import ConfigureNotify, StartEvent, StopEvent, QuitMessage, ConfigureOptions, ConfigureEvent
from .scheduler import Scheduler
from .display import Display, DisplaySettings
from .timer_tick import TimerTick
from .basic_task import BasicTask, ExecuteMessage, QuitMessage
from .message_router import MessageRouter, Route
from .telemetry_sink import TelemetrySink

class Application(BasicTask):
	def __init__(self, name = None, sink: TelemetrySink = None):
		super().__init__(name)
		self.sink = sink
		self.started = threading.Event()
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
		elif isinstance(msg, DisplaySettings):
			# STEP 3 configure scheduler (it also receives DisplaySettings)
			self.logger.info(f"'{self.name}' DisplaySettings {msg.name} {msg.width} {msg.height}.")
			configs = ConfigureEvent("scheduler", ConfigureOptions(cm=self.cm.duplicate()), self)
			self.scheduler.send(configs)
			pass
		elif isinstance(msg, ConfigureNotify):
			# STEP 4 start the timer if scheduler configured successfully
			self.logger.info(f"'{self.name}' ConfigureNotify {msg.token} {msg.error} {msg.content}.")
			if msg.error == True and self.sink:
				self.sink.send(msg)

			if msg.token == "scheduler":
				if msg.error == False:
					self.logger.info(f"'{self.name}' starting timer.")
					self.timer.start()
				else:
					self.logger.error(f"'{self.name}' Cannot start the timer; scheduler failed to initialize")
					self.logger.error(f"{msg.content}")
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
		self.cm = ConfigurationManager(
			root_path=msg.options.basePath if msg.options is not None else None,
			storage_path=msg.options.storagePath if msg.options is not None else None
			)
		if msg.options is not None and msg.options.hardReset:
			self.logger.info(f"'{self.name}' hard reset configuration.")
			self.cm.hard_reset()
		else:
			self.cm.ensure_folders()
		self.logger.info(f"'{self.name}' start tasks.")
		# STEP 0 assemble tasks and routes
		self.router = MessageRouter()
		self.display = Display("Display", self.router)
		self.scheduler = Scheduler("Scheduler", self.router)
		self.router.addRoute(Route("display", [self.display]))
		self.router.addRoute(Route("scheduler", [self.scheduler]))
		self.router.addRoute(Route("tick", [self.scheduler, self.display]))
		self.router.addRoute(Route("display-settings", [self, self.scheduler]))
		if self.sink is not None:
			self.router.addRoute(Route('telemetry', [self.sink]))
		# STEP 1 configure the Display task
		configd = ConfigureEvent("display", ConfigureOptions(cm=self.cm.duplicate()), self)
		self.display.send(configd)
		self.scheduler.start()
		self.display.start()
		# STEP 2 create but do not start timer
		self.timer = msg.timerTask(self.router) if msg.timerTask is not None else TimerTick(self.router, interval=60, align_to_minute=True)

	def _handleStop(self):
		if self.timer.is_alive():
			self.timer.stop()
			self.timer.join()
			self.logger.info("Timer stopped");
		self.scheduler.send(QuitMessage())
		self.scheduler.join()
		self.logger.info("Scheduler stopped");
		self.display.send(QuitMessage())
		self.display.join()
		self.logger.info("Display stopped");
