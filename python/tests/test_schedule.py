import unittest
from datetime import datetime, timedelta
import random
import string

from ..model.schedule import TimedSchedule, PluginSchedule, PluginScheduleData, generate_schedule, generate_trigger_time

def random_plugin_data():
	return PluginScheduleData({
		'value': random.randint(1, 100),
		'info': ''.join(random.choices(string.ascii_letters, k=8))
	})

class TestSchedule(unittest.TestCase):
	def setUp(self):
			now = datetime.now().replace(second=0, microsecond=0)
			self.items = [
					PluginSchedule(
						plugin_name="PluginA",
						id="1",
						title="First",
						start_minutes=0,
						duration_minutes=30,
						content=random_plugin_data()
					),
					PluginSchedule(
						plugin_name="PluginB",
						id="2",
						title="Second",
						start_minutes=25,
						duration_minutes=30,
						content=random_plugin_data()
					),
					PluginSchedule(
						plugin_name="PluginC",
						id="3",
						title="Third",
						start_minutes=60,
						duration_minutes=15,
						content=random_plugin_data()
					),
			]
			self.schedule = TimedSchedule("test-schedule", "TestSchedule", self.items)
			self.schedule.set_date_controller(lambda: now)

	def test_sorted_items(self):
		sorted_items = self.schedule.sorted_items
		self.assertEqual(sorted_items[0].start, min(item.start for item in self.items))
		self.assertEqual(sorted_items[-1].start, max(item.start for item in self.items))

	def test_check_overlap(self):
		# Overlaps with first and second
		overlap_item = PluginSchedule(
			plugin_name="PluginX",
			id="X",
			title="Overlap",
			start_minutes=self.items[0].start_minutes + 20,
			duration_minutes=20,
			content=random_plugin_data()
		)
		offending = self.schedule.check(overlap_item)
		self.assertIsNotNone(offending)
		self.assertIn(offending.id, ["1", "2"])

		# No overlap
		no_overlap_item = PluginSchedule(
			plugin_name="PluginY",
			id="Y",
			title="NoOverlap",
			start_minutes=self.items[2].start_minutes + self.items[2].duration_minutes + 1,
			duration_minutes=10,
			content=random_plugin_data()
		)
		self.assertIsNone(self.schedule.check(no_overlap_item))

	def test_current(self):
		# Should be in first item
		ts = self.items[0].start + timedelta(minutes=10)
		current = self.schedule.current(ts)
		self.assertIsNotNone(current)
		self.assertEqual(current.id, "1")

		# Should be in second item (overlap region)
		ts = self.items[1].start + timedelta(minutes=5)
		current = self.schedule.current(ts)
		self.assertIsNotNone(current)
		self.assertEqual(current.id, "2")

		# Should be None (outside all items)
		ts = self.items[2].end + timedelta(minutes=5)
		self.assertIsNone(self.schedule.current(ts))

	def test_validate(self):
		# Should raise ValueError due to overlap between items 1 and 2
		result = self.schedule.validate()
		self.assertIsNotNone(result)

		# Remove overlap and validate should not raise
		non_overlapping_items = [
				PluginSchedule(
					plugin_name="PluginA",
					id="1",
					title="First",
					start_minutes=self.items[0].start_minutes,
					duration_minutes=10,
					content=random_plugin_data()
				),
				PluginSchedule(
					plugin_name="PluginB",
					id="2",
					title="Second",
					start_minutes=self.items[0].start_minutes + 15,
					duration_minutes=10,
					content=random_plugin_data()
				),
		]
		schedule_no_overlap = TimedSchedule("NoOverlap", non_overlapping_items)
		overlaps = schedule_no_overlap.validate()
		self.assertIsNone(overlaps)

class TestTriggers(unittest.TestCase):
	def test_generate_trigger_time_hourly(self):
		now = datetime(2024, 1, 1, 10, 15)  # Jan 1, 2024, 10:15 AM
		time_config = {
			"type": "hourly",
			"minutes": [0, 30]
		}
		generator = generate_trigger_time(now, time_config)
		expected_times = [
			datetime(2024, 1, 1, 10, 30),
			datetime(2024, 1, 1, 11, 0),
			datetime(2024, 1, 1, 11, 30),
			datetime(2024, 1, 1, 12, 0),
			datetime(2024, 1, 1, 12, 30),
			datetime(2024, 1, 1, 13, 0),
			datetime(2024, 1, 1, 13, 30),
			datetime(2024, 1, 1, 14, 0),
			datetime(2024, 1, 1, 14, 30),
			datetime(2024, 1, 1, 15, 0),
			datetime(2024, 1, 1, 15, 30),
			datetime(2024, 1, 1, 16, 0),
			datetime(2024, 1, 1, 16, 30),
			datetime(2024, 1, 1, 17, 0),
			datetime(2024, 1, 1, 17, 30),
			datetime(2024, 1, 1, 18, 0),
			datetime(2024, 1, 1, 18, 30),
			datetime(2024, 1, 1, 19, 0),
			datetime(2024, 1, 1, 19, 30),
			datetime(2024, 1, 1, 20, 0),
			datetime(2024, 1, 1, 20, 30),
			datetime(2024, 1, 1, 21, 0),
			datetime(2024, 1, 1, 21, 30),
			datetime(2024, 1, 1, 22, 0),
			datetime(2024, 1, 1, 22, 30),
			datetime(2024, 1, 1, 23, 0),
			datetime(2024, 1, 1, 23, 30),
		]
		for expected in expected_times:
			self.assertEqual(next(generator), expected)
		generator = generate_trigger_time(now, time_config)
		for gen in generator:
			self.assertIn(gen, expected_times)

	def test_generate_schedule_daily(self):
		now = datetime(2024, 1, 1, 10, 15)  # Jan 1, 2024, 10:15 AM
		trigger_config = {
			"day": {
				"type": "dayofweek",
				"days": [0,1,2,3,4,5,6]  # Every day
			},
			"time": {
				"type": "hourly",
				"minutes": [0]
			}
		}
		generator = generate_schedule(now, trigger_config)
		expected_times = [
			datetime(2024, 1, 1, 11, 0),
			datetime(2024, 1, 1, 12, 0),
			datetime(2024, 1, 1, 13, 0),
			datetime(2024, 1, 1, 14, 0),
			datetime(2024, 1, 1, 15, 0),
			datetime(2024, 1, 1, 16, 0),
			datetime(2024, 1, 1, 17, 0),
			datetime(2024, 1, 1, 18, 0),
			datetime(2024, 1, 1, 19, 0),
			datetime(2024, 1, 1, 20, 0),
			datetime(2024, 1, 1, 21, 0),
			datetime(2024, 1, 1, 22, 0),
			datetime(2024, 1, 1, 23, 0),
		]
		for expected in expected_times:
			self.assertEqual(next(generator), expected)

		generator = generate_schedule(now, trigger_config)
		for gen in generator:
			self.assertIn(gen, expected_times)

if __name__ == "__main__":
    unittest.main()