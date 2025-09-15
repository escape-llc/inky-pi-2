from typing import Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class BasicMessage:
	"""Base class for all messages."""
	def __init__(self):
		self.timestamp = datetime.now()

class QuitMessage(BasicMessage):
	"""Message to signal the thread to quit."""
	def __init__(self):
		super().__init__()

class ExecuteMessage(BasicMessage, Generic[T]):
	"""Message to execute a command."""
	def __init__(self, content: T):
		super().__init__()
		self.content = content