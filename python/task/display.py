import logging
from PIL import Image

from ..display.mock_display import MockDisplay
from ..display.display_base import DisplayBase
from ..model.configuration_manager import ConfigurationManager
from ..task.basic_task import BasicTask
from ..task.messages import ConfigureEvent, ExecuteMessage

class DisplayImage(ExecuteMessage):
	def __init__(self, title:str, img: Image):
		super().__init__()
		self.title = title
		self.img = img

class Display(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.cm:ConfigurationManager = None
		self.display:DisplayBase = None
		self.logger = logging.getLogger(__name__)

	def execute(self, msg: ExecuteMessage):
		# Handle display messages here
		self.logger.info(f"'{self.name}' received message: {msg}")
		if isinstance(msg, ConfigureEvent):
			self.cm = msg.content.cm
			settings = self.cm.settings_manager()
			self.display_settings = settings.load_settings("display")
			self.display = MockDisplay("mock")
			self.display.initialize(self.cm)
		elif isinstance(msg, DisplayImage):
			self.logger.info(f"Display {msg.title}")
			if self.display is None:
				self.logger.error("No driver is loaded")
				return
			self.display.render(msg.img)
			pass

