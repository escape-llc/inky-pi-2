import threading
import queue
import logging

from .messages import MessageSink, BasicMessage, ExecuteMessage, QuitMessage

class BasicTask(threading.Thread, MessageSink):
	"""Task that runs in its own thread and processes messages."""
	def __init__(self, name=None):
		super().__init__()
		self.msg_queue = queue.Queue()
		self.name = name or self.__class__.__name__
		self.stopped = threading.Event()
		self.logger = logging.getLogger(__name__)

	def _dispatch(self, msg):
		if isinstance(msg, QuitMessage):
			try:
				self.quitMsg(msg)
			except Exception as e:
				self.logger.error(f"quit.unhandled '{self.name}': {e}", exc_info=True)
		elif isinstance(msg, ExecuteMessage):
			try:
				self.execute(msg)
			except Exception as e:
				self.logger.error(f"execute.unhandled '{self.name}': {e}", exc_info=True)
		# Optionally handle other message types
		else:
			self.logger.warning(f"'{self.name}' received unknown message type: {msg}")

	def run(self):
		self.logger.info(f"'{self.name}' start.")
		running = True
		while running:
			try:
				msg = self.msg_queue.get()
				self._dispatch(msg)
				self.msg_queue.task_done()
			except queue.ShutDown:
				self.logger.debug(f"Queue shut down")
				running = False
			except Exception as e:
				self.msg_queue.task_done()
				self.logger.error(f"'{self.name} unhandled", e)
#		self.logger.info(f"'{self.name}' stopped {self.msg_queue.qsize()}.")
#		self.stopped.set()
		self.logger.info(f"'{self.name}' end {self.msg_queue.qsize()}.")

	def quitMsg(self, msg: QuitMessage):
		"""Handles the QuitMessage to gracefully stop the task."""
		self.stopped.set()
		self.logger.info(f"'{self.name}' Quit.")

	def execute(self, msg: ExecuteMessage):
		"""Abstract method to execute a message."""
		pass

	def send(self, msg: BasicMessage):
		if self.msg_queue.is_shutdown:
			raise ValueError("Cannot send message to stopped task.")
		self.msg_queue.put(msg)
		if isinstance(msg, QuitMessage):
			self.msg_queue.shutdown()