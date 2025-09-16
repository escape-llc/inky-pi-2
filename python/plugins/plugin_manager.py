import os
import importlib
import logging
# from utils.app_utils import resolve_path
from pathlib import Path

logger = logging.getLogger(__name__)
PLUGINS_DIR = 'plugins'
PLUGIN_CLASSES = {}
