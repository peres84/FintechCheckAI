import json
import sys
import os
from pathlib import Path

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

def find_config_file() -> str:
    """
    Find the config.json file regardless of execution context.
    
    Returns:
        str: Path to the config.json file
    """
    # Get the directory where this config.py file is located
    current_dir = Path(__file__).parent
    config_file = current_dir / "config.json"
    
    if config_file.exists():
        return str(config_file)
    
    # Fallback: try different possible locations
    possible_paths = [
        "backend/core/config.json",  # From project root
        "core/config.json",          # From backend directory
        "../core/config.json",       # From backend subdirectory
        "config.json"                # Current directory
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If none found, return the expected path for better error message
    return str(config_file)

"""VARIABLES-----------------------------------------------------------"""
#Path to your config JSON file
CONFIG_FILE_PATH = find_config_file()

#Load the entire configuration data, the one to be used
config = read_data_from_json(CONFIG_FILE_PATH, exit_on_error=True)
