import os
import json
import logging
from typing import List

from .schedule import MasterSchedule, Schedule
from .schedule_loader import ScheduleLoader

logger = logging.getLogger(__name__)

class ScheduleManager:
	def __init__(self, root_path):
		if root_path == None:
			raise ValueError("root_path cannot be None")
		if not os.path.exists(root_path):
			raise ValueError(f"root_path {root_path} does not exist.")
		self.ROOT_PATH = root_path
		logger.debug(f"ROOT_PATH: {self.ROOT_PATH}")

	def load(self):
		master_schedule_file = os.path.join(self.ROOT_PATH, "master_schedule.json")
		if not os.path.isfile(master_schedule_file):
			raise FileNotFoundError(f"Master schedule file '{master_schedule_file}' does not exist.")
		schedule_list:List[Schedule] = []
		master_schedule:MasterSchedule = None
		for schedule in os.listdir(self.ROOT_PATH):
			logger.debug(f"Found schedule: {schedule}")
			schedule_path = os.path.join(self.ROOT_PATH, schedule)
			if schedule.endswith("master_schedule.json"):
				with open(schedule_path, 'r', encoding='utf-8') as f:
					master_schedule = ScheduleLoader.loadMasterFile(schedule_path)
			else:
				schedule_info = ScheduleLoader.loadFile(schedule_path)
				schedule_list.append({ "info":schedule_info, "name":schedule, "path":schedule_path })
		return { "master": master_schedule, "schedules": schedule_list }

	def validate(self, schedule_list):
		if schedule_list is None:
			raise ValueError("schedule_list cannot be None")
		if schedule_list.get("master", None) is None:
			raise ValueError("Master schedule is missing.")
		for schedule in schedule_list.get("schedules", []):
			info = schedule.get("info", None)
			if info is None:
				raise ValueError(f"Schedule info is None for {schedule.get('name', 'unknown')}")
			if isinstance(info, MasterSchedule):
				validation_error = info.validate(schedule_list)
				if validation_error is not None:
					raise ValueError(f"Validation error in master schedule '{schedule.get('name', 'unknown')}': {validation_error}")
			elif isinstance(info, Schedule):
				validation_error = info.validate()
				if validation_error is not None:
					raise ValueError(f"Validation error in schedule '{schedule.get('name', 'unknown')}': {validation_error}")
		pass