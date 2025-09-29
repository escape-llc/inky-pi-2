#!/usr/bin/env python3

# run from root folder
# python3 -m python.eink-billboard --dev --host localhost --storage ./.storage
# set up logging
import os, logging.config

from python.model.configuration_manager import ConfigurationManager

from .blueprints.root import root_bp
from .blueprints.api import api_bp
from .task.telemetry_sink import TelemetrySink
from .task.application import Application, StartEvent, StopEvent
from .task.messages import QuitMessage, StartOptions
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'config', 'logging.conf'))

# suppress warning from inky library https://github.com/pimoroni/inky/issues/205
import warnings
warnings.filterwarnings("ignore", message=".*Busy Wait: Held high.*")

import random
import logging
import argparse
#from utils.app_utils import generate_startup_image
from flask import Flask, request
from werkzeug.serving import is_running_from_reloader
# from config import Config
#from jinja2 import ChoiceLoader, FileSystemLoader
from waitress import serve

logger = logging.getLogger(__name__)

# Parse command line arguments
APPNAME = "EInk Billboard"
parser = argparse.ArgumentParser(description=f"{APPNAME} Server")
parser.add_argument('--dev', action='store_true', help='Run in development mode')
parser.add_argument('--host', help='Change listening interface')
parser.add_argument('--app', help='Path to web app bundle')
parser.add_argument('--storage', help='Path to storage folder')
args = parser.parse_args()

# development mode
if args.dev:
#    Config.config_file = os.path.join(Config.BASE_DIR, "config", "device_dev.json")
	DEV_MODE = True
	PORT = 8080
	logger.info(f"Starting {APPNAME} in DEVELOPMENT mode on port 8080")
else:
	DEV_MODE = False
	PORT = 80
	logger.info(f"Starting {APPNAME} in PRODUCTION mode on port 80")

# listening interface
HOST = "0.0.0.0"
if args.host:
	HOST = args.host
	logger.info(f"HOST {HOST}")

# app bundle path
PATH = "../app/dist"
if args.app:
	PATH = args.app
	logger.info(f"PATH {PATH}")

STORAGE = None
if args.storage:
	STORAGE = args.storage
	logger.info(f"STORAGE {STORAGE}")

logging.getLogger('waitress.queue').setLevel(logging.ERROR)
app = Flask(__name__, static_folder=f"{PATH}/static", template_folder=f"{PATH}", static_url_path="/static")
template_dirs = [
   os.path.join(os.path.dirname(__file__), "templates"),    # Default template folder
   os.path.join(os.path.dirname(__file__), "plugins"),      # Plugin templates
]
# app.jinja_loader = ChoiceLoader([FileSystemLoader(directory) for directory in template_dirs])

# Set additional parameters
app.config['MAX_FORM_PARTS'] = 10_000

# Register Blueprints
app.register_blueprint(root_bp)
app.register_blueprint(api_bp)

if __name__ == '__main__':
	# display default inkypi image on startup
#	if device_config.get_config("startup") is True:
#		logger.info("Startup flag is set, displaying startup image")
#		img = generate_startup_image(device_config.get_resolution())
#		display_manager.display_image(img)
#		device_config.update_value("startup", False, write=True)

	try:
		cm = ConfigurationManager(storage_path=STORAGE)
		# start the application layer
		sink = TelemetrySink()
		xapp = Application(APPNAME, sink)
		xapp.start()
		options = StartOptions(storagePath=STORAGE)
		xapp.send(StartEvent(options))
		started = xapp.started.wait(timeout=5)
		if not started:
			logger.warning(f"Application start timed out")
		else:
			logger.info("Application is started")
		app.config['APPLICATION'] = xapp
		app.config['TELEMETRY'] = sink
		app.config['ROOT_PATH'] = cm.ROOT_PATH
		app.config['STORAGE_PATH'] = cm.STORAGE_PATH

		msg = sink.receive()
		while msg is not None:
			logger.warning(f"startup message {msg}")
			msg = sink.receive()

		# Run the Flask app
		app.secret_key = str(random.randint(100000,999999))

		# Get local IP address for display (only in dev mode when running on non-Pi)
		if DEV_MODE:
			import socket
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(("8.8.8.8", 80))
				local_ip = s.getsockname()[0]
				s.close()
				logger.info(f"Serving on http://{local_ip}:{PORT}")
			except:
				pass  # Ignore if we can't get the IP

		serve(app, host=HOST, port=PORT, threads=1)
	except Exception as e:
		logger.error(f"Exception in main: {e}", exc_info=True)
	finally:
		app.send(QuitMessage())
		app.join(timeout=5)
		logger.info("InkyPi application has shut down")