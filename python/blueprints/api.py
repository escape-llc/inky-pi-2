import os
from flask import Blueprint, jsonify, render_template, current_app, send_from_directory, send_file
import pytz
import logging

logger = logging.getLogger(__name__)

from python.model.configuration_manager import ConfigurationManager

api_bp = Blueprint('api', __name__, url_prefix='/api')

def create_cm():
	root = current_app.config['ROOT_PATH']
	storage = current_app.config['STORAGE_PATH']
	return ConfigurationManager(root_path=root, storage_path=storage)

@api_bp.route('/settings/system', methods=['GET'])
def settings_system():
	logger.info("GET /settings/system")
	cm = create_cm()
	path = os.path.join(cm.storage_settings, "system-settings.json")
	try:
		return send_file(path, mimetype="application/json")
	except FileNotFoundError as e:
		logger.error(f"/schemas/system: {path}: {str(e)}")
		error = { "message": str(e), "path": path }
		return jsonify(error), 404

@api_bp.route('/settings/display', methods=['GET'])
def settings_display():
	logger.info("GET /settings/display")
	cm = create_cm()
	path = os.path.join(cm.storage_settings, "display-settings.json")
	try:
		return send_file(path, mimetype="application/json")
	except FileNotFoundError as e:
		logger.error(f"/schemas/system: {path}: {str(e)}")
		error = { "message": str(e), "path": path }
		return jsonify(error), 404

@api_bp.route('/schemas/system', methods=['GET'])
def schemas_system():
	logger.info("GET /schemas/system")
	cm = create_cm()
	path = os.path.join(cm.storage_schemas, "system.json")
	try:
		return send_file(path, mimetype="application/json")
	except FileNotFoundError as e:
		logger.error(f"/schemas/system: {path}: {str(e)}")
		error = { "message": str(e), "path": path }
		return jsonify(error), 404

@api_bp.route('/schemas/display', methods=['GET'])
def schemas_display():
	logger.info("GET /schemas/display")
	cm = create_cm()
	path = os.path.join(cm.storage_schemas, "display.json")
	try:
		return send_file(path, mimetype="application/json")
	except FileNotFoundError as e:
		logger.error(f"/schemas/display: {path}: {str(e)}")
		error = { "message": str(e), "path": path }
		return jsonify(error), 404

@api_bp.route('/schemas/plugin/<plugin>', methods=['GET'])
def plugin_schema(plugin:str):
	logger.info(f"GET /schemas/plugin{plugin}")
	return "Ho-lee cow!"

@api_bp.route('/plugins/list', methods=['GET'])
def plugins_list():
	cm = create_cm()
	plugins = cm.enum_plugins()
	plist = list(map(lambda x: x.get("info"), plugins))
	return jsonify(plist)

@api_bp.route('/plugins/<plugin>/settings', methods=['GET'])
def plugin_settings(plugin:str):
	logger.info(f"GET /plugins/plugin{plugin}/settings")
	cm = create_cm()
	settings = cm.plugin_manager(plugin).load_settings()
	return jsonify(settings)

@api_bp.route('/lookups/timezone', methods=['GET'])
def list_timezones():
	"""Returns a list of all time zones using the pytz library."""
	logger.info("GET /lookups/timezone")
	timezones = sorted(pytz.all_timezones)
	lookup = list(map(lambda x: { "name": x, "value": x }, timezones))
	return jsonify(lookup)

@api_bp.route('/lookups/locale', methods=['GET'])
def get_locales():
	"""
	Returns a list of supported locales.
	"""
	logger.info("GET /lookups/locale")
	locales = [
		{"value": "en-US", "name": "English"},
		{"value": "es-ES", "name": "Español"},
		{"value": "fr-FR", "name": "Français"},
		{"value": "de-DE", "name": "Deutsch"}
	]
	return jsonify(locales)
