from datetime import datetime, timedelta
import logging
import requests

from PIL import Image

from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ...task.messages import BasicMessage, FutureCompleted
from ...task.display import DisplayImage
from ...utils.image_utils import get_image
from ..plugin_base import PluginBase, PluginExecutionContext
from .constants import NEWSPAPERS

FREEDOM_FORUM_URL = "https://cdn.freedomforum.org/dfp/jpg{}/lg/{}.jpg"
class Newspaper(PluginBase):
	TOKEN = "newspaper-download"
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		settings = ctx.sb.content.data
		dimensions = ctx.resoluion
		schedule_ts = ctx.schedule_ts
		def future_feed_download():
			return self.generate_image(settings, dimensions, schedule_ts)
		ctx.future(self.TOKEN, future_feed_download)
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, pec: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, FutureCompleted):
			if msg.token == self.TOKEN:
				if msg.is_success:
					self.logger.debug(f"{self.TOKEN} {msg.result}")
					image = msg.result
					if image is not None:
						self.logger.debug(f"display {pec.schedule_ts} Newspaper")
						pec.router.send("display", DisplayImage(f"{pec.schedule_ts} Newspaper", image))
				else:
					self.logger.error(f"'{self.name}' {self.TOKEN} {str(msg.error)}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")
	def generate_image(self, settings, dimensions, schedule_ts:datetime):
		newspaper_slug = settings.get('slug')

		if not newspaper_slug:
			raise RuntimeError("Newspaper input not provided.")
		newspaper_slug = newspaper_slug.upper()

		# Get today's date
		today = schedule_ts

		# check the next day, then today, then prior day
		days = [today + timedelta(days=diff) for diff in [1,0,-1,-2]]

		image = None
		for date in days:
			image_url = FREEDOM_FORUM_URL.format(date.day, newspaper_slug)
			image = get_image(image_url)
			if image:
				logging.info(f"Found {newspaper_slug} front cover for {date.strftime('%Y-%m-%d')}")
				break

		if image:
			# expand height if newspaper is wider than resolution
			img_width, img_height = image.size
			desired_width, desired_height = dimensions

			img_ratio = img_width / img_height
			desired_ratio = desired_width / desired_height

			if img_ratio < desired_ratio:
				new_height =  int((img_width*desired_width) / desired_height)
				new_image = Image.new("RGB", (img_width, new_height), (255, 255, 255))
				new_image.paste(image, (0, 0))
				image = new_image
		else:
			raise RuntimeError("Newspaper front cover not found.")

		return image
