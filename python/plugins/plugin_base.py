class PluginBase:
	def __init__(self, id, name):
		self.id = id
		self.name = name
	def schedule(self):
		pass
	def receive(self, msg):
		pass
	def reconfigure(self, config):
		pass