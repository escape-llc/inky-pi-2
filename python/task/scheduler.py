import logging
from datetime import datetime, timedelta

from ..plugins.plugin_base import PluginBase, PluginExecutionContext
from ..model.configuration_manager import ConfigurationManager
from ..model.schedule import MasterSchedule, Schedule
from .application import ConfigureEvent
from .timer_tick import TickMessage
from .basic_task import BasicTask, ExecuteMessage

class Scheduler(BasicTask):
	def __init__(self, name, display_task: BasicTask):
		super().__init__(name)
		if display_task is None:
			raise ValueError("display_task is None")
		self.display_task = display_task
		self.schedules = []
		self.master_schedule:MasterSchedule = None
		self.cm:ConfigurationManager = None
		self.plugin_info = None
		self.plugin_map = None
		self.current_schedule_state = None
		self.state = 'uninitialized'
		self.logger = logging.getLogger(__name__)

	def calculate_current_state(self, schedule_ts: datetime, tick: TickMessage):
		current = self.master_schedule.evaluate(schedule_ts)
		self.logger.info(f"Current schedule {tick.tick_ts}[{tick.tick_number}]{schedule_ts}: {current}")
		if current:
			# locate schedule from items
			self.logger.info(f"Selecting schedule: {current.name} ({current.schedule})")
			schedule = next((sx for sx in self.schedules if sx.get("name", None) and sx["name"] == current.schedule), None)
			if schedule and "info" in schedule and isinstance(schedule["info"], Schedule):
				# get the active time slot
				target:Schedule = schedule["info"]
				timeslot = target.current(schedule_ts)
				self.logger.info(f"Current slot {timeslot}")
				if timeslot:
					if self.plugin_map.get(timeslot.plugin_name, None):
						self.logger.debug(f"Executing plugin '{timeslot.plugin_name}' with args {timeslot.content}")
						plugin = self.plugin_map[timeslot.plugin_name]
						if isinstance(plugin, PluginBase):
							return { "plugin": plugin, "timeslot": timeslot, "schedule": target, "tick": tick, "schedulets": schedule_ts }
						else:
							errormsg = f"Plugin '{timeslot.plugin_name}' is not a valid PluginBase instance."
							self.logger.error(errormsg)
							return { "plugin": plugin, "timeslot": timeslot, "schedule": target, "tick": tick, "schedulets": schedule_ts, "error": errormsg }
					else:
						errormsg = f"Plugin '{timeslot.plugin_name}' is not a valid PluginBase instance."
						self.logger.error(errormsg)
						return { "plugin": None, "timeslot": timeslot, "schedule": target, "tick": tick, "schedulets": schedule_ts, "error": errormsg }
				else:
					self.logger.debug("No timeslot found")
					return { "plugin":None, "timeslot": None, "schedule":target, "tick": tick, "schedulets": schedule_ts }
		return None

	def evaluate_schedule_state(self, schedule_ts: datetime, schedule_state):
		self.logger.debug(f"'{self.name}' evaluate_schedule_state: {self.current_schedule_state} {schedule_state}")
		if self.current_schedule_state is None:
			if schedule_state is not None:
				schedule = schedule_state["schedule"]
				timeslot = schedule_state["timeslot"]
				selected = f"{schedule.id}/{timeslot.id}"
				self.logger.info(f"timeslot starting {selected}")
				self.invoke_plugin_timeslot_start(schedule_ts, schedule_state)
			else:
				self.logger.warning(f"no timeslot selected; current_schedule_state is None")
				pass
			pass
		else:
			if schedule_state is not None:
				pschedule = self.current_schedule_state["schedule"]
				ptimeslot = self.current_schedule_state["timeslot"]
				timeslot = schedule_state["timeslot"]
				schedule = schedule_state["schedule"]
				selected = f"{schedule.id}/{timeslot.id}"
				current = f"{pschedule.id}/{ptimeslot.id}"
				self.logger.debug(f"timeslots selected {selected} current {current}")
				if selected == current:
					self.logger.debug(f"same timeslot {current}")
					self.invoke_plugin_schedule(schedule_ts, schedule_state)
				else:
					self.logger.debug(f"timeslot ending {current}")
					self.invoke_plugin_timeslot_end(schedule_ts, self.current_schedule_state)
					self.logger.debug(f"timeslot starting {selected}")
					self.invoke_plugin_timeslot_start(schedule_ts, schedule_state)
				pass
			else:
				self.logger.warning(f"no timeslot selected; current_schedule_state is not None")
				pass
			pass
		self.current_schedule_state = schedule_state

	def invoke_plugin_timeslot_start(self, schedule_ts: datetime, schedule_state):
		pic = lambda plugin, ctx: plugin.timeslot_start(ctx)
		self.invoke_plugin(schedule_ts, schedule_state, pic)
	def invoke_plugin_timeslot_end(self, schedule_ts: datetime, schedule_state):
		pic = lambda plugin, ctx: plugin.timeslot_end(ctx)
		self.invoke_plugin(schedule_ts, schedule_state, pic)
	def invoke_plugin_schedule(self, schedule_ts: datetime, schedule_state):
		pic = lambda plugin, ctx: plugin.schedule(ctx)
		self.invoke_plugin(schedule_ts, schedule_state, pic)
	def invoke_plugin(self, schedule_ts: datetime, schedule_state, plugin_callback: callable):
		if plugin_callback is None:
			raise ValueError(f"plugin_callback is None")
		if schedule_state.get("error",None) is None:
			if schedule_state.get("plugin", None) is not None and schedule_state.get("timeslot", None) is not None:
				plugin = schedule_state["plugin"]
				timeslot = schedule_state["timeslot"]
				self.logger.debug(f"Executing plugin '{timeslot.plugin_name}' with args {timeslot.content}")
				try:
					psm = self.cm.plugin_storage_manager(timeslot.plugin_name)
					scm = self.cm.settings_manager()
					ctx = PluginExecutionContext(timeslot, scm, psm, schedule_ts, self.display_task)
					plugin_callback(plugin, ctx)
				except Exception as e:
					self.logger.error(f"Error executing plugin '{timeslot.plugin_name}': {e}", exc_info=True)
			else:
				self.logger.error(f"'{self.name}' no plugin was selected.")
		else:
			self.logger.error(f"'{self.name}' {schedule_state['error']}.")

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
			schedule_ts = msg.tick_ts.replace(second=0,microsecond=0)
			for schedule in self.schedules:
				info = schedule.get("info", None)
				if info is not None and isinstance(info, Schedule):
					info.set_date_controller(lambda: schedule_ts)
			schedule_state = self.calculate_current_state(schedule_ts, msg)
			self.logger.info(f"schedule state {msg.tick_ts}[{msg.tick_number}]: {schedule_ts} {schedule_state}")
			self.evaluate_schedule_state(schedule_ts, schedule_state)
			pass
