from datetime import timedelta
import logging
import requests

from PIL import Image, ImageDraw, ImageFont

from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ...task.messages import BasicMessage, FutureCompleted
from ...task.display import DisplayImage
from ..plugin_base import PluginBase, PluginExecutionContext
from .comic_parser import COMICS, get_items


class Comic(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		ctx.pcm.delete_state()
		data = ctx.sb.content.data
		comic = data.get("comic")
		def future_feed_download():
			return get_items(comic)
		if comic is not None:
			ctx.future("feed-download", future_feed_download)
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, pec: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, FutureCompleted):
			if msg.token == "feed-download":
				if msg.is_success:
					self.logger.debug(f"feed-download {msg.result}")
					pec.pcm.save_state(msg.result)
					item = msg.result[0]
					def future_feed_image():
						return self._generate_image(pec, item)
					pec.future("feed-image", future_feed_image)
				else:
					self.logger.error(f"feed-download {str(msg.error)}")
			elif msg.token == "feed-image":
				if msg.is_success:
					self.logger.debug(f"feed-image {msg.result}")
					image = msg.result.get("image",None)
					if image is not None:
						data = pec.sb.content.data
						comic = data.get("comic")
						self.logger.debug(f"display {pec.schedule_ts} {comic}")
						pec.router.send("display", DisplayImage(f"{pec.schedule_ts} {comic}", image))
					state = pec.pcm.load_state()
					# remove this item
					info = msg.result.get("info")
					new_state =[itx for itx in state if itx["image_url"] != info["image_url"]]
					pec.pcm.save_state(new_state)
					if len(new_state) > 0:
						settings = pec.sb.content.data
						slideshow_minutes = settings.get("slideshowMinutes", None)
						if slideshow_minutes is not None:
							delta = timedelta(minutes=slideshow_minutes)
							wake_ts = pec.schedule_ts + delta
							self.logger.debug(f"schedule_ts {pec.schedule_ts} wake_ts {wake_ts}")
							pec.alarm_clock(wake_ts)
				else:
					self.logger.error(f"feed-image {str(msg.error)}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")
		if isinstance(ctx.sb, PluginSchedule):
			state = ctx.pcm.load_state()
			if state is not None and len(state) > 0:
				item = state[0]
				def future_feed_image():
					return self._generate_image(ctx, item)
				ctx.future("feed-image", future_feed_image)

	def _generate_image(self, ctx: PluginExecutionContext, item):
		display_settings = ctx.scm.load_settings("display")
		dimensions = ctx.resoluion
		settings = ctx.sb.content.data
		is_caption = settings.get("titleCaption") == "true"
		caption_font_size = settings.get("fontSize", 16)
		if display_settings.get("orientation") == "vertical":
			dimensions = dimensions[::-1]
		width, height = dimensions
		caption_font = ctx.stm.get_font("Jost", font_size=int(caption_font_size)) if is_caption else None
		img = self._compose_image(item, caption_font, width, height)
		return { "image": img, "info": item }

	def _compose_image(self, item, caption_font, width, height):
		response = requests.get(item["image_url"], stream=True)
		response.raise_for_status()

		with Image.open(response.raw) as img:
			background = Image.new("RGB", (width, height), "white")
			draw = ImageDraw.Draw(background)
			top_padding, bottom_padding = 0, 0

			if caption_font is not None:
				if item["title"]:
					lines, wrapped_text = self._wrap_text(item["title"], caption_font, width)
					draw.multiline_text((width // 2, 0), wrapped_text, font=caption_font, fill="black", anchor="ma")
					top_padding = caption_font.getbbox(wrapped_text)[3] * lines + 1

				if item["caption"]:
					lines, wrapped_text = self._wrap_text(item["caption"], caption_font, width)
					draw.multiline_text((width // 2, height), wrapped_text, font=caption_font, fill="black", anchor="md")
					bottom_padding = caption_font.getbbox(wrapped_text)[3] * lines + 1

			scale = min(width / img.width, (height - top_padding - bottom_padding) / img.height)
			new_size = (int(img.width * scale), int(img.height * scale))
			img = img.resize(new_size, Image.LANCZOS)

			y_middle = (height - img.height) // 2
			y_top_bound = top_padding
			y_bottom_bound = height - img.height - bottom_padding

			xx = (width - img.width) // 2
			yy = yy = min(max(y_middle, y_top_bound), y_bottom_bound)

			background.paste(img, (xx, yy))

			return background

	def _wrap_text(self, text, font, width):
		lines = []
		words = text.split()[::-1]

		while words:
			line = words.pop()
			while words and font.getbbox(line + ' ' + words[-1])[2] < width:
				line += ' ' + words.pop()
			lines.append(line)

		return len(lines), '\n'.join(lines)