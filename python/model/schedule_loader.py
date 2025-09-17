import json
from datetime import datetime
from .schedule import MasterSchedule, MasterScheduleItem, Schedule, PluginSchedule, PluginScheduleData

class ScheduleLoader:
	@staticmethod
	def loadFile(filename: str) -> Schedule:
		with open(filename, 'r', encoding='utf-8') as f:
			data = json.load(f)
		return ScheduleLoader.parse(data)

	@staticmethod
	def loadString(s: str) -> Schedule:
		data = json.loads(s)
		return ScheduleLoader.parse(data)

	def loadMasterFile(filename: str) -> MasterSchedule:
		with open(filename, 'r', encoding='utf-8') as f:
			data = json.load(f)
		return ScheduleLoader.parseMaster(data)

	@staticmethod
	def loadMasterString(s: str) -> MasterSchedule:
		data = json.loads(s)
		return ScheduleLoader.parseMaster(data)

	@staticmethod
	def parseMaster(data: dict) -> MasterSchedule:
		defsched = data.get("defaultSchedule", None)
		schedulesp = data.get("schedules", None)
		if defsched is None or schedulesp is None:
			raise ValueError("Invalid master schedule data")
		schedules = []
		for entry in schedulesp:
			id = entry["id"]
			name = entry.get("name", None)
			description = entry.get("description", None)
			enabled = bool(entry.get("enabled", False))
			schedule = entry.get("schedule", None)
			trigger = entry.get("trigger", None)
			schedules.append(MasterScheduleItem(id, name, description, trigger, enabled, schedule))
		return MasterSchedule(defsched, schedules)

	@staticmethod
	def parse(data: dict) -> Schedule:
		name = data.get("name", "Unnamed Schedule")
		items = []
		for entry in data.get("items", []):
			item_type = entry.get("type", "")
			id = entry["id"]
			title = entry.get("title", "")
			start = int(entry["start_minutes"])
			duration = int(entry["duration_minutes"])

			# Use type field to determine which Python class to instantiate
			if item_type == "PluginSchedule":
				content = entry.get("content", {})
				plugin_name = entry.get("plugin_name", "")
				plugin_data = PluginScheduleData(content)
				item = PluginSchedule(
					plugin_name=plugin_name,
					id=id,
					title=title,
					start_minutes=start,
					duration_minutes=duration,
					content=plugin_data
				)
			else:
				raise ValueError(f"Unknown schedule item type: {item_type}")
			items.append(item)

		return Schedule(name, items)