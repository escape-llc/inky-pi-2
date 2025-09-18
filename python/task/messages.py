from typing import Generic, TypeVar
from datetime import datetime

from ..model.configuration_manager import ConfigurationManager

T = TypeVar('T')

class BasicMessage:
	"""Base class for all messages."""
	def __init__(self):
		self.timestamp = datetime.now()

class QuitMessage(BasicMessage):
	"""Message to signal the thread to quit."""
	def __init__(self):
		super().__init__()

class ExecuteMessage(BasicMessage):
	"""Message to execute a command."""
	def __init__(self):
		super().__init__()

class ExecuteMessageWithContent(ExecuteMessage, Generic[T]):
	"""Message to execute a command with content."""
	def __init__(self, content: T):
		super().__init__()
		self.content = content

class StartOptions:
	"""Options for starting the application."""
	def __init__(self, basePath:str = None, storagePath:str = None, hardReset:bool = False):
		self.basePath = basePath
		self.storagePath = storagePath
		self.hardReset = hardReset
class StartEvent(ExecuteMessage):
	"""Event to start the application with given options and timer task."""
	def __init__(self, options:StartOptions = None, timerTask: callable = None):
		super().__init__()
		self.options = options
		self.timerTask = timerTask

class StopEvent(ExecuteMessage):
	"""Event to stop the application."""
	def __init__(self):
		super().__init__()

class ConfigureOptions:
	"""Options for configuring tasks."""
	def __init__(self, cm: ConfigurationManager):
		if cm is None:
			raise ValueError("cm cannot be None")
		self.cm = cm
class ConfigureEvent(ExecuteMessageWithContent[ConfigureOptions]):
	"""Event to configure tasks with given options."""
	def __init__(self, content=None):
		super().__init__(content)
