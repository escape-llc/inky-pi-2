from datetime import datetime, timedelta
import os
import unittest
import time
import logging
from python.task.application import Application, LoadScheduleFile, ScheduleFileData, StartEvent, StopEvent
from python.task.messages import QuitMessage
from python.task.timer_tick import BasicTimer, TickMessage

class DebugTimerTask(BasicTimer):
	def __init__(self, tasks, eventList, app):
		super().__init__(tasks)
		self.eventList = eventList
		self.app = app
		self.logger = logging.getLogger(__name__)
	def run(self):
		self.logger.info("DebugTimerTask thread starting.")
		try:
			for event in self.eventList:
				if self.stopped.is_set():
					return
				time.sleep(0.1)
				tick = event
				self.logger.info(f"Tick {tick.tick_number}: {tick.tick_ts}")
				for task in self.tasks:
					task.send(tick)
			self.app.send(QuitMessage())
		except Exception as e:
			self.logger.error(f"Exception in DebugTimerTask: {e}", exc_info=True)
		finally:
			self.logger.info("DebugTimerTask thread exiting.")

class TestApplication(unittest.TestCase):
	def create_timer_task(self, now, count=10):
		nowx = now.replace(second=0,microsecond=0)
		eventlist = [TickMessage(nowx + timedelta(minutes=ix), ix) for ix in range(count)];
		return eventlist

	@unittest.skip("Skipping start/stop test to avoid long waits during routine testing.")
	def test_start_and_stop_events(self):
		app = Application("TestApp")
		app.start()
		eventlist = self.create_timer_task(datetime.now(), 10)
		app.send(StartEvent(timerTask=lambda tasks: DebugTimerTask(tasks, eventlist, app)))
		# Wait for the started event to be set
		started = app.started.wait(timeout=1)
		self.assertTrue(started, "Application did not start as expected.")
		if started:
			# Wait for the stopped event to be set
			stopped = app.stopped.wait()
			self.assertTrue(stopped, "Application did not stop as expected.")

		app.join(timeout=1)
		self.assertFalse(app.is_alive(), "Application thread did not quit as expected.")
		appstopped = app.stopped.is_set()
		self.assertTrue(appstopped, "Application did not set stopped event as expected.")

	def test_start_configure_stop(self):
		app = Application("TestApp")
		app.start()
		eventlist = self.create_timer_task(datetime.now(), 60*24)
		app.send(StartEvent(timerTask=lambda tasks: DebugTimerTask(tasks, eventlist, app)))
		# Wait for the started event to be set
		started = app.started.wait(timeout=1)
		self.assertTrue(started, "Application did not start as expected.")
		if started:
			# Let it run for a short while
			test_file_path = os.path.abspath(__file__)
			test_directory = os.path.dirname(test_file_path)
			app.send(LoadScheduleFile(ScheduleFileData(filename=f"{test_directory}/schedules/test_schedule.json")))
			# Wait for the stopped event to be set
			stopped = app.stopped.wait()
			self.assertTrue(stopped, "Application did not stop as expected.")

		app.join(timeout=1)
		self.assertFalse(app.is_alive(), "Application thread did not quit as expected.")
		appstopped = app.stopped.is_set()
		self.assertTrue(appstopped, "Application did not set stopped event as expected.")

if __name__ == "__main__":
    unittest.main()