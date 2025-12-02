import logging

from python.datasources.data_source import DataSourceManager
from python.model.schedule import MasterSchedule, Playlist, PlaylistBase
from python.plugins.plugin_base import BasicExecutionContext, PluginBase, PluginProtocol

from ..model.configuration_manager import ConfigurationManager
from .display import DisplaySettings
from .messages import ConfigureEvent, ExecuteMessage
from .message_router import MessageRouter
from .basic_task import BasicTask

class PlaylistLayerMessage(ExecuteMessage):
	def __init__(self, timestamp=None):
		super().__init__(timestamp)
class StartPlayback(PlaylistLayerMessage):
	def __init__(self, timestamp=None):
		super().__init__(timestamp)
class NextTrack(PlaylistLayerMessage):
	def __init__(self, timestamp=None):
		super().__init__(timestamp)

class PlaylistLayer(BasicTask):
	def __init__(self, name, router: MessageRouter):
		super().__init__(name)
		if router is None:
			raise ValueError("router is None")
		self.router = router
		self.cm:ConfigurationManager = None
		self.playlists = []
		self.master_schedule:MasterSchedule = None
		self.plugin_info = None
		self.plugin_map = None
		self.datasources: DataSourceManager = None
		self.resolution = [800,480]
		self.playlist_state = None
		self.state = 'uninitialized'
		self.logger = logging.getLogger(__name__)
	def _evaluate_plugin(self, track:PlaylistBase):
		if self.plugin_map.get(track.plugin_name, None):
#						self.logger.debug(f"selecting plugin '{timeslot.plugin_name}' with args {timeslot.content}")
			plugin = self.plugin_map[track.plugin_name]
			if isinstance(plugin, PluginBase):
				return { "plugin": plugin, "track": track }
			else:
				errormsg = f"Plugin '{track.plugin_name}' is not a valid PluginBase instance."
				self.logger.error(errormsg)
				return { "plugin": plugin, "track": track, "error": errormsg }
		else:
			errormsg = f"Plugin '{track.plugin_name}' is not available."
			self.logger.error(errormsg)
			return { "plugin": None, "track": track, "error": errormsg }
	def _create_context(self):
		scm = self.cm.settings_manager()
		stm = self.cm.static_manager()
		return BasicExecutionContext(stm, scm, self.datasources, self.resolution, self.router)
	def _start_playback(self):
		self.logger.info(f"'{self.name}' StartPlayback {self.state}")
		if self.state != 'loaded':
			self.logger.error(f"Cannot start playback, state is '{self.state}'")
			return
		if len(self.playlists) == 0:
			self.logger.error(f"No playlists available to play.")
			return
		# Start playback logic here
		current_playlist:Playlist = self.playlists[0]
		current_track:PlaylistBase = current_playlist.items[0] if len(current_playlist.items) > 0 else None
		if current_track is None:
			self.logger.error(f"Current playlist '{current_playlist.name}' has no tracks.")
			return
		plugin_eval = self._evaluate_plugin(current_track)
		active_plugin:PluginProtocol = plugin_eval.get("plugin", None)
		if active_plugin is None:
			self.logger.error(f"Cannot start playback, plugin '{current_track.plugin_name}' for track '{current_track.title}' is not available.")
			return
		context = self._create_context()
		self.playlist_state = {
			'current_playlist_index': 0,
			'current_playlist': current_playlist,
			'current_track_index': 0,
			'current_track': current_track,
			'active_plugin': active_plugin,
			'context': context
		}
		try:
			active_plugin.start(context, current_track)
			self.state = 'playing'
			self.logger.info(f"'{self.name}' Playback started.")
		except Exception as e:
			self.logger.error(f"Error starting playback with plugin '{current_track.plugin_name}' for track '{current_track.title}': {e}", exc_info=True)
			self.state = 'error'
	def execute(self, msg: ExecuteMessage):
		# Handle scheduling messages here
		self.logger.info(f"'{self.name}' receive: {msg}")
		if isinstance(msg, ConfigureEvent):
			self.cm = msg.content.cm
			try:
				plugin_info = self.cm.enum_plugins()
				plugins = self.cm.load_plugins(plugin_info)
				self.logger.info(f"Plugins loaded: {list(plugins.keys())}")
				self.plugin_info = plugin_info
				self.plugin_map = plugins
				datasource_info = self.cm.enum_datasources()
				datasources = self.cm.load_datasources(datasource_info)
				self.datasources = DataSourceManager(datasources)
				self.logger.info(f"Datasources loaded: {list(datasources.keys())}")
				sm = self.cm.schedule_manager()
				schedule_info = sm.load()
				sm.validate(schedule_info)
				self.master_schedule = schedule_info.get("master", None)
				self.playlists = schedule_info.get("playlists", [])
				self.logger.info(f"schedule loaded")
				self.state = 'loaded'
				msg.notify()
				self.send(StartPlayback("SystemStart"))
			except Exception as e:
				self.logger.error(f"Failed to load/validate schedules: {e}", exc_info=True)
				self.state = 'error'
				msg.notify(True, e)
		elif isinstance(msg, DisplaySettings):
			self.logger.info(f"'{self.name}' DisplaySettings {msg.name} {msg.width} {msg.height}.")
			self.resolution = [msg.width, msg.height]
		elif isinstance(msg, StartPlayback):
			self._start_playback()