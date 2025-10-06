from datetime import datetime, timedelta
import logging
import requests
from io import BytesIO
import base64
from openai import OpenAI
from PIL import Image, ImageOps, ImageFilter

from ...model.schedule import PluginSchedule
from ...model.configuration_manager import PluginConfigurationManager
from ...task.messages import BasicMessage, FutureCompleted
from ...task.display import DisplayImage
from ...utils.image_utils import get_image
from ..plugin_base import PluginBase, PluginExecutionContext

IMAGE_MODELS = ["dall-e-3", "dall-e-2", "gpt-image-1"]
DEFAULT_IMAGE_MODEL = "dall-e-3"
DEFAULT_IMAGE_QUALITY = "standard"

class OpenAIImage(PluginBase):
	TOKEN = "generate-image"
	def __init__(self, id, name):
		super().__init__(id, name)
		self.logger = logging.getLogger(__name__)
	def timeslot_start(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.start '{ctx.sb.title}'.")
		settings = ctx.sb.content.data
		plugin_settings = ctx.pcm.load_settings()
		display_settings = ctx.scm.load_settings("display")

		api_key = plugin_settings.get("apiKey", None)
		if not api_key:
				raise RuntimeError("OPEN AI API Key not configured.")
		text_prompt = settings.get("prompt", "")
		image_model = settings.get("imageModel", DEFAULT_IMAGE_MODEL)
		if image_model not in IMAGE_MODELS:
			raise RuntimeError("Invalid Image Model provided.")
		image_quality = settings.get('quality', "medium" if image_model == "gpt-image-1" else "standard")
		randomize_prompt = settings.get('randomizePrompt') == True
		orientation = display_settings.get("orientation", "landscape")

		def future_image_download():
			image = self._dispatch_image(ctx, api_key, image_model, image_quality, text_prompt, randomize_prompt, orientation)
			return image
		ctx.future(self.TOKEN, future_image_download)
	def timeslot_end(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' timeslot.end '{ctx.sb.title}'.")
	def receive(self, ctx: PluginExecutionContext, msg: BasicMessage):
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, FutureCompleted):
			if msg.token == self.TOKEN:
				if msg.is_success:
					self.logger.debug(f"{self.TOKEN} {msg.result}")
					self.logger.debug(f"display {ctx.schedule_ts} OpenAI Image")
					ctx.router.send("display", DisplayImage(f"{ctx.schedule_ts} OpenAI Image", msg.result))
				else:
					self.logger.error(f"'{self.name}' {self.TOKEN} {str(msg.error)}")
	def reconfigure(self, pec: PluginExecutionContext, config):
		self.logger.info(f"'{self.name}' reconfigure: {config}")
	def schedule(self, ctx: PluginExecutionContext):
		self.logger.info(f"'{self.name}' schedule '{ctx.sb.title}'.")
	def _dispatch_image(self, ctx: PluginExecutionContext, api_key, image_model, image_quality, text_prompt, randomize_prompt, orientation):
		image = None
		try:
			ai_client = OpenAI(api_key = api_key)
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
		except Exception as e:
			self.logger.error(f"Failed to make Open AI request: {str(e)}")
			raise RuntimeError("Open AI request failure, please check logs.")
		return image

	@staticmethod
	def fetch_image(logger, ai_client, prompt, model="dall-e-3", quality="standard", orientation="horizontal"):
		logger.info(f"fetch_image prompt: {prompt}, model: {model}, quality: {quality}")
		prompt += (
			". The image should fully occupy the entire canvas without any frames, "
			"borders, or cropped areas. No blank spaces or artificial framing."
		)
		prompt += (
			"Focus on simplicity, bold shapes, and strong contrast to enhance clarity "
			"and visual appeal. Avoid excessive detail or complex gradients, ensuring "
			"the design works well with flat, vibrant colors."
		)
		args = {
			"model": model,
			"prompt": prompt,
			"size": "1024x1024",
		}
		if model == "dall-e-3":
			args["size"] = "1792x1024" if orientation == "horizontal" else "1024x1792"
			args["quality"] = quality
		elif model == "gpt-image-1":
			args["size"] = "1536x1024" if orientation == "horizontal" else "1024x1536"
			args["quality"] = quality

		response = ai_client.images.generate(**args)
		if model in ["dall-e-3", "dall-e-2"]:
				image_url = response.data[0].url
				response = requests.get(image_url)
				img = Image.open(BytesIO(response.content))
		elif model == "gpt-image-1":
				image_base64 = response.data[0].b64_json
				image_bytes = base64.b64decode(image_base64)
				img = Image.open(BytesIO(image_bytes))
		return img

	@staticmethod
	def fetch_image_prompt(logger, ai_client, from_prompt=None):
		logger.info(f"fetch_image_prompt")

		system_content = (
			"You are a creative assistant generating extremely random and unique image prompts. "
			"Avoid common themes. Focus on unexpected, unconventional, and bizarre combinations "
			"of art style, medium, subjects, time periods, and moods. No repetition. Prompts "
			"should be 20 words or less and specify random artist, movie, tv show or time period "
			"for the theme. Do not provide any headers or repeat the request, just provide the "
			"updated prompt in your response."
		)
		user_content = (
			"Give me a completely random image prompt, something unexpected and creative! "
			"Let's see what your AI mind can cook up!"
		)
		if from_prompt and from_prompt.strip():
			system_content = (
				"You are a creative assistant specializing in generating highly descriptive "
				"and unique prompts for creating images. When given a short or simple image "
				"description, your job is to rewrite it into a more detailed, imaginative, "
				"and descriptive version that captures the essence of the original while "
				"making it unique and vivid. Avoid adding irrelevant details but feel free "
				"to include creative and visual enhancements. Avoid common themes. Focus on "
				"unexpected, unconventional, and bizarre combinations of art style, medium, "
				"subjects, time periods, and moods. Do not provide any headers or repeat the "
				"request, just provide your updated prompt in the response. Prompts "
				"should be 20 words or less and specify random artist, movie, tv show or time "
				"period for the theme."
			)
			user_content = (
				f"Original prompt: \"{from_prompt}\"\n"
				"Rewrite it to make it more detailed, imaginative, and unique while staying "
				"true to the original idea. Include vivid imagery and descriptive details. "
				"Avoid changing the subject of the prompt."
			)

		# Make the API call
		response = ai_client.chat.completions.create(
			model="gpt-4o",
			messages=[
				{
					"role": "system",
					"content": system_content
				},
				{
					"role": "user",
					"content": user_content
				}
			],
			temperature=1
		)

		prompt = response.choices[0].message.content.strip()
		logger.info(f"fetch_image_prompt.Generated: {prompt}")
		return prompt
