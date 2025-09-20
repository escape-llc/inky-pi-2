from abc import abstractmethod
import logging
from PIL import Image

from ..model.configuration_manager import ConfigurationManager

class DisplayBase:
	def __init__(self, name: str):
		self.name = name
	@abstractmethod
	def initialize(self, cm: ConfigurationManager):
		pass
	@abstractmethod
	def render(self, img: Image):
		pass
