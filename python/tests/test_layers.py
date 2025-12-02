import unittest

from python.task.playlist_layer import PlaylistLayer, StartPlayback
from python.task.message_router import MessageRouter
from python.plugins.plugin_base import PluginBase
from python.model.schedule import Playlist, PlaylistSchedule, PlaylistScheduleData
from python.tests.utils import create_configuration_manager


class TestPlugin(PluginBase):
	def __init__(self, id, name):
		super().__init__(id, name)
		self.started = False
		self.start_args = None

	# Implement abstract methods as no-ops
	def timeslot_start(self, pec):
		pass
	def timeslot_end(self, pec):
		pass
	def schedule(self, pec):
		pass
	def receive(self, pec, msg):
		pass
	def reconfigure(self, pec, config):
		pass

	# PlaylistLayer expects plugin to expose a `start(track, context)` method
	def start(self, track, context):
		self.started = True
		self.start_args = (track, context)

class PlaylistLayerTests(unittest.TestCase):
	def setUp(self):
		self.router = MessageRouter()
		self.layer = PlaylistLayer("testlayer", self.router)
		self.layer.cm = create_configuration_manager()

	def test_start_playback_success(self):
		# Prepare a plugin and a playlist with one track that references it
		plugin = TestPlugin("p1", "TestPlugin")
		# plugin_map keys are plugin ids used in PlaylistSchedule.plugin_name
		self.layer.plugin_map = {"p1": plugin}

		# Create a playlist with a single PlaylistSchedule track
		track = PlaylistSchedule("p1", "t1", "Title", PlaylistScheduleData({}))
		playlist = Playlist("pl1", "Main", items=[track])
		self.layer.playlists = [playlist]
		self.layer.state = 'loaded'

		# Trigger playback
		self.layer.execute(StartPlayback("start"))

		self.assertEqual(self.layer.state, 'playing')
		self.assertIsNotNone(self.layer.playlist_state)
		self.assertTrue(plugin.started)
		# verify indices set
		self.assertEqual(self.layer.playlist_state['current_playlist_index'], 0)
		self.assertEqual(self.layer.playlist_state['current_track_index'], 0)

	def test_start_playback_no_playlists(self):
		self.layer.playlists = []
		self.layer.plugin_map = {}
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
		self.layer.plugin_map = {}
		self.layer.state = 'loaded'

		# Trigger playback; plugin missing should prevent start
		self.layer.execute(StartPlayback("start"))
		self.assertNotEqual(self.layer.state, 'playing')
		self.assertIsNone(self.layer.playlist_state)


if __name__ == '__main__':
	unittest.main()

