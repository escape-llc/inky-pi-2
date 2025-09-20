import logging
from PIL import Image

from ..task.basic_task import BasicTask
from ..task.messages import ExecuteMessage

class DisplayImage(ExecuteMessage):
	def __init__(self, title:str, img: Image):
		super().__init__()
		self.title = title
		self.img = img

class Display(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)

	def execute(self, msg: ExecuteMessage):
		# Handle display messages here
		self.logger.info(f"'{self.name}' received message: {msg}")

