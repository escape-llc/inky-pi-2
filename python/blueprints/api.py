from datetime import datetime, date, timedelta
import os
from flask import Blueprint, jsonify, render_template, current_app, send_from_directory, send_file, request
import pytz
import logging

from ..model.schedule import Schedule
from ..model.configuration_manager import ConfigurationManager

logger = logging.getLogger(__name__)
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

@api_bp.route('/schedule/render', methods=['GET'])
def render_schedule():
	"""
	QSP   format  default  description
	days  int     7        number of days to render
	start iso8601 today    starting date (time is ignored) SHOULD include TZ
	"""
	logger.info("GET /schedule/render")
	start_at = request.args.get("start", None)
	days = request.args.get("days", 7, type=int)
	cm = create_cm()
	stm = cm.settings_manager()
	system = stm.load_settings("system")
	tz = pytz.timezone(system.get("timezoneName", "US/Eastern"))
	sm = cm.schedule_manager()
	schedule_info = sm.load()
	sm.validate(schedule_info)
	master_schedule = schedule_info.get("master", None)
	if master_schedule is None:
		return jsonify({"success": False, "error": "Master Schedule not found"}), 404
	schedules = schedule_info.get("schedules", [])
	if schedules is []:
		return jsonify({"success": False, "error": "Schedule List not found"}), 404

	start_ts = datetime.now(tz) if start_at is None else datetime.fromisoformat(start_at)
	start_ts = start_ts.replace(hour=0, minute=0, second=0, microsecond=0)
	end_ts = start_ts + timedelta(days=days)
	schedule_ts = start_ts
	schedule_map = {}
	render_list = []
	while schedule_ts < end_ts:
		for schedule in schedules:
			info = schedule.get("info", None)
			if info is not None and isinstance(info, Schedule):
				info.set_date_controller(lambda: schedule_ts)
		current = master_schedule.evaluate(schedule_ts)
		if current:
			schedule = next((sx for sx in schedules if sx.get("name", None) and sx["name"] == current.schedule), None)
			if schedule and "info" in schedule and isinstance(schedule["info"], Schedule):
				target:Schedule = schedule["info"]
				render = [{ "schedule": target.id, "id":xx.id, "start": xx.start.isoformat(), "end": xx.end.isoformat() } for xx in target.items]
				render_list.extend(render)
				schedule_map.setdefault(target.id, target.to_dict())
		else:
			return jsonify({ "schedule_ts": schedule_ts.isoformat(), "success": False, "error": "Master Schedule evaluate failed"}), 404
		schedule_ts = schedule_ts + timedelta(days=1)
		pass
	retv = {
		"success": True,
		"start_ts": start_ts.isoformat(),
		"end_ts": end_ts.isoformat(),
		"days": days,
		"schedules": schedule_map,
		"render": render_list
	}
	return jsonify(retv)
