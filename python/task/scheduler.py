import logging
from datetime import datetime, timedelta

from ..model.configuration_manager import ConfigurationManager
from ..model.schedule import MasterSchedule, Schedule
from .application import ConfigureEvent
from .timer_tick import TickMessage
from .basic_task import BasicTask, ExecuteMessage

class Scheduler(BasicTask):
	def __init__(self, name=None):
		super().__init__(name)
		self.logger = logging.getLogger(__name__)
		self.schedules = []
		self.master_schedule:MasterSchedule = None
		self.cm:ConfigurationManager = None
		self.plugin_info = None
		self.plugin_map = None
		self.state = 'uninitialized'

	def execute(self, msg: ExecuteMessage):
		# Handle scheduling messages here
		self.logger.info(f"'{self.name}' received message: {msg}")
		if isinstance(msg, ConfigureEvent):
			self.cm = msg.content.cm
			try:
				plugin_info = self.cm.enum_plugins()
				plugins = self.cm.load_plugins(plugin_info)
				self.logger.info(f"Plugins loaded: {list(plugins.keys())}")
				self.plugin_info = plugin_info
				self.plugin_map = plugins
				sm = self.cm.schedule_manager()
				schedule_info = sm.load()
				sm.validate(schedule_info)
				self.master_schedule = schedule_info.get("master", None)
				self.schedules = schedule_info.get("schedules", [])
				self.logger.info(f"schedule loaded")
				self.state = 'loaded'
			except Exception as e:
				self.logger.error(f"Failed to load/validate schedules: {e}", exc_info=True)
				self.state = 'error'
		elif isinstance(msg, TickMessage):
			# Perform scheduled tasks
			if self.state != 'loaded':
				self.logger.warning(f"'{self.name}' waiting for configuration. Current state: {self.state}")
				return
			if self.master_schedule is None:
				self.logger.error(f"'{self.name}' has no schedule loaded.")
				return
			# for now; at some point there is another level of mapping from day->schedule
			now = datetime.now()
			for schedule in self.schedules:
				info = schedule.get("info", None)
				if info is not None and isinstance(info, Schedule):
					info.set_date_controller(lambda: msg.tick_ts)
					break
			current = self.master_schedule.evaluate(msg.tick_ts)
			self.logger.info(f"Current schedule {msg.tick_ts}[{msg.tick_number}]: {current}")
			if current:
				# Here you would trigger the actual task associated with the current schedule item
				self.logger.info(f"Selecting schedule: {current.name} ({current.schedule})")
				schedule = next((s for s in self.schedules if s.get("name", None) and s["name"] == current.schedule), None)
				if schedule and "info" in schedule and isinstance(schedule["info"], Schedule):
					# Execute the schedule's tasks
					target:Schedule = schedule["info"]
					timeslot = target.current(msg.tick_ts)
					self.logger.info(f"Current slot {timeslot}")
					if timeslot:
						self.logger.info(f"Selecting slot '{timeslot.title}'")
						# Placeholder for actual task execution logic
						if self.plugin_map.get(timeslot.plugin_name, None):
							self.logger.info(f"Executing plugin '{timeslot.plugin_name}' with args {timeslot.content}")
							# Here you would call the plugin's execute method or similar
							plugin = self.plugin_map[timeslot.plugin_name]
							try:
								plugin.execute(timeslot.content)
							except Exception as e:
								self.logger.error(f"Error executing plugin '{timeslot.plugin_name}': {e}", exc_info=True)
						else:
							self.logger.error(f"Plugin '{timeslot.plugin_name}' not found.")
			pass
