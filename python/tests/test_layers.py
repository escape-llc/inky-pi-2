import os
import time
import unittest

from python.datasources.data_source import DataSourceManager
from python.task.display import DisplaySettings
from python.task.timer import TimerService

from ..task.messages import BasicMessage, ConfigureEvent, ConfigureOptions, QuitMessage
from ..task.playlist_layer import PlaylistLayer, StartPlayback
from ..task.message_router import MessageRouter
from ..plugins.plugin_base import BasicExecutionContext2, PluginBase, PluginProtocol
from ..model.schedule import Playlist, PlaylistBase, PlaylistSchedule, PlaylistScheduleData, SchedulableBase
from .utils import create_configuration_manager

class TestPlugin(PluginProtocol):
	def __init__(self, id, name):
		self._id = id
		self._name = name
		self.started = False
		self.start_args = None
	@property
	def id(self) -> str:
		return self._id
	@property
	def name(self) -> str:
		return self._name
	def start(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase):
		self.started = True
	def receive(self, context: BasicExecutionContext2, track: SchedulableBase|PlaylistBase, msg: BasicMessage):
		pass

	# PlaylistLayer expects plugin to expose a `start(track, context)` method
	def start(self, track, context):
		self.started = True
		self.start_args = (track, context)

class PlaylistLayerSimulation(unittest.TestCase):
	def test_simulate_playlist_layer(self):
		router = MessageRouter()
		cm = create_configuration_manager()
		# Further simulation logic would go here
		options = ConfigureOptions(cm)
		configure = ConfigureEvent("configure", options)
		layer = PlaylistLayer("testlayer", router)
		dev = DisplaySettings("none", 800, 480)
		layer.start()
		layer.send(dev)
		layer.send(configure)
		time.sleep(10)
		layer.send(QuitMessage())
		layer.join(timeout=2)

class PlaylistLayerTests(unittest.TestCase):
	def setUp(self):
		self.router = MessageRouter()
		self.layer = PlaylistLayer("testlayer", self.router)
		self.layer.cm = create_configuration_manager()
		self.layer.datasources = DataSourceManager(None, {})
		self.layer.timer = TimerService(None)

	def test_start_playback_success(self):
		# Prepare a plugin and a playlist with one track that references it
#		plugin = TestPlugin("p1", "TestPlugin")
		# plugin_map keys are plugin ids used in PlaylistSchedule.plugin_name
		test_file_path = os.path.abspath(__file__)
		folder = os.path.dirname(test_file_path)
		self.layer.plugin_info = [
			{
				"info": {
					"id": "p1", "name": "Test Plugin",
					"module":"python.tests.test_layers",
					"class":"TestPlugin",
					"file":"test_layers.py"
				},
				"path": folder
			}
		]

		# Create a playlist with a single PlaylistSchedule track
		track = PlaylistSchedule("p1", "t1", "Title", PlaylistScheduleData({}))
		playlist = Playlist("pl1", "Main", items=[track])
		self.layer.playlists = [playlist]
		self.layer.state = 'loaded'

		# Trigger playback
		self.layer.execute(StartPlayback("start"))

		self.assertEqual(self.layer.state, 'playing')
		self.assertIsNotNone(self.layer.playlist_state)
		self.assertTrue(self.layer.playlist_state['active_plugin'].started)
		# verify indices set
		self.assertEqual(self.layer.playlist_state['current_playlist_index'], 0)
		self.assertEqual(self.layer.playlist_state['current_track_index'], 0)

	def test_start_playback_no_playlists(self):
		self.layer.playlists = []
		self.layer.plugin_info = []
		self.layer.state = 'loaded'

		# Should not raise, but should not start playback
		self.layer.execute(StartPlayback("start"))
		self.assertNotEqual(self.layer.state, 'playing')
		self.assertIsNone(self.layer.playlist_state)

	def test_start_playback_missing_plugin(self):
		# Playlist refers to a plugin that is not in plugin_map
		track = PlaylistSchedule("missing", "t2", "Title2", PlaylistScheduleData({}))
		playlist = Playlist("pl2", "Main2", items=[track])
		self.layer.playlists = [playlist]
		self.layer.plugin_info = []
		self.layer.state = 'loaded'

		# Trigger playback; plugin missing should prevent start
		self.layer.execute(StartPlayback("start"))
		self.assertNotEqual(self.layer.state, 'playing')
		self.assertIsNone(self.layer.playlist_state)


if __name__ == '__main__':
	unittest.main()

