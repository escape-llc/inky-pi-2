from flask import Blueprint, render_template

root_bp = Blueprint('root', __name__)

@root_bp.route('/', defaults={"path":""})
@root_bp.route("/<path:path>")
def index(path):
	return render_template("index.html")