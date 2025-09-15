from typing import Generic, TypeVar, List
from datetime import datetime, timedelta

T = TypeVar('T')

class SchedulableBase:
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

class Schedule(Generic[T]):
	def __init__(self, name: str, items: List[SchedulableBase] = None, dc: callable = None):
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