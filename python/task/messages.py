from typing import Protocol
from typing import Generic, TypeVar
from datetime import datetime

from ..model.configuration_manager import ConfigurationManager

T = TypeVar('T')

class BasicMessage:
	"""Base class for all messages."""
	def __init__(self, timestamp: datetime = datetime.now()):
		self.timestamp = timestamp

class MessageSink(Protocol):
	def send(self, msg: BasicMessage):
		pass

class QuitMessage(BasicMessage):
	"""Message to signal the thread to quit."""
	def __init__(self, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)

class ExecuteMessage(BasicMessage):
	"""Message to execute a command."""
	def __init__(self, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)

class ExecuteMessageWithContent(ExecuteMessage, Generic[T]):
	"""Message to execute a command with content."""
	def __init__(self, content: T, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)
		self.content = content

class StartOptions:
	"""Options for starting the application."""
	def __init__(self, basePath: str = None, storagePath: str = None, hardReset: bool = False):
		self.basePath = basePath
		self.storagePath = storagePath
		self.hardReset = hardReset
class StartEvent(ExecuteMessage):
	"""Event to start the application with given options and timer task."""
	def __init__(self, options: StartOptions = None, timerTask: callable = None, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)
		self.options = options
		self.timerTask = timerTask

class StopEvent(ExecuteMessage):
	"""Event to stop the application."""
	def __init__(self, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)

class ConfigureOptions:
	"""Options for configuring tasks."""
	def __init__(self, cm: ConfigurationManager):
		if cm is None:
			raise ValueError("cm cannot be None")
		self.cm = cm

class ConfigureEvent(ExecuteMessageWithContent[ConfigureOptions]):
	"""Event to configure tasks with given options."""
	def __init__(self, token: str, content = None, notifyTo: MessageSink = None, timestamp: datetime = datetime.now()):
		super().__init__(content, timestamp)
		self.token = token
		self.notifyTo = notifyTo

	def notify(self, error: bool = False, content = None):
		if self.notifyTo is not None:
			self.notifyTo.send(ConfigureNotify(self.token, error, content))

class ConfigureNotify(ExecuteMessage):
	def __init__(self, token: str, error: bool = False, content = None, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)
		self.token = token
		self.error = error
		self.content = content

class FutureCompleted(ExecuteMessage):
	def __init__(self, plugin_name: str, token: str, result, error = None, timestamp: datetime = datetime.now()):
		super().__init__(timestamp)
		self.plugin_name = plugin_name
		self.token = token
		self.result = result
		self.error = error
		self.is_success = error is None
