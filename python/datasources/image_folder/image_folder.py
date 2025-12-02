from concurrent.futures import Future
import logging

from PIL import Image
from ...plugins.image_folder.image_folder import grab_image, list_files_in_folder
from ..data_source import DataSource, DataSourceExecutionContext, MediaList

class ImageFolder(DataSource, MediaList):
	def __init__(self, id: str, name: str):
		super().__init__(id, name)
	def open(self, dsec: DataSourceExecutionContext, params: dict[str, any]) -> Future[list]:
		if self._es is None:
			raise RuntimeError("Executor not set for DataSource")
		folder_path = params.get('folder')
		def open_folder():
			image_files = list_files_in_folder(folder_path)
			return image_files
		future = self._es.submit(open_folder)
		return future
	def render(self, dsec: DataSourceExecutionContext, params:dict[str,any], state:any) -> Future[Image.Image | None]:
		if self._es is None:
			raise RuntimeError("Executor not set for DataSource")
		def load_next():
			if state is None:
				return None
			img = grab_image(state, dsec.dimensions, pad_image=True, logger=logging.getLogger(__name__))
			return img
		future = self._es.submit(load_next)
		return future

