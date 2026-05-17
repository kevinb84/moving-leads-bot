import logging
import sys
from logging.handlers import RotatingFileHandler
import os
import io

# Force UTF-8 encoding for standard output on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def setup_logger(name="lead_gen"):
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger to catch everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Stream Handler (Console) - Now safer due to sys.stdout wrapping
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)

    # File Handler (Rotating)
    fh = RotatingFileHandler(
        os.path.join(log_dir, "lead_gen.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8' # Explicitly use utf-8 for file logs
    )
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    return logging.getLogger(name)

# Global logger instance
logger = setup_logger()
