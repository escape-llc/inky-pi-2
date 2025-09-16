from abc import abstractmethod
import threading
import queue
import logging

from .messages import BasicMessage, ExecuteMessage, QuitMessage

class BasicTask(threading.Thread):
	def __init__(self, name=None):
		super().__init__()
		self.msg_queue = queue.Queue()
		self.name = name or self.__class__.__name__
		self.stopped = threading.Event()
		self.logger = logging.getLogger(__name__)

	def run(self):
		self.logger.info(f"'{self.name}' start.")
		while not self.stopped.is_set():
			msg = self.msg_queue.get()
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
		self.logger.info(f"'{self.name}' end.")

	@abstractmethod
	def quitMsg(self, msg: QuitMessage):
		self.msg_queue.shutdown(immediate=True)
		self.stopped.set()
		self.logger.info(f"'{self.name}' Quit.")

	@abstractmethod
	def execute(self, msg: ExecuteMessage):
		"""Abstract method to execute a message."""
		pass

	def send(self, msg: BasicMessage):
		if self.stopped.is_set():
			raise ValueError("Cannot send message to stopped task.")
		self.msg_queue.put(msg)