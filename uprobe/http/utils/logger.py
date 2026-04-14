import logging
import sys
from pathlib import Path
from datetime import datetime
from uprobe.http.utils.paths import get_data_dir

class MonthlyDirFileHandler(logging.Handler):
    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.current_date = None
        self.file_handler = None
        
    def _get_handler(self):
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        if self.current_date != date_str:
            if self.file_handler:
                self.file_handler.close()
            
            log_dir = self.base_dir / f"{now.year:04d}" / f"{now.month:02d}"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"server_{date_str}.log"
            
            self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
            self.file_handler.setFormatter(self.formatter)
            self.current_date = date_str
            
        return self.file_handler

    def emit(self, record):
        try:
            handler = self._get_handler()
            handler.emit(record)
        except Exception:
            self.handleError(record)
            
    def close(self):
        if self.file_handler:
            self.file_handler.close()
        super().close()

class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            line = line.strip()
            if line:
                # Remove granian's internal log prefixes if present to avoid duplication
                if line.startswith("[INFO] "):
                    line = line[7:]
                elif line.startswith("[WARN] "):
                    line = line[7:]
                elif line.startswith("[ERROR] "):
                    line = line[8:]
                
                # Remove granian's internal timestamp prefix for access logs
                # e.g. "[2026-04-08 00:10:05 +0800] 127.0.0.1 - ..."
                import re
                line = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}\]\s*', '', line)
                
                # Skip empty lines after stripping
                if not line.strip():
                    continue
                    
                self.logger.log(self.level, line)

    def flush(self):
        pass

    def isatty(self):
        return False

def setup_logging():

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Use sys.__stdout__ to avoid infinite recursion when redirecting sys.stdout
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    data_dir = get_data_dir()
    base_log_dir = data_dir / "logs" / "server"
    
    file_handler = MonthlyDirFileHandler(base_log_dir)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Redirect stdout and stderr to logging
    sys.stdout = StreamToLogger(logging.getLogger('Server'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('Server'), logging.ERROR)

    # Ensure granian, uvicorn and fastapi loggers use our handlers and don't duplicate
    for logger_name in ("granian", "granian.access", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers = [console_handler, file_handler]
        logger.propagate = False
