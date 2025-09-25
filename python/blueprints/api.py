from flask import Blueprint, jsonify, render_template
import pytz

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/test')
def user_list():
	return "Ho-lee cow!"

@api_bp.route('/lookups/timezone', methods=['GET'])
def list_timezones():
    """Returns a list of all time zones using the pytz library."""
    timezones = sorted(pytz.all_timezones)
    return jsonify(timezones)

@api_bp.route('/lookups/locale', methods=['GET'])
def get_locales():
	"""
	Returns a list of supported locales.
	"""
	locales = [
			{"value": "en-US", "name": "English"},
			{"value": "es-ES", "name": "Español"},
			{"value": "fr-FR", "name": "Français"},
			{"value": "de-DE", "name": "Deutsch"}
	]
	return jsonify(locales)
