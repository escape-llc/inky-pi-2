import unittest
from python.task.basic_task import BasicTask
from python.task.messages import ExecuteMessage, QuitMessage

class RecordingTask(BasicTask):
	def __init__(self):
		super().__init__()
		self.received = []

	def execute(self, msg: ExecuteMessage):
		self.received.append(msg.content)

class TestBasicTask(unittest.TestCase):
	def test_execute_message(self):
		task = RecordingTask()
		task.start()
		task.send(ExecuteMessage("Hello"))
		task.send(QuitMessage())
		task.join()
		self.assertFalse(task.is_alive())

	def test_quit_message_stops_thread(self):
		task = RecordingTask()
		task.start()
		task.send(QuitMessage())
		task.join(timeout=1)
		self.assertFalse(task.is_alive())
		self.assertEqual(task.received, [])

	# Add more tests as needed

if __name__ == "__main__":
	unittest.main()