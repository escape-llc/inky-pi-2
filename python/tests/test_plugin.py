from datetime import datetime, timedelta
import os
import queue
import unittest
import time
import logging

from ..model.schedule import PluginSchedule, PluginScheduleData
from ..model.configuration_manager import ConfigurationManager
from ..plugins.plugin_base import PluginBase, PluginExecutionContext
from ..task.active_plugin import ActivePlugin
from ..task.message_router import MessageRouter, Route
from ..task.messages import BasicMessage, MessageSink, QuitMessage, StartEvent, StartOptions
from ..task.basic_task import BasicTask
from ..task.timer_tick import TickMessage

class DebugMessageSink(MessageSink):
	def __init__(self):
		self.msg_queue = queue.Queue()
	def send(self, msg: BasicMessage):
		self.msg_queue.put(msg)

class RecordingTask(BasicTask):
	def __init__(self, name):
		super().__init__(name)
		self.msgs = []
		self.logger = logging.getLogger(__name__)

	def execute(self, msg):
		self.logger.debug(f"{self.name}: {msg}")
		self.msgs.append(msg)

TICK_RATE_FAST = 0.05
TICK_RATE_SLOW = 1
TICKS = 60*1

class TestApplication(unittest.TestCase):
	def create_timer_task(self, now, count=10):
		nowx = now.replace(minute=0, second=0, microsecond=0)
		eventlist = [TickMessage(nowx + timedelta(minutes=ix), ix) for ix in range(count)];
		return eventlist

	def run_plugin_schedule(self, item:PluginSchedule, tick_rate = TICK_RATE_FAST):
		eventlist = self.create_timer_task(datetime.now(), TICKS)
		test_file_path = os.path.abspath(__file__)
		test_directory = os.path.dirname(test_file_path)
		storage = os.path.join(test_directory, "storage")
		cm = ConfigurationManager(storage_path=storage)
		plugin_info = cm.enum_plugins()
		plugins = cm.load_plugins(plugin_info)
		plugin:PluginBase = plugins[item.plugin_name]
		self.assertIsNotNone(plugin, "plugin failed")
		psm = cm.plugin_manager(item.plugin_name)
		scm = cm.settings_manager()
		stm = cm.static_manager()
		resolution = [800,480]
		sink = DebugMessageSink()
		display = RecordingTask("FakeDisplay")
		display.start()
		router = MessageRouter()
		router.addRoute(Route("display", [display]))
		active_plugin = ActivePlugin(item.plugin_name, sink)
		resolution = [800,480]
		for event in eventlist:
			ctx = PluginExecutionContext(item, stm, scm, psm, active_plugin, resolution, event.tick_ts, router)
			if event.tick_number == 0:
				plugin.timeslot_start(ctx)
				if active_plugin.state == "ready":
					plugin.schedule(ctx)
			elif event.tick_number == TICKS - 1:
				plugin.timeslot_end(ctx)
			else:
				active_plugin.check_alarm_clock(event.tick_ts)
				if active_plugin.state == "ready":
					plugin.schedule(ctx)
			time.sleep(tick_rate)
			try:
				sinkmsg = sink.msg_queue.get_nowait()
				# dispatch callback
				active_plugin.state = "notify"
				plugin.receive(ctx, sinkmsg)
				active_plugin.notify_complete()
			except queue.Empty as e:
				pass
		active_plugin.shutdown()
		display.send(QuitMessage())
		display.join()
		return display

	def test_image_folder(self):
		content = {
			"folder": "C:\\Users\\johng\\Pictures\\Saved Pictures\\MediaLab\\OpenCV Images",
			"slideshow": True,
			"slideshowMinutes": 15
		}
		plugin_data = PluginScheduleData(content)
		item = PluginSchedule(
			plugin_name="image-folder",
			id="10",
			title="10 Item",
			start_minutes=600,
			duration_minutes=60,
			content=plugin_data
		)
		display = self.run_plugin_schedule(item, TICK_RATE_SLOW)
		self.assertEqual(len(display.msgs), 4, "display.msgs failed")

	def test_year_progress(self):
		content = {}
		plugin_data = PluginScheduleData(content)
		item = PluginSchedule(
			plugin_name="year_progress",
			id="10",
			title="10 Item",
			start_minutes=600,
			duration_minutes=60,
			content=plugin_data
		)
		display = self.run_plugin_schedule(item)
		self.assertEqual(len(display.msgs), 1, "display.msgs failed")

if __name__ == "__main__":
    unittest.main()