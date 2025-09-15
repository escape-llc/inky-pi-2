import unittest
import tempfile
import json
from datetime import datetime, timedelta

from python.model.schedule_loader import ScheduleLoader

class TestScheduleLoader(unittest.TestCase):
    def test_load_schedule_from_json(self):
        # Create a temporary JSON file with schedule data
        now = datetime.now().replace(second=0, microsecond=0)
        schedule_data = {
            "name": "Test Schedule",
            "items": [
                {
                    "type": "PluginSchedule",
                    "plugin_name": "PluginA",
                    "id": "1",
                    "title": "First Item",
                    "start_minutes": 0,
                    "duration_minutes": 30,
                    "content": {"key": "value1"}
                },
                {
                    "type": "PluginSchedule",
                    "plugin_name": "PluginB",
                    "id": "2",
                    "title": "Second Item",
                    "start_minutes": 30,
                    "duration_minutes": 30,
                    "content": {"key": "value2"}
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
            json.dump(schedule_data, tmp)
            tmp.flush()
            filename = tmp.name

        # Load the schedule using ScheduleLoader
        schedule = ScheduleLoader.loadFile(filename)

        # Assertions
        self.assertEqual(schedule.name, "Test Schedule")
        self.assertEqual(len(schedule.items), 2)
        self.assertEqual(schedule.items[0].id, "1")
        self.assertEqual(schedule.items[1].id, "2")
        self.assertEqual(schedule.items[0].title, "First Item")
        self.assertEqual(schedule.items[1].content.data["key"], "value2")

if __name__ == "__main__":
    unittest.main()