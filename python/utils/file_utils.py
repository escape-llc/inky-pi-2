import os
from urllib.parse import urljoin
from urllib.request import pathname2url

def path_to_file_url(path):
	"""
	Converts a platform-specific file path to a properly formatted file:// URL.
	"""
	# 1. Convert the path to an absolute path to ensure clarity
	absolute_path = os.path.abspath(path)
	# 2. Convert the pathname to a URL path segment (handles slashes and basic encoding)
	url_path = pathname2url(absolute_path)
	# 3. Join with the 'file://' scheme using urljoin to handle scheme-specific logic
	file_url = urljoin('file:', url_path)
	return file_url

