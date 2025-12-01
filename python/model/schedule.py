from abc import abstractmethod, ABC
from typing import Generic, TypeVar, List
from datetime import datetime, timedelta

T = TypeVar('T')

class SchedulableBase(ABC):
	def __init__(self, id: str, title: str, start_minutes: int, duration_minutes: int, dc: callable = None):
		self.id = id
		self.title = title
		self.start_minutes = start_minutes
		self.duration_minutes = duration_minutes
		self.date_controller = dc if dc is not None else lambda : datetime.now()
	@property
	def start(self) -> datetime:
		if self.date_controller is None:
			raise ValueError("Date controller is not set")
		# start at midnight
		the_date = self.date_controller().replace(hour=0, minute=0, second=0, microsecond=0)
		return the_date + timedelta(minutes=self.start_minutes)
	@property
	def end(self) -> datetime:
		return self.start + timedelta(minutes=self.duration_minutes)
	@abstractmethod
	def to_dict(self):
		retv = {
			"id": self.id,
			"title": self.title,
			"start_minutes": self.start_minutes,
			"duration_minutes": self.duration_minutes
		}
		return retv

class SchedulableItem(SchedulableBase, Generic[T]):
	def __init__(self, id: str, title: str, start_minutes: int, duration_minutes: int, content: T, dc: callable = None):
		super().__init__(id, title, start_minutes, duration_minutes, dc)
		self.content = content

class PluginScheduleData:
	def __init__(self, data: dict):
		self.data = data

class PluginSchedule(SchedulableItem[PluginScheduleData]):
	def __init__(self, plugin_name: str, id: str, title: str, start_minutes: int, duration_minutes: int, content: PluginScheduleData, dc: callable = None):
		super().__init__(id, title, start_minutes, duration_minutes, content, dc)
		self.plugin_name = plugin_name
	def to_dict(self):
		retv = super().to_dict()
		retv["plugin_name"] = self.plugin_name
		retv["content"] = self.content.data
		return retv

class DefaultItem:
	def __init__(self, plugin_name: str, title: str, content: dict):
		self.plugin_name = plugin_name
		self.title = title
		self.content = content

class MasterScheduleItem:
	def __init__(self, id:str, name:str ,description:str, trigger, enabled:bool, schedule:str):
		self.id = id
		self.name = name
		self.description = description
		self.trigger = trigger
		self.enabled = enabled
		self.schedule = schedule

class MasterSchedule:
	def __init__(self, defaultSchedule: str, schedules: List[MasterScheduleItem]):
		if defaultSchedule is None or schedules is None:
			raise ValueError("default_schedule and schedules cannot be None")
		self.defaultSchedule = defaultSchedule
		self.schedules = schedules

	def validate(self, schedule_infos: List[dict]):
		if schedule_infos is None:
			raise ValueError("schedule_infos cannot be None")
		mscheck = [item for item in schedule_infos if item['name'] == self.defaultSchedule]
		if len(mscheck) != 1:
			return f"Default schedule '{self.defaultSchedule}' does not exist."
		ids = set()
		for item in self.schedules:
			if item.id in ids:
				return f"Duplicate schedule ID found: {item.id}"
			ids.add(item.id)
			sscheck = [sinfo for sinfo in schedule_infos if sinfo['name'] == item.schedule]
			if len(sscheck) != 1:
				return f"Schedule '{item.schedule}' referenced by master schedule item '{item.id}' does not exist."
		return None

	def evaluate(self, now:datetime) -> MasterScheduleItem:
		matching_schedules = []
		for item in self.schedules:
			if item.enabled:
				match item.trigger.get("type", None):
					case "dayofweek":
						days = item.trigger.get("days", [])
						if now.weekday() in days:
							matching_schedules.append(item)
					case "dayofmonth":
						days = item.trigger.get("dayofmonth", None)
						if days is not None and now.day == days:
							matching_schedules.append(item)
					case "dayandmonth":
						day = item.trigger.get("day", None)
						month = item.trigger.get("month", None)
						if day is not None and month is not None and now.day == day and now.month == month:
							matching_schedules.append(item)
					case "dayandmonthrange":
						day_start = item.trigger.get("day_start", None)
						month_start = item.trigger.get("month_start", None)
						day_end = item.trigger.get("day_end", None)
						month_end = item.trigger.get("month_end", None)
						if day_start is not None and month_start is not None and day_end is not None and month_end is not None:
							start_date = datetime(now.year, month_start, day_start, 0, 0, 0)
							end_date = datetime(now.year, month_end, day_end, 23, 59, 59)
							if start_date <= now <= end_date:
								matching_schedules.append(item)
							pass
					case "daymonthyear":
						day = item.trigger.get("day", None)
						month = item.trigger.get("month", None)
						year = item.trigger.get("year", None)
						if day is not None and month is not None and year is not None and now.day == day and now.month == month and now.year == year:
							matching_schedules.append(item)
					case _:
						# Unknown trigger type, ignore
						pass
		return matching_schedules[-1] if matching_schedules else None

class Schedule(Generic[T]):
	def __init__(self, id: str, name: str, items: List[SchedulableBase] = None, dc: callable = None):
		self.id = id
		self.name = name
		self.items = items if items is not None else []
		self.date_controller = dc if dc is not None else lambda : datetime.now()

	@property
	def sorted_items(self) -> List[SchedulableBase]:
		return sorted(self.items, key=lambda item: (item.start, item.end))

	def set_date_controller(self, dc: callable):
		if dc is None:
			raise ValueError("Date controller cannot be None")
		self.date_controller = dc
		for item in self.items:
			item.date_controller = dc

	def check(self, item: SchedulableBase):
		for existing in self.items:
				# Check for overlap: [start1, end1) and [start2, end2) overlap if start1 < end2 and start2 < end1
				if item.start < existing.end and existing.start < item.end:
						return existing
		return None

	def current(self, now: datetime):
		for item in self.items:
			if item.start <= now < item.end:
				return item
		return None

	def validate(self):
		overlaps = []
		lx = len(self.items)
		for ix in range(lx):
				for jx in range(ix + 1, lx):
					ox1 = self.items[ix]
					ox2 = self.items[jx]
					if ox1.start < ox2.end and ox2.start < ox1.end:
						overlaps.append((ox1, ox2))
		if overlaps:
			return overlaps
		return None

	def to_dict(self):
		retv = {
			"id": self.id,
			"name": self.name,
			"items": [xx.to_dict() for xx in self.sorted_items]
		}
		return retv