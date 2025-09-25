from flask import Blueprint, render_template

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/test')
def user_list():
	return "Ho-lee cow!"