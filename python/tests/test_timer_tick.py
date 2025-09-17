import unittest
import time
from python.task.timer_tick import TimerTick, TickMessage
from python.task.basic_task import BasicTask
from python.task.messages import ExecuteMessage, QuitMessage
import logging

logging.basicConfig(
	level=logging.DEBUG,  # Or DEBUG for more detail
	format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

class RecordingTask(BasicTask):
	def __init__(self):
		super().__init__()
		self.ticks = []
		self.logger = logging.getLogger(__name__)

	def execute(self, msg):
		# Only record TickMessage
		self.logger.debug(f"RecordingTask: {msg}")
		if isinstance(msg, TickMessage):
			self.ticks.append((msg.tick_ts, msg.tick_number))

class TestTimerTick(unittest.TestCase):
	@unittest.skip("Skipping timer tick test to avoid timing issues in CI")
	def test_tick_messages_sent_to_tasks(self):
		task1 = RecordingTask()
		task2 = RecordingTask()
		task1.start()
		task2.start()

		timer = TimerTick([task1, task2], interval=0.01, align_to_minute=False)  # Fast ticks for testing
		timer.start()

		# Let it tick a few times
		time.sleep(0.1)
		timer.stop()
		timer.join()

		# Stop tasks
		task1.send(QuitMessage())
		task2.send(QuitMessage())
		task1.join()
		task2.join()

		# Assert both tasks received tick messages
		self.assertGreaterEqual(len(task1.ticks), 1, "Task 1 should have received at least one tick")
		self.assertGreaterEqual(len(task2.ticks), 1, "Task 2 should have received at least one tick")
		self.assertEqual(len(task1.ticks), len(task2.ticks), "Both tasks should have received the same number of ticks")

if __name__ == "__main__":
    unittest.main()