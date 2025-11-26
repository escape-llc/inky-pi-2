from datetime import datetime, timedelta
import unittest
import time
import logging

from python.task.timer_tick import TickMessage

from ..task.timer import Timer

logging.basicConfig(
	level=logging.DEBUG,  # Or DEBUG for more detail
	format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

class TestTimer(Timer):
	def __init__(self, tick, delta):
		super().__init__(tick, delta)
		self.expired = False
	def timer_expired(self):
		self.expired = True

class ExceptionTimer(Timer):
	def __init__(self, tick, delta):
		super().__init__(tick, delta)
		self.expired = False
	def timer_expired(self):
		raise Exception("Timer deliberate exception for testing")

class TestTimerTick(unittest.TestCase):
	def test_timer_expires(self):
		initial_tick = TickMessage(datetime.now(), 0)
		timer = TestTimer(initial_tick, timedelta(seconds=2))
		self.assertFalse(timer.was_triggered())
		next_tick = TickMessage(initial_tick.tick_ts + timedelta(seconds=1), 1)
		self.assertFalse(timer.trigger(next_tick))
		next_tick = TickMessage(initial_tick.tick_ts + timedelta(seconds=2), 2)
		self.assertTrue(timer.trigger(next_tick))
		self.assertTrue(timer.was_triggered())
		self.assertTrue(timer.expired)
	def test_timer_throws(self):
		initial_tick = TickMessage(datetime.now(), 0)
		timer = ExceptionTimer(initial_tick, timedelta(seconds=2))
		self.assertFalse(timer.was_triggered())
		next_tick = TickMessage(initial_tick.tick_ts + timedelta(seconds=1), 1)
		self.assertFalse(timer.trigger(next_tick))
		next_tick = TickMessage(initial_tick.tick_ts + timedelta(seconds=2), 2)
		try:
			timer.trigger(next_tick)
		except Exception:
			self.assertTrue(timer.was_triggered())
			self.assertFalse(timer.expired)

if __name__ == "__main__":
	unittest.main()