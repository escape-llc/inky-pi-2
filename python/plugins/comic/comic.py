import logging
import requests

from PIL import Image, ImageDraw, ImageFont

from ...task.display import DisplayImage
from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ..plugin_base import PluginBase, PluginExecutionContext
from .comic_parser import COMICS, get_panel


class Comic(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		ctx.pcm.delete_state()
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, msg):
		self.logger.info(f"'{self.name}' receive: {msg}")
	def reconfigure(self, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")
		if isinstance(ctx.sb, PluginSchedule):
			display_settings = ctx.scm.load_settings("display")
			dimensions = ctx.resoluion
			data = ctx.sb.content.data
			comic = data.get("comic")
			image = self.generate_image(ctx.pcm, data, dimensions, display_settings)
			if image is not None:
				self.logger.debug(f"display {ctx.schedule_ts} {comic}")
				ctx.router.send("display", DisplayImage(f"{ctx.schedule_ts} {comic}", image))

	def generate_image(self, pcm: PluginConfigurationManager, settings, dimensions, display_settings):
		comic = settings.get("comic")
		if not comic or comic not in COMICS:
			raise RuntimeError("Invalid comic provided.")

		plugin_state = pcm.load_state()
		comic_panel = get_panel(comic)

		if plugin_state is None or plugin_state.get("image_url") != comic_panel["image_url"]:
			is_caption = settings.get("titleCaption") == "true"
			caption_font_size = settings.get("fontSize")
			if display_settings.get("orientation") == "vertical":
				dimensions = dimensions[::-1]
			width, height = dimensions

			img = self._compose_image(comic_panel, is_caption, caption_font_size, width, height)
			pcm.save_state(comic_panel)
			return img
		else:
			self.logger.info(f"URL has not changed {comic_panel["image_url"]}")
		return None

	def _compose_image(self, comic_panel, is_caption, caption_font_size, width, height):
		response = requests.get(comic_panel["image_url"], stream=True)
		response.raise_for_status()

		with Image.open(response.raw) as img:
			background = Image.new("RGB", (width, height), "white")
			font = ImageFont.truetype("DejaVuSans.ttf", size=int(caption_font_size))
			draw = ImageDraw.Draw(background)
			top_padding, bottom_padding = 0, 0

			if is_caption:
				if comic_panel["title"]:
					lines, wrapped_text = self._wrap_text(comic_panel["title"], font, width)
					draw.multiline_text((width // 2, 0), wrapped_text, font=font, fill="black", anchor="ma")
					top_padding = font.getbbox(wrapped_text)[3] * lines + 1

				if comic_panel["caption"]:
					lines, wrapped_text = self._wrap_text(comic_panel["caption"], font, width)
					draw.multiline_text((width // 2, height), wrapped_text, font=font, fill="black", anchor="md")
					bottom_padding = font.getbbox(wrapped_text)[3] * lines + 1

			scale = min(width / img.width, (height - top_padding - bottom_padding) / img.height)
			new_size = (int(img.width * scale), int(img.height * scale))
			img = img.resize(new_size, Image.LANCZOS)

			y_middle = (height - img.height) // 2
			y_top_bound = top_padding
			y_bottom_bound = height - img.height - bottom_padding
			
			x = (width - img.width) // 2
			y = y = min(max(y_middle, y_top_bound), y_bottom_bound)
			
			background.paste(img, (x, y))

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