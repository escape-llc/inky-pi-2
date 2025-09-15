import threading
import logging
from datetime import datetime, timedelta
from .messages import ExecuteMessage

class TickMessage(ExecuteMessage):
	"""Message indicating a timer tick."""
	def __init__(self, tick_ts, tick_number):
		self.tick_ts = tick_ts
		self.tick_number = tick_number

class TimerTick(threading.Thread):
	def __init__(self, tasks, interval=60, align_to_minute=True):
		"""
		:param tasks: List of BasicTask instances to send TickMessage to.
		:param interval: Time in seconds between ticks.
		:param align_to_minute: If True, align first tick to the next minute.
		"""
		super().__init__()
		self.tasks = tasks
		self.interval = interval
		self.align_to_minute = align_to_minute
		self.tick_count = 0
		self.logger = logging.getLogger(__name__)
		self._stop_event = threading.Event()

	def run(self):
		self.logger.info("TimerTick thread starting.")
		try:
			if self.align_to_minute:
				self.logger.info("Aligning to next minute.")
				now = datetime.now()
				next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
				sleep_seconds = (next_minute - now).total_seconds()
				tick = TickMessage(now, self.tick_count)
				self.logger.info(f"Pre-align Tick {tick.tick_number}: {tick.tick_ts}")
				self.tick_count += 1
				for task in self.tasks:
					task.send(tick)
				self.logger.debug(f"Sleeping for {sleep_seconds:.2f} seconds to align to minute {next_minute}.")
				if self._stop_event.wait(timeout=sleep_seconds):
					return  # Exit if stop event is set

			while not self._stop_event.is_set():
				now = datetime.now()
				tick = TickMessage(now, self.tick_count)
				self.tick_count += 1
				self.logger.info(f"Tick {tick.tick_number}: {tick.tick_ts}")
				for task in self.tasks:
					task.send(tick)
				# Align to next interval boundary
				if self.interval >= 60:
					overage = now - now.replace(second=0, microsecond=0)
					sleep_time = max(0, self.interval - overage.total_seconds())
					self.logger.debug(f"Sleeping for {sleep_time:.4f} seconds (interval={self.interval}, now={now}).")
					if self._stop_event.wait(timeout=sleep_time):
						break
				elif self.interval >= 1:
					overage = now - now.replace(microsecond=0)
					sleep_time = max(0, self.interval - overage.total_seconds())
					self.logger.debug(f"Sleeping for {sleep_time:.4f} seconds (interval={self.interval}, now={now}).")
					if self._stop_event.wait(timeout=sleep_time):
						break
				else:
					self.logger.debug(f"Sleeping for {self.interval:.2f}.")
					if self._stop_event.wait(timeout=self.interval):
						break

		except Exception as e:
			self.logger.error(f"Exception in TimerTick thread: {e}", exc_info=True)
		finally:
			self.logger.info("TimerTick thread stopped.")

	def stop(self):
		self._stop_event.set()
		self.logger.info("Stopping TimerTick thread.")
