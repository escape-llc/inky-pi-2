import os
from ..model.configuration_manager import ConfigurationManager

def storage_path():
	test_file_path = os.path.abspath(__file__)
	test_directory = os.path.dirname(test_file_path)
	storage = os.path.join(test_directory, ".storage")
	return storage

def create_configuration_manager():
	storage = storage_path()
	cm = ConfigurationManager(storage_path=storage)
	return cm
