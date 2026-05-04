# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Automaticaly detects ffmpeg in PATH and writes the resolved path into
#               Add-on Preferences. Also runs a probe so the user immediately
#               sees the version.
# ------------------------------------------------------------------------------
"""Detect FFmpeg from PATH."""

import bpy

from ..class_manager import ClassManager
from ..log_service import LogService
from ..preferences import get_prefs
from .. import ffmpeg_runner

_LOG = LogService.get_logger("operators.detect_ffmpeg")


class MUL_OT_DetectFFmpeg(bpy.types.Operator):
    """Search PATH for an ffmpeg binary"""
    bl_idname = "mul.detect_ffmpeg"
    bl_label = "Auto-Detect (PATH)"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = get_prefs(context)
        if prefs is None:
            self.report({'ERROR'}, "Add-on preferences not available")
            return {'CANCELLED'}

        found = ffmpeg_runner.find_ffmpeg("")
        if not found:
            self.report({'WARNING'}, "FFmpeg not found in PATH. Set the path manually.")
            return {'CANCELLED'}

        prefs.ffmpeg_path = found
        version = ffmpeg_runner.probe_version(found)
        prefs.detected_version = version
        encoders = ffmpeg_runner.probe_encoders(found)
        prefs.detected_encoders = ",".join(sorted(encoders))

        self.report({'INFO'}, f"Detected FFmpeg: {found}")
        return {'FINISHED'}


ClassManager.add_class(MUL_OT_DetectFFmpeg)
