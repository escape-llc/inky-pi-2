import logging
import os
import socket
import subprocess
from PIL import Image, ImageDraw, ImageOps

from ..model.configuration_manager import StaticConfigurationManager

logger = logging.getLogger(__name__)

FONTS = {
	"ds-gigi": "DS-DIGI.TTF",
	"napoli": "Napoli.ttf",
	"jost": "Jost.ttf",
	"jost-semibold": "Jost-SemiBold.ttf"
}

def get_ip_address():
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sx:
		sx.connect(("8.8.8.8", 80))
		ip_address = sx.getsockname()[0]
	return ip_address

def get_wifi_name():
	try:
		output = subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
		return output
	except subprocess.CalledProcessError:
		return None

def is_connected():
	"""Check if the Raspberry Pi has an internet connection."""
	try:
		# Try to connect to Google's public DNS server
		socket.create_connection(("8.8.8.8", 53), timeout=2)
		return True
	except OSError:
		return False

def generate_startup_image(stm:StaticConfigurationManager, dimensions=(800,480)):
	bg_color = (255,255,255)
	text_color = (0,0,0)
	width,height = dimensions

	hostname = socket.gethostname()
	ip = get_ip_address()

	image = Image.new("RGBA", dimensions, bg_color)
	image_draw = ImageDraw.Draw(image)

	title_font_size = width * 0.145
	image_draw.text((width/2, height/2), "inkypi", anchor="mm", fill=text_color, font=stm.get_font("Jost", title_font_size))

	text = f"To get started, visit http://{hostname}.local"
	text_font_size = width * 0.032
	image_draw.text((width/2, height*3/4), text, anchor="mm", fill=text_color, font=stm.get_font("Jost", text_font_size))

	return image

def parse_form(request_form):
	request_dict = request_form.to_dict()
	for key in request_form.keys():
		if key.endswith('[]'):
			request_dict[key] = request_form.getlist(key)
	return request_dict

def handle_request_files(request_files, form_data={}):
	allowed_file_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}
	file_location_map = {}
	# handle existing file locations being provided as part of the form data
	for key in set(request_files.keys()):
			is_list = key.endswith('[]')
			if key in form_data:
					file_location_map[key] = form_data.getlist(key) if is_list else form_data.get(key)
	# add new files in the request
	for key, file in request_files.items(multi=True):
			is_list = key.endswith('[]')
			file_name = file.filename
			if not file_name:
					continue

			extension = os.path.splitext(file_name)[1].replace('.', '')
			if not extension or extension.lower() not in allowed_file_extensions:
					continue

			file_name = os.path.basename(file_name)

			file_save_dir = resolve_path(os.path.join("static", "images", "saved"))
			file_path = os.path.join(file_save_dir, file_name)

			# Open the image and apply EXIF transformation before saving
			if extension in {'jpg', 'jpeg'}:
					try:
							with Image.open(file) as img:
									img = ImageOps.exif_transpose(img)
									img.save(file_path)
					except Exception as e:
							logger.warn(f"EXIF processing error for {file_name}: {e}")
							file.save(file_path)
			else:
					# Directly save non-JPEG files
					file.save(file_path)

			if is_list:
					file_location_map.setdefault(key, [])
					file_location_map[key].append(file_path)
			else:
					file_location_map[key] = file_path
	return file_location_map