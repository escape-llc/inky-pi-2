from concurrent.futures import Executor, ThreadPoolExecutor, Future
from datetime import datetime
from typing import Protocol
from PIL import Image

from python.model.configuration_manager import DatasourceConfigurationManager, SettingsConfigurationManager, StaticConfigurationManager

class DataSource:
	def __init__(self, name: str) -> None:
		self.name = name
		self.es = None
	def set_executor(self, es: Executor) -> None:
		self.es = es

class DataSourceExecutionContext:
	def __init__(self, stm: StaticConfigurationManager, scm: SettingsConfigurationManager, dscm: DatasourceConfigurationManager, dimensions, schedule_ts: datetime):
		if stm is None:
			raise ValueError("stm is None")
		if scm is None:
			raise ValueError("scm is None")
		if dscm is None:
			raise ValueError("dscm is None")
		if schedule_ts is None:
			raise ValueError("schedule_ts is None")
		self.scm = scm
		self.stm = stm
		self.dscm = dscm
		self.dimensions = dimensions
		self.schedule_ts = schedule_ts

class MediaList(Protocol):
	def open(self, dsec: DataSourceExecutionContext, params:dict[str,any]) -> Future[list]:
		pass
	def render(self, dsec: DataSourceExecutionContext, params:dict[str,any], state:any) -> Future[Image.Image | None]:
		pass

class DataSourceManager:
	def __init__(self, es: Executor|None, sources: dict[str, DataSource]) -> None:
		self.es = es if es is not None else ThreadPoolExecutor(max_workers=4)
		self.sources = sources
		for source in self.sources.values():
			source.set_executor(self.es)
	def get_source(self, name: str) -> DataSource|None:
		return self.sources.get(name, None)
	def shutdown(self) -> None:
		self.es.shutdown(wait=True, cancel_futures=True)