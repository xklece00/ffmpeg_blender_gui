# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Probes the configured ffmpeg path. Runs `-version` and
#               `-encoders` and stores results in add-on Preferences for
#               other parts of the add-on to read.
# ------------------------------------------------------------------------------
"""Test the configured FFmpeg binary."""

import bpy

from ..class_manager import ClassManager
from ..log_service import LogService
from ..preferences import get_prefs
from .. import ffmpeg_runner

_LOG = LogService.get_logger("operators.test_ffmpeg")


class MUL_OT_TestFFmpeg(bpy.types.Operator):
    """Run ffmpeg -version and -encoders to verify the configured path"""
    bl_idname = "mul.test_ffmpeg"
    bl_label = "Test"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = get_prefs(context)
        if prefs is None:
            self.report({'ERROR'}, "Add-on preferences not available")
            return {'CANCELLED'}

        resolved = ffmpeg_runner.find_ffmpeg(prefs.ffmpeg_path)
        if not resolved:
            self.report({'ERROR'}, "FFmpeg not found at the configured path")
            prefs.detected_version = ""
            prefs.detected_encoders = ""
            return {'CANCELLED'}

        version = ffmpeg_runner.probe_version(resolved)
        if not version:
            self.report({'ERROR'}, "FFmpeg binary did not respond to -version")
            return {'CANCELLED'}

        encoders = ffmpeg_runner.probe_encoders(resolved)
        prefs.detected_version = version
        prefs.detected_encoders = ",".join(sorted(encoders))

        self.report({'INFO'}, f"OK: {version} ({len(encoders)} encoders)")
        return {'FINISHED'}


ClassManager.add_class(MUL_OT_TestFFmpeg)
