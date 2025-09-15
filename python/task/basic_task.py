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
		self._running = True
		self.logger = logging.getLogger(__name__)

	def run(self):
		self.logger.info(f"'{self.name}' starting.")
		while self._running:
			msg = self.msg_queue.get()
			if isinstance(msg, QuitMessage):
				self._running = False
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

	@abstractmethod
	def quitMsg(self, msg: QuitMessage):
		self.logger.info(f"'{self.name}' Quit.")
		pass

	@abstractmethod
	def execute(self, msg: ExecuteMessage):
		"""Abstract method to execute a message."""
		pass

	def send(self, msg: BasicMessage):
		self.msg_queue.put(msg)