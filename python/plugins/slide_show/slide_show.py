from ...datasources.data_source import DataSourceManager, MediaList
from ...task.display import DisplayImage
from ...task.message_router import MessageRouter
from ...model.schedule import PlaylistBase, PlaylistSchedule, PluginSchedule, SchedulableBase
from ...task.messages import BasicMessage
from ..plugin_base import BasicExecutionContext2, PluginProtocol
import logging

class SlideShow(PluginProtocol):
	def __init__(self, id, name):
		self._id = id
		self._name = name
		self.logger = logging.getLogger(__name__)
	@property
	def id(self) -> str:
		return self._id
	@property
	def name(self) -> str:
		return self._name
	def start(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase):
		self.logger.info(f"{self.id} start '{track.title}'")
		if isinstance(track, PlaylistSchedule):
			settings = track.content.data
			dataSourceName = settings.get("dataSource", None)
			if dataSourceName is None:
				raise RuntimeError("dataSource is not specified")
			dsm = context.provider.get_service(DataSourceManager)
			if dsm is None:
				raise RuntimeError("DataSourceManager is not available")
			router = context.provider.get_service(MessageRouter)
			if router is None:
				raise RuntimeError("MessageRouter is not available")
			dataSource = dsm.get_source(dataSourceName)
			if dataSource is None:
				raise RuntimeError(f"dataSource '{dataSourceName}' is not available")
			if isinstance(dataSource, MediaList):
				dsec = context.create_datasource_context(dataSource)
				future = dataSource.open(dsec, settings)
				state = future.result(timeout=10)
				if len(state) == 0:
					raise RuntimeError(f"{dataSourceName}: No media items found for slide show")
				item = state[0]
				future2 = dataSource.render(dsec, settings, item)
				image = future2.result(timeout=10)
				state.pop(0)
				router.send("display", DisplayImage(track.title, image))
			pass
		elif isinstance(track, PluginSchedule):
			raise RuntimeError(f"Unsupported track type: {type(track)}")
		else:
			raise RuntimeError(f"Unsupported track type: {type(track)}")
	def receive(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase, msg: BasicMessage):
		self.logger.info(f"{self.id} receive '{track.title}' {msg}")
		if isinstance(track, PlaylistSchedule):
			pass
		elif isinstance(track, PluginSchedule):
			raise RuntimeError(f"Unsupported track type: {type(track)}")
		else:
			raise RuntimeError(f"Unsupported track type: {type(track)}")
		pass