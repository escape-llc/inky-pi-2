import unittest
import os
import tempfile

from .utils import storage_path
from ..model.schedule import MasterSchedule, Playlist, Schedule
from ..model.schedule_manager import ScheduleManager

class TestScheduleManager(unittest.TestCase):
	def test_load_schedule(self):
		# This is a placeholder test. Actual implementation would depend on the filesystem and schedule structure.
		storage = storage_path()
		sm = ScheduleManager(root_path=f"{os.path.join(storage, "schedules")}")
		sinfos = sm.load()
		self.assertIsNotNone(sinfos)
		self.assertIn('master', sinfos)
		self.assertIn('schedules', sinfos)
		self.assertIn('playlists', sinfos)
		self.assertGreater(len(sinfos['schedules']), 0)  # Adjust based on expected number of schedules
		self.assertGreater(len(sinfos['playlists']), 0)  # Adjust based on expected number of playlists
		for sinfo in sinfos['schedules']:
			self.assertIn('info', sinfo)
			self.assertIn('path', sinfo)
			self.assertIn('name', sinfo)
			self.assertIn('type', sinfo)
			self.assertIsInstance(sinfo['path'], str)
			self.assertIsInstance(sinfo['name'], str)
			self.assertIsInstance(sinfo['type'], str)
			self.assertIsInstance(sinfo['info'], Schedule)
		for sinfo in sinfos['playlists']:
			self.assertIn('info', sinfo)
			self.assertIn('path', sinfo)
			self.assertIn('name', sinfo)
			self.assertIn('type', sinfo)
			self.assertIsInstance(sinfo['path'], str)
			self.assertIsInstance(sinfo['name'], str)
			self.assertIsInstance(sinfo['type'], str)
			self.assertIsInstance(sinfo['info'], Playlist)
		info = sinfos['master']
		if isinstance(info, MasterSchedule):
			self.assertIsNotNone(info.defaultSchedule)
			self.assertIsNotNone(info.schedules)
			for item in info.schedules:
				self.assertIsNotNone(item.id)
				self.assertIsNotNone(item.name)
				self.assertIsNotNone(item.enabled)
				self.assertIsNotNone(item.description)
				self.assertIsNotNone(item.schedule)
				self.assertIsNotNone(item.trigger)

	def test_validate(self):
		storage = storage_path()
		sm = ScheduleManager(root_path=f"{os.path.join(storage, "schedules")}")
		sinfos = sm.load()
		self.assertIsNotNone(sinfos)
		self.assertGreater(len(sinfos), 0)
		sm.validate(sinfos)
		pass
