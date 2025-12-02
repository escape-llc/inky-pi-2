from datetime import datetime, timedelta
from ...task.playlist_layer import NextTrack
from ...task.timer import TimerService
from ...datasources.data_source import DataSourceExecutionContext, DataSourceManager, MediaList
from ...task.display import DisplayImage
from ...task.message_router import MessageRouter
from ...model.schedule import PlaylistBase, PlaylistSchedule, PluginSchedule, SchedulableBase
from ...task.messages import BasicMessage, ExecuteMessage, MessageSink
from ..plugin_base import BasicExecutionContext2, PluginProtocol
import logging

class SlideShowTimerExpired(ExecuteMessage):
	def __init__(self, remaining_state: list, timestamp: datetime = None):
		super().__init__(timestamp)
		self.remaining_state = remaining_state
	def __repr__(self) -> str:
		return f"SlideShowTimerExpired(remaining_items={len(self.remaining_state)})"

class SlideShow(PluginProtocol):
	def __init__(self, id, name):
		self._id = id
		self._name = name
		self.timer_info = None
		self.logger = logging.getLogger(__name__)
	@property
	def id(self) -> str:
		return self._id
	@property
	def name(self) -> str:
		return self._name
	def _render_image(self, title: str, context: DataSourceExecutionContext, dataSource: MediaList, settings: dict, state: list, router: MessageRouter, timer: TimerService, timer_sink: MessageSink):
		item = state[0]
		future2 = dataSource.render(context, settings, item)
		image = future2.result(timeout=10)
		state.pop(0)
		router.send("display", DisplayImage(title, image))
		slideshowMinutes = settings.get("slideshowMinutes", 15)
		self.timer_info = timer.create_timer(timedelta(minutes=slideshowMinutes), timer_sink, SlideShowTimerExpired(state))
	def start(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase):
		self.logger.info(f"{self.id} start '{track.title}'")
		if isinstance(track, PlaylistSchedule):
			settings = track.content.data
			# assert required services are available
			dsm = context.provider.get_service(DataSourceManager)
			if dsm is None:
				raise RuntimeError("DataSourceManager is not available")
			router = context.provider.get_service(MessageRouter)
			if router is None:
				raise RuntimeError("MessageRouter is not available")
			timer = context.provider.get_service(TimerService)
			if timer is None:
				raise RuntimeError("TimerService is not available")
			timer_sink = context.provider.get_service(MessageSink)
			if timer_sink is None:
				raise RuntimeError("MessageSink is not available")
			# safe to continue
			dataSourceName = settings.get("dataSource", None)
			if dataSourceName is None:
				raise RuntimeError("dataSource is not specified")
			dataSource = dsm.get_source(dataSourceName)
			if dataSource is None:
				raise RuntimeError(f"dataSource '{dataSourceName}' is not available")
			if isinstance(dataSource, MediaList):
				dsec = context.create_datasource_context(dataSource)
				future = dataSource.open(dsec, settings)
				state = future.result(timeout=10)
				if len(state) == 0:
					raise RuntimeError(f"{dataSourceName}: No media items found for slide show")
				self._render_image(track.title, dsec, dataSource, settings, state, router, timer, timer_sink)
		elif isinstance(track, PluginSchedule):
			raise RuntimeError(f"Unsupported track type: {type(track)}")
		else:
			raise RuntimeError(f"Unsupported track type: {type(track)}")
	def receive(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase, msg: BasicMessage):
		self.logger.info(f"{self.id} receive '{track.title}' {msg}")
		if isinstance(track, PlaylistSchedule):
			if isinstance(msg, SlideShowTimerExpired):
				settings = track.content.data
				# assert required services are available
				dsm = context.provider.get_service(DataSourceManager)
				if dsm is None:
					raise RuntimeError("DataSourceManager is not available")
				router = context.provider.get_service(MessageRouter)
				if router is None:
					raise RuntimeError("MessageRouter is not available")
				timer = context.provider.get_service(TimerService)
				if timer is None:
					raise RuntimeError("TimerService is not available")
				local_sink = context.provider.get_service(MessageSink)
				if local_sink is None:
					raise RuntimeError("MessageSink is not available")
				# safe to continue
				dataSourceName = settings.get("dataSource", None)
				if dataSourceName is None:
					raise RuntimeError("dataSource is not specified")
				dataSource = dsm.get_source(dataSourceName)
				if dataSource is None:
					raise RuntimeError(f"dataSource '{dataSourceName}' is not available")
				if isinstance(dataSource, MediaList):
					state = msg.remaining_state
					if len(state) == 0:
						self.logger.info(f"{dataSourceName}: Slide show completed, moving to next track")
						self.timer_info = None
						local_sink.send(NextTrack())
						return
					dsec = context.create_datasource_context(dataSource)
					self._render_image(track.title, dsec, dataSource, settings, state, router, timer, local_sink)
				pass
		elif isinstance(track, PluginSchedule):
			raise RuntimeError(f"Unsupported track type: {type(track)}")
		else:
			raise RuntimeError(f"Unsupported track type: {type(track)}")
