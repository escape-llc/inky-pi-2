import os
from pathlib import Path
from PIL import Image
from datetime import datetime, timezone
import logging
import pytz

from ...model.schedule import PluginSchedule
from ...task.display import DisplayImage
from ...model.configuration_manager import StaticConfigurationManager
from ..plugin_base import PluginBase, PluginExecutionContext, RenderSession

logger = logging.getLogger(__name__)
class Countdown(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		if isinstance(ctx.sb, PluginSchedule):
			dimensions = ctx.resoluion
			data = ctx.sb.content.data
			display_config = ctx.scm.load_settings("display")
			img = None
			try:
				img = self.generate_image(ctx.schedule_ts, ctx.stm, dimensions, data, display_config)
			except Exception as e:
				self.logger.error(f"Failed to draw year progress image: {str(e)}")
			if img is not None:
				self.logger.debug(f"display {ctx.schedule_ts}")
				ctx.router.send("display", DisplayImage(f"{ctx.schedule_ts} year progress", img))

	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")

	def generate_image(self, schedule_ts:datetime, stm: StaticConfigurationManager, dimensions, settings, display_config):
		title = settings.get('title')
		countdown_date_str = settings.get('targetDate')

		if not countdown_date_str:
			raise RuntimeError("Date is required.")

		if display_config.get("orientation") == "portrait":
			dimensions = dimensions[::-1]
		
		timezone = "US/Eastern" #display_config.get_config("timezone", default="America/New_York")
		tz = pytz.timezone(timezone)
#		current_time = datetime.now(tz)
		current_time = schedule_ts.astimezone(tz)

		countdown_date = datetime.strptime(countdown_date_str, "%Y-%m-%d")
		countdown_date = tz.localize(countdown_date)

		day_count = (countdown_date.date() - current_time.date()).days
		label = "Days Left" if day_count > 0 else "Days Passed"

		template_params = {
			"title": title,
			"date": countdown_date.strftime("%B %d, %Y"),
			"day_count": abs(day_count),
			"label": label,
			"settings": settings
		}

		px = Path(os.path.dirname(__file__)).joinpath("render")
		css = os.path.join(px.resolve(), "countdown.css")
		rs = RenderSession(stm, px.resolve(), "countdown.html", css)
		image = rs.render(dimensions, template_params)
		return image