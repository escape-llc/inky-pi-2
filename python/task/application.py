import logging
import threading
from datetime import datetime, timedelta

from python.model.schedule_loader import ScheduleLoader
from python.task.timer_tick import TickMessage, TimerTick
from .basic_task import BasicTask, ExecuteMessage, QuitMessage, BasicMessage

class StartEvent(ExecuteMessage):
	def __init__(self, timerTask: callable = None):
		super().__init__(content=None)
		self.timerTask = timerTask

class StopEvent(ExecuteMessage):
	pass

class ScheduleFileData:
	def __init__(self, filename: str):
		self.filename = filename
class LoadScheduleFile(ExecuteMessage[ScheduleFileData]):
	def __init__(self, content=None):
		super().__init__(content)

class Scheduler(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)
		self.schedule = None
		self.state = 'uninitialized'

	def execute(self, msg: ExecuteMessage):
		# Handle scheduling messages here
		self.logger.info(f"Scheduler '{self.name}' received message: {msg}")
		if isinstance(msg, LoadScheduleFile):
			schedule_file = msg.content.filename
			self.logger.info(f"Loading schedule file: {schedule_file}")
			self.schedule = ScheduleLoader.loadFile(schedule_file)
			outcome = self.schedule.validate()
			self.logger.info(f"schedule.validate: {outcome}")
			self.state = 'loaded' if outcome == None else 'error'
		elif isinstance(msg, TickMessage):
			# Perform scheduled tasks
			if self.state != 'loaded':
				self.logger.warning(f"Scheduler '{self.name}' waiting for configuration. Current state: {self.state}")
				return
			if self.schedule is None:
				self.logger.error(f"Scheduler '{self.name}' has no schedule loaded.")
				return
			# for now; at some point there is another level of mapping from day->schedule
			now = datetime.now()
			self.schedule.set_date_controller(lambda: now)
			current = self.schedule.current(msg.tick_ts)
			self.logger.info(f"Current scheduled item at {msg.tick_ts}: {current}")
			if current:
				# Here you would trigger the actual task associated with the current schedule item
				self.logger.info(f"Executing scheduled item: {current.title}")
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

	def execute(self, msg: ExecuteMessage):
		# Handle Start and Stop events
		if isinstance(msg, StartEvent):
			try:
				self._handleStart(msg)
				self.logger.info(f"Application '{self.name}' started.")
				self.started.set()
			except Exception as e:
				self.logger.error(f"Failed to start application '{self.name}': {e}", exc_info=True)
				self.stopped.set()
		elif isinstance(msg, StopEvent):
			try:
				self._handleStop()
				self.logger.info(f"Application '{self.name}' stopped.")
			except Exception as e:
				self.logger.error(f"Failed to stop application '{self.name}': {e}", exc_info=True)
			finally:
				self.stopped.set()
		elif isinstance(msg, LoadScheduleFile):
			if self.started.is_set() and not self.stopped.is_set():
				if hasattr(self, 'scheduler') and self.scheduler:
					self.scheduler.send(msg)
				else:
					self.logger.warning(f"Application '{self.name}' cannot load schedule; scheduler not initialized.")
		else:
			self.logger.warning(f"Application '{self.name}' received unknown message: {msg}")

	def quitMsg(self, msg: QuitMessage):
		self.logger.info(f"Application '{self.name}' quitting.")
		if self.started.is_set() and not self.stopped.is_set():
			try:
				self._handleStop()
				self.logger.info(f"Application '{self.name}' stopped during quit.")
			except Exception as e:
				self.logger.error(f"Failed to stop application '{self.name}' during quit: {e}", exc_info=True)
			finally:
				self.stopped.set()

	def _handleStart(self, msg: StartEvent):
		self.scheduler = Scheduler("Scheduler")
		self.display = Display("Display")
		self.scheduler.start()
		self.display.start()
		self.timer = msg.timerTask([self.scheduler, self.display]) if msg.timerTask is not None else TimerTick([self.scheduler, self.display], interval=1, align_to_minute=True)
		self.timer.start()
		pass

	def _handleStop(self):
		self.timer.stop()
		self.timer.join(timeout=5)
		self.scheduler.send(QuitMessage())
		self.scheduler.join(timeout=5)
		self.display.send(QuitMessage())
		self.display.join(timeout=5)
		pass