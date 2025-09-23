from queue import ShutDown
import threading
from typing import List

from .basic_task import MessageSink
from .messages import BasicMessage

class Route:
	def __init__(self, name:str, receivers:List[MessageSink]):
		self.name = name
		self.receivers = receivers

class MessageRouter:
	def __init__(self):
		self.routes = {}
		self.lock = threading.Lock()

	def addRoute(self, route:Route):
		with self.lock:
			self.routes.setdefault(route.name, route)

	def send(self, route:str, msg: BasicMessage):
		with self.lock:
			rroute = self.routes.get(route, None)
			if rroute is not None:
				for kx in rroute.receivers:
					try:
						kx.send(msg)
					except ShutDown:
						pass