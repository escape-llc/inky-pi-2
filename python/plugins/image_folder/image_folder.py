from datetime import datetime, timedelta
import logging
import os
import requests

from PIL import Image, ImageOps, ImageFilter

from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ...task.messages import BasicMessage, FutureCompleted
from ...task.display import DisplayImage
from ...utils.image_utils import get_image
from ..plugin_base import PluginBase, PluginExecutionContext

def list_files_in_folder(folder_path):
	"""Return a list of image file paths in the given folder, excluding hidden files."""
	image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
	return [
		os.path.join(folder_path, fx)
		for fx in os.listdir(folder_path)
		if (
			os.path.isfile(os.path.join(folder_path, fx))
			and fx.lower().endswith(image_extensions)
			and not fx.startswith('.')
		)
	]

def grab_image(image_path, dimensions, pad_image, logger):
	"""Load an image from disk, auto-orient it, and resize to fit within the specified dimensions, preserving aspect ratio."""
	try:
		img = Image.open(image_path)
		img = ImageOps.exif_transpose(img)  # Correct orientation using EXIF
		img = ImageOps.contain(img, dimensions, Image.LANCZOS)

		if pad_image:
			bkg = ImageOps.fit(img, dimensions)
			bkg = bkg.filter(ImageFilter.BoxBlur(8))
			img_size = img.size
			bkg.paste(img, ((dimensions[0] - img_size[0]) // 2, (dimensions[1] - img_size[1]) // 2))
			img = bkg
		return img
	except Exception as e:
		logger.error(f"Error loading image from {image_path}: {e}")
		return None

class ImageFolder(PluginBase):
	TOKEN = "folder-list"
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		settings = ctx.sb.content.data

		folder_path = settings.get('folder')
		if not folder_path:
				raise RuntimeError("Folder path is required.")
		if not os.path.exists(folder_path):
				raise RuntimeError(f"Folder does not exist: {folder_path}")
		if not os.path.isdir(folder_path):
				raise RuntimeError(f"Path is not a directory: {folder_path}")

		def future_feed_download():
			image_files = list_files_in_folder(folder_path)
			return image_files
		ctx.future(self.TOKEN, future_feed_download)
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, ctx: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, FutureCompleted):
			if msg.token == self.TOKEN:
				if msg.is_success:
					self.logger.debug(f"{self.TOKEN} {msg.result}")
					ctx.pcm.save_state(msg.result)
					item = msg.result[0]
					self._dispatch_image(item, ctx)
				else:
					self.logger.error(f"'{self.name}' {self.TOKEN} {str(msg.error)}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")
		if isinstance(ctx.sb, PluginSchedule):
			state = ctx.pcm.load_state()
			if state is not None:
				state.pop(0)
				ctx.pcm.save_state(state)
				if len(state) > 0:
					item = state[0]
					self._dispatch_image(item, ctx)
	def _dispatch_image(self, item, ctx: PluginExecutionContext):
		settings = ctx.sb.content.data
		dimensions = ctx.resoluion
		display_settings = ctx.scm.load_settings("display")
		if display_settings.get("orientation") == "vertical":
				dimensions = dimensions[::-1]
		pad_image = settings.get('padImage', False)
		image = grab_image(item, dimensions, pad_image, self.logger)
		if image is not None:
			self.logger.debug(f"display {ctx.schedule_ts} ImageFolder")
			ctx.router.send("display", DisplayImage(f"{ctx.schedule_ts} ImageFolder", image))
			slideshow_minutes = settings.get("slideshowMinutes", None)
			if slideshow_minutes is not None:
				delta = timedelta(minutes=slideshow_minutes)
				wake_ts = ctx.schedule_ts + delta
				self.logger.debug(f"schedule_ts {ctx.schedule_ts} wake_ts {wake_ts}")
				ctx.alarm_clock(wake_ts)
