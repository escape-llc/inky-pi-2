import unittest
import logging
from ..task.basic_task import BasicTask
from ..task.messages import ExecuteMessage, ExecuteMessageWithContent, QuitMessage

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
		task.send(ExecuteMessageWithContent("Hello"))
		task.send(QuitMessage())
		task.join()
		self.assertFalse(task.is_alive())
		self.assertEqual(len(task.received), 1, 'Should have received 1 messages')
		self.assertEqual(task.received[0], "Hello", 'Message content mismatch')

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