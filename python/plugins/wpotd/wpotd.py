"""
Wpotd Plugin for eInk Billboard
This plugin fetches the Wikipedia Picture of the Day (Wpotd) from Wikipedia's API
and displays it. 

It supports optional manual date selection or random dates and can resize the image to fit the device's dimensions.

Wikipedia API Documentation: https://www.mediawiki.org/wiki/API:Main_page
Picture of the Day example: https://www.mediawiki.org/wiki/API:Picture_of_the_day_viewer
Github Repository: https://github.com/wikimedia/mediawiki-api-demos/tree/master/apps/picture-of-the-day-viewer
Wikimedia requires a User Agent header for API requests, which is set in the SESSION headers:
https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy

Flow:

1. Fetch the date to use for the Picture of the Day (POTD) based on settings. (_determine_date)
2. Make an API request to fetch the POTD data for that date. (_fetch_potd)
3. Extract the image filename from the response. (_fetch_potd)
4. Make another API request to get the image URL. (_fetch_image_src)
5. Download the image from the URL. (_download_image)
6. Optionally resize the image to fit the device dimensions. (_shrink_to_fit))
"""
from datetime import date, timedelta
import datetime
from io import BytesIO
import logging
from random import randint
from typing import Any, Dict
import requests

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ...task.messages import BasicMessage, FutureCompleted
from ...task.display import DisplayImage
from ..plugin_base import PluginBase, PluginExecutionContext

class Wpotd(PluginBase):
	API_URL = "https://en.wikipedia.org/w/api.php"
	TOKEN = "wpotd-download"
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)

	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		settings = ctx.sb.content.data
		dimensions = ctx.resoluion
		def future_feed_download():
			return self.generate_image(settings, dimensions)
		ctx.future(self.TOKEN, future_feed_download)
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, pec: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, FutureCompleted):
			if msg.token == self.TOKEN:
				if msg.is_success:
					self.logger.debug(f"wpotd-download {msg.result}")
					image = msg.result
					if image is not None:
						self.logger.debug(f"display {pec.schedule_ts} Wpotd")
						pec.router.send("display", DisplayImage(f"{pec.schedule_ts} Wpotd", image))
				else:
					self.logger.error(f"wpotd-download {str(msg.error)}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")

	def generate_image(self, settings: Dict[str, Any], dimensions) -> Image.Image:
		self.logger.info(f"'{self.name}' settings: {settings}")
		datetofetch = self._determine_date(settings)
		self.logger.info(f"'{self.name}' datetofetch: {datetofetch}")

		data = self._fetch_potd(datetofetch)
		picurl = data["image_src"]
		self.logger.info(f"'{self.name}' Picture URL: {picurl}")

		image = self._download_image(picurl)
		if image is None:
			self.logger.error(f"'{self.name}' Failed to download image.")
			raise RuntimeError(f"'{self.name}' Failed to download image.")
		if settings.get("shrinkToFitWpotd") == "true":
			max_width, max_height = dimensions
			image = self._shrink_to_fit(image, max_width, max_height)
			self.logger.info(f"'{self.name}' Image resized: {max_width},{max_height}")

		return image

	def _determine_date(self, settings: Dict[str, Any]) -> date:
		if settings.get("randomizeWpotd") == "true":
			start = datetime(2015, 1, 1)
			delta_days = (datetime.today() - start).days
			return (start + timedelta(days=randint(0, delta_days))).date()
		elif settings.get("customDate"):
			return datetime.strptime(settings["customDate"], "%Y-%m-%d").date()
		else:
			return datetime.today().date()

	def _download_image(self, url: str) -> Image.Image:
		try:
			if url.lower().endswith(".svg"):
				self.logger.warning("'{self.name}' SVG format is not supported by Pillow. Skipping image download.")
				raise RuntimeError("'{self.name}' Unsupported image format: SVG.")

			response = self.SESSION.get(url, headers=self.HEADERS, timeout=10)
			response.raise_for_status()
			return Image.open(BytesIO(response.content))
		except UnidentifiedImageError as e:
			self.logger.error(f"'{self.name}' Unsupported image format at {url}: {str(e)}")
			raise RuntimeError(f"'{self.name}' Unsupported image format.")
		except Exception as e:
			self.logger.error(f"'{self.name}' Failed to load WPOTD image from {url}: {str(e)}")
			raise RuntimeError(f"'{self.name}' Failed to load WPOTD image.")

	def _fetch_potd(self, cur_date: date) -> Dict[str, Any]:
		title = f"Template:POTD/{cur_date.isoformat()}"
		params = {
			"action": "query",
			"format": "json",
			"formatversion": "2",
			"prop": "images",
			"titles": title
		}

		data = self._make_request(params)
		try:
			filename = data["query"]["pages"][0]["images"][0]["title"]
		except (KeyError, IndexError) as e:
			self.logger.error(f"'{self.name}' Failed to retrieve POTD filename for {cur_date}: {e}")
			raise RuntimeError(f"'{self.name}' Failed to retrieve POTD filename.")

		image_src = self._fetch_image_src(filename)

		return {
			"filename": filename,
			"image_src": image_src,
			"image_page_url": f"https://en.wikipedia.org/wiki/{title}",
			"date": cur_date
		}

	def _fetch_image_src(self, filename: str) -> str:
		params = {
			"action": "query",
			"format": "json",
			"prop": "imageinfo",
			"iiprop": "url",
			"titles": filename
		}
		data = self._make_request(params)
		try:
			page = next(iter(data["query"]["pages"].values()))
			return page["imageinfo"][0]["url"]
		except (KeyError, IndexError, StopIteration) as e:
			self.logger.error(f"'{self.name}' Failed to retrieve image URL for {filename}: {e}")
			raise RuntimeError(f"'{self.name}' Failed to retrieve image URL.")

	def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
		try:
			response = self.SESSION.get(self.API_URL, params=params, headers=self.HEADERS, timeout=10)
			response.raise_for_status()
			return response.json()
		except Exception as e:
			self.logger.error(f"'{self.name}' Wikipedia API request failed with params {params}: {str(e)}")
			raise RuntimeError(f"'{self.name}' Wikipedia API request failed.")

	def _shrink_to_fit(self, image: Image.Image, max_width: int, max_height: int) -> Image.Image:
		"""
		Resize the image to fit within max_width and max_height while maintaining aspect ratio.
		Uses high-quality resampling.
		"""
		orig_width, orig_height = image.size

		if orig_width > max_width or orig_height > max_height:
			# Determine whether to constrain by width or height
			if orig_width >= orig_height:
				# Landscape or square -> constrain by max_width
				if orig_width > max_width:
					new_width = max_width
					new_height = int(orig_height * max_width / orig_width)
				else:
					new_width, new_height = orig_width, orig_height
			else:
				# Portrait -> constrain by max_height
				if orig_height > max_height:
					new_height = max_height
					new_width = int(orig_width * max_height / orig_height)
				else:
					new_width, new_height = orig_width, orig_height
			# Resize using high-quality resampling
			image = image.resize((new_width, new_height), Image.LANCZOS)
			# Create a new image with white background and paste the resized image in the center
			new_image = Image.new("RGB", (max_width, max_height), (255, 255, 255))
			new_image.paste(image, ((max_width - new_width) // 2, (max_height - new_height) // 2))
			return new_image
		else:
			# If the image is already within bounds, return it as is
			return image