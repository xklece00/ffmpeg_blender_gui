# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Collects Blender classes from all
#               modules at import time and registers them into Blender.
# ------------------------------------------------------------------------------
"""Central class registry for the add-on."""

import bpy


class ClassManager:
    _classes = []

    @classmethod
    def add_class(cls, klass):
        if klass not in cls._classes:
            cls._classes.append(klass)

    @classmethod
    def register_all(cls):
        for klass in cls._classes:
            try:
                bpy.utils.register_class(klass)
            except ValueError:
                # Already registered, can happen on script reload
                pass

    @classmethod
    def unregister_all(cls):
        for klass in reversed(cls._classes):
            try:
                bpy.utils.unregister_class(klass)
            except (RuntimeError, ValueError):
                pass
