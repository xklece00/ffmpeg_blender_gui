# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Wrapper around stdlib logging used by other add-on modules.
# ------------------------------------------------------------------------------
"""Logging helper."""

import logging
import sys

_ROOT = "ffmpeg_gui"


class LogService:
    _initialized = False

    @classmethod
    def _init_root(cls):
        if cls._initialized:
            return
        root = logging.getLogger(_ROOT)
        if not root.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
            root.addHandler(handler)
        root.setLevel(logging.INFO)
        root.propagate = False
        cls._initialized = True

    @staticmethod
    def get_logger(name):
        LogService._init_root()
        return logging.getLogger(f"{_ROOT}.{name}")

    @staticmethod
    def set_debug(enabled):
        LogService._init_root()
        logging.getLogger(_ROOT).setLevel(logging.DEBUG if enabled else logging.INFO)
