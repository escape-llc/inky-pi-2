from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from .timer_tick import TickMessage

class Timer(ABC):
	def __init__(self, tick: TickMessage, delta: timedelta):
		self.tick = tick
		self.delta = delta
		self.expiration_time = tick.tick_ts + delta
		self.triggered = False
	def trigger(self, tick: TickMessage) -> bool:
		if self.triggered:
			return True
		if tick.tick_ts >= self.expiration_time:
			try:
				self.timer_expired()
				return True
			finally:
				self.triggered = True
		return False
	def was_triggered(self) -> bool:
		return self.triggered
	@abstractmethod
	def timer_expired(self):
		pass