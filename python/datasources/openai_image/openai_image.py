from concurrent.futures import Future
from PIL import Image
from openai import BadRequestError, OpenAI
import logging

import openai

from ...plugins.ai_image.ai_image import OpenAIImage
from ..data_source import DataSource, DataSourceExecutionContext, MediaList

DEFAULT_IMAGE_MODEL = "dall-e-3"
DEFAULT_IMAGE_QUALITY = "standard"
IMAGE_MODELS = ["dall-e-3", "dall-e-2", "gpt-image-1"]
class OpenAI(DataSource,MediaList):
	def __init__(self,name:str):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)
	def open(self, dsec: DataSourceExecutionContext, params: dict[str, any]) -> Future[list]:
		if self.es is None:
			raise RuntimeError("Executor not set for DataSource")
		def locate_image_url():
			plugin_settings = dsec.dscm.load_settings()
			if not plugin_settings:
				raise RuntimeError("Open AI Image datasource not configured.")
			api_key = plugin_settings.get("apiKey", None)
			if not api_key:
					raise RuntimeError("OPEN AI API Key not configured.")
			text_prompt = params.get("prompt", "")
			image_model = params.get("imageModel", DEFAULT_IMAGE_MODEL)
			if image_model not in IMAGE_MODELS:
				raise RuntimeError(f"Invalid Image Model provided: {image_model}")
			image_quality = params.get('quality', "medium" if image_model == "gpt-image-1" else "standard")
			randomize_prompt = params.get('randomizePrompt') == True
			display_settings = dsec.scm.load_settings("display")
			orientation = display_settings.get("orientation", "landscape")
			return [{ "api_key": api_key, "text_prompt": text_prompt, "image_model": image_model, "image_quality": image_quality, "randomize_prompt": randomize_prompt, "orientation": orientation }]
		future = self.es.submit(locate_image_url)
		return future
	def render(self, dsec: DataSourceExecutionContext, params:dict[str,any], state:any) -> Future[Image.Image | None]:
		if self.es is None:
			raise RuntimeError("Executor not set for DataSource")
		def load_next():
			if state is None:
				return None
			image = self._dispatch_image(dsec, state.get('api_key'), state.get('image_model'), state.get('image_quality'), state.get('text_prompt'), state.get('randomize_prompt'), state.get('orientation'))
			return image
		future = self.es.submit(load_next)
		return future
	def _dispatch_image(self, dsec: DataSourceExecutionContext, api_key, image_model, image_quality, text_prompt, randomize_prompt, orientation) -> Image.Image | None:
		image = None
		try:
			ai_client = openai.OpenAI(api_key = api_key, timeout=60, max_retries=3)
			if randomize_prompt:
				text_prompt = OpenAIImage.fetch_image_prompt(self.logger, ai_client, text_prompt)

			image = OpenAIImage.fetch_image(
				self.logger,
				ai_client,
				text_prompt,
				model=image_model,
				quality=image_quality,
				orientation=orientation
			)
			return image
		except BadRequestError as bre:
			self.logger.error(f"Open AI Bad Request: {bre.body.get("message")}")
			raise RuntimeError(f"Open AI Bad Request: {bre.body.get("message")}")
		except Exception as e:
			self.logger.error(f"Failed to make Open AI request: {str(e)}")
			raise RuntimeError(f"Open AI request failure: {str(e)}")
