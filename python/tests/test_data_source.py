from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import unittest
import logging

from python.datasources.openai_image.openai_image import OpenAI
from python.datasources.comic.comic_feed import ComicFeed
from python.datasources.data_source import DataSourceExecutionContext, DataSourceManager
from python.datasources.wpotd.wpotd import Wpotd
from python.model.configuration_manager import ConfigurationManager, DatasourceConfigurationManager
from python.datasources.newspaper.newspaper import Newspaper

from ..datasources.image_folder.image_folder import ImageFolder

logging.basicConfig(
	level=logging.DEBUG,  # Or DEBUG for more detail
	format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

class TestDataSources(unittest.TestCase):
	def create_data_source_context(self, dsid:str):
		test_file_path = os.path.abspath(__file__)
		test_directory = os.path.dirname(test_file_path)
		storage = os.path.join(test_directory, "storage")
		cm = ConfigurationManager(storage_path=storage)
		cm.ensure_folders()
		scm = cm.settings_manager()
		stm = cm.static_manager()
		dscm = cm.datasource_manager(dsid)
		resolution = [800,480]
		return DataSourceExecutionContext(stm, scm, dscm, resolution, datetime.now())

	def run_datasource(self, ds, params, image_size, image_count):
		tpe = ThreadPoolExecutor(max_workers=2)
		ds.set_executor(tpe)
		try:
			dsec = self.create_data_source_context(ds.name)
			future_state = ds.open(dsec, params)
			state = future_state.result(timeout=5)
			self.assertTrue(len(state) > 0)
			images = []
			while len(state) > 0:
				item = state[0]
				state.pop(0)
				future_img = ds.render(dsec, params, item)
				result = future_img.result(timeout=5)
				if result is None:
					break
				images.append(result)
				self.assertEqual(result.size, image_size)
			self.assertEqual(len(images), image_count)
		finally:
			ds.set_executor(None)
			tpe.shutdown(wait=True, cancel_futures=True)
	def test_image_folder(self):
		ds = ImageFolder("image-folder")
		params = {
			"folder": "python/tests/images"
		}
		self.run_datasource(ds, params, (800, 480), 9)
	def test_comic_feed(self):
		ds = ComicFeed("comic-feed")
		params = {
			"comic": "XKCD",
			"titleCaption": True,
			"fontSize": 12
		}
		self.run_datasource(ds, params, (800, 480), 4)
	def test_wikipedia(self):
		ds = Wpotd("wpotd")
		params = {
			"shrinkToFit": True
		}
		self.run_datasource(ds, params, (800, 480), 1)
	def test_newspaper(self):
		ds = Newspaper("newspaper")
		params = {
			"slug": "ny_nyt"
		}
		self.run_datasource(ds, params, (700, 1166), 1)
	def test_openai(self):
		ds = OpenAI("openai-image")
		params = {
			"prompt": "a cute robot reading a book in a cozy library",
			"imageModel": "dall-e-3",
		}
		self.run_datasource(ds, params, (800, 480), 1)
	def test_datasource_manager(self):
		sources = {
			"image-folder": ImageFolder("image-folder"),
			"comic-feed": ComicFeed("comic-feed"),
			"wpotd": Wpotd("wpotd"),
			"newspaper": Newspaper("newspaper")
		}
		dsm = ds_mgr = None
		try:
			dsm = ds_mgr = DataSourceManager(None, sources)
			for name, ds in sources.items():
				retrieved = dsm.get_source(name)
				self.assertIsNotNone(retrieved)
				self.assertEqual(retrieved.name, ds.name)
			nonexistent = dsm.get_source("nonexistent-source")
			self.assertIsNone(nonexistent)
		finally:
			if dsm is not None:
				dsm.shutdown()
if __name__ == "__main__":
	unittest.main()