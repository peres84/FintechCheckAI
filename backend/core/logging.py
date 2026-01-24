import os
import logging
import sys
import datetime
from pathlib import Path

#Other files imports
from backend.core.config import config

def get_log_directory() -> str:
    """
    Get the log directory path, ensuring it's relative to the project root.
    
    Returns:
        str: Path to the log directory
    """
    log_dir_name = config["logging"]["dir_name"]
    
    # If we're in the backend directory, go up one level for logs
    current_dir = Path.cwd()
    if current_dir.name == "backend":
        project_root = current_dir.parent
        log_directory = project_root / log_dir_name
    else:
        # Assume we're in project root
        log_directory = Path(log_dir_name)
    
    return str(log_directory)

#Map config string levels to logging module levels
LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "notset": logging.NOTSET
}

#Get log level string from config and convert to logging level, default to INFO if not found
log_level_str = config["logging"].get("logging_level", "info").lower()
log_level = LOG_LEVELS.get(log_level_str, logging.INFO)

"""Log basic configuration"""
log_handler = logging.getLogger(config["logging"]["log_file_name"])
log_handler.setLevel(log_level)

"""Logger formatter"""
log_format = logging.Formatter(
    fmt="%(asctime)s %(msecs)03dZ | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

"""File handler (File accessible only when it runs locally)"""
#Create folder
log_directory = get_log_directory()
os.makedirs(log_directory, exist_ok=True)

#Create log file
log_file = os.path.join(
                    log_directory, 
                    datetime.datetime.now().strftime(
                        f"{config["logging"]["log_file_name"]}_%Y-%m-%dT%H-%M-%S.log"))
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(log_format)

"""Console handler for Render logs"""
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)

#Final log handler
if not log_handler.hasHandlers():
    log_handler.addHandler(file_handler)
    log_handler.addHandler(console_handler)

log_handler.info(f"FinTech Check AI backend server starting")
log_handler.warning(f"Current working directory: {os.getcwd()}, Logs are written to '{log_file}'")
