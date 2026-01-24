import json
import sys

def read_data_from_json(file_path: str, exit_on_error: bool = True) -> dict:
    """
    Reads data from a JSON configuration file.

    Returns:
        dict: Parsed JSON configuration data.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)
        return config_data
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {file_path}")
        if exit_on_error:
            sys.exit(1)
        else:
            return None
    except json.JSONDecodeError:
        print(f"ERROR: Failed to parse JSON config file: {file_path}")
        if exit_on_error:
            sys.exit(1)
        else:
            return None

"""VARIABLES-----------------------------------------------------------"""
#Path to your config JSON file
CONFIG_FILE_PATH = "backend/core/config.json"

#Load the entire configuration data, the one to be used
config = read_data_from_json(CONFIG_FILE_PATH, exit_on_error=True)
