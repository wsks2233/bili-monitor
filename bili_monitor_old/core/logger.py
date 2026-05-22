# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import LoggerConfig


def setup_logger(config: Optional[LoggerConfig] = None) -> logging.Logger:
    if config is None:
        config = LoggerConfig()
    
    logger = logging.getLogger('bili-monitor')
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    if logger.handlers:
        logger.handlers.clear()
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    log_dir = os.path.dirname(config.file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        config.file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    file_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger
