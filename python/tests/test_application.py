import os
import unittest
import time
from python.task.application import Application, LoadScheduleFile, ScheduleFileData, StartEvent, StopEvent
from python.task.messages import QuitMessage

class TestApplication(unittest.TestCase):
	@unittest.skip("Skipping start/stop test to avoid long waits during routine testing.")
	def test_start_and_stop_events(self):
		app = Application("TestApp")
		app.start()
		app.send(StartEvent(None))
		# Wait for the started event to be set
		started = app.started.wait(timeout=1)
		self.assertTrue(started, "Application did not start as expected.")
		if started:
			# Let it run for a short while
			time.sleep(70)
			app.send(StopEvent(None))
			# Wait for the stopped event to be set
			stopped = app.stopped.wait(timeout=1)
			self.assertTrue(stopped, "Application did not stop as expected.")

		app.send(QuitMessage())
		app.join(timeout=1)
		self.assertFalse(app.is_alive(), "Application thread did not quit as expected.")

	def test_start_configure_stop(self):
		app = Application("TestApp")
		app.start()
		app.send(StartEvent(None))
		# Wait for the started event to be set
		started = app.started.wait(timeout=1)
		self.assertTrue(started, "Application did not start as expected.")
		if started:
			# Let it run for a short while
			test_file_path = os.path.abspath(__file__)
			test_directory = os.path.dirname(test_file_path)
			app.send(LoadScheduleFile(ScheduleFileData(filename=f"{test_directory}/schedules/test_schedule.json")))
			time.sleep(70)
			app.send(StopEvent(None))
			# Wait for the stopped event to be set
			stopped = app.stopped.wait(timeout=1)
			self.assertTrue(stopped, "Application did not stop as expected.")

		app.send(QuitMessage())
		app.join(timeout=1)
		self.assertFalse(app.is_alive(), "Application thread did not quit as expected.")

if __name__ == "__main__":
    unittest.main()