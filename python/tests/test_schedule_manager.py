import unittest
import os
import tempfile

from python.model.schedule import MasterSchedule, Schedule
from python.model.schedule_manager import ScheduleManager

class TestScheduleManager(unittest.TestCase):
	def test_load_schedule(self):
		# This is a placeholder test. Actual implementation would depend on the filesystem and schedule structure.
		test_file_path = os.path.abspath(__file__)
		test_directory = os.path.dirname(test_file_path)
		sm = ScheduleManager(root_path=f"{test_directory}/storage/schedules")
		sinfos = sm.load()
		self.assertIsNotNone(sinfos)
		self.assertIn('master', sinfos)
		self.assertIn('schedules', sinfos)
		self.assertGreater(len(sinfos['schedules']), 0)  # Adjust based on expected number of schedules
		for sinfo in sinfos['schedules']:
			self.assertIn('info', sinfo)
			self.assertIn('path', sinfo)
			self.assertIn('name', sinfo)
			self.assertIsInstance(sinfo['path'], str)
			self.assertIsInstance(sinfo['name'], str)
			self.assertIsInstance(sinfo['info'], (Schedule, MasterSchedule))
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
		test_file_path = os.path.abspath(__file__)
		test_directory = os.path.dirname(test_file_path)
		sm = ScheduleManager(root_path=f"{test_directory}/storage/schedules")
		sinfos = sm.load()
		self.assertIsNotNone(sinfos)
		self.assertGreater(len(sinfos), 0)
		sm.validate(sinfos)
		pass
