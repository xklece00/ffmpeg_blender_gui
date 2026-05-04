# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Copies the FFmpeg command that would be executed for the
#               current scene settings into the system clipboard.
# ------------------------------------------------------------------------------
"""Copy the resolved FFmpeg command to the clipboard."""

import os
import bpy

from ..class_manager import ClassManager
from ..log_service import LogService
from ..preferences import get_prefs
from .. import ffmpeg_runner
from .. import codecs as _codecs

_LOG = LogService.get_logger("operators.copy_command")


def build_preview_command(context):
    """Build the ffmpeg argv that the encode operator would run.

    Uses placeholder paths for inputs/outputs to keep the command readable.
    """
    scene = context.scene
    props = scene.mul_ffmpeg
    prefs = get_prefs(context)

    ffmpeg_path = ffmpeg_runner.find_ffmpeg(prefs.ffmpeg_path if prefs else "")
    if not ffmpeg_path:
        ffmpeg_path = "ffmpeg"

    fps = scene.render.fps / max(scene.render.fps_base, 1e-6)
    if props.output_filepath:
        output_path = _codecs.ensure_container_ext(
            bpy.path.abspath(props.output_filepath), props.container
        )
    else:
        output_path = (
            os.path.splitext(bpy.path.abspath(scene.render.filepath) or "render")[0]
            + "." + _codecs.get_container_ext(props.container)
        )
    audio_path = "<audio.wav>" if props.audio_enabled else None
    frame_pattern = "<frames>/frame_%04d.png"

    return ffmpeg_runner.build_command(
        props=props,
        ffmpeg_path=ffmpeg_path,
        frame_pattern=frame_pattern,
        fps=fps,
        audio_path=audio_path,
        output_path=output_path,
        frame_start=scene.frame_start,
        force_audio=bool(props.audio_enabled),
    )


class MUL_OT_CopyCommand(bpy.types.Operator):
    """Copy the FFmpeg command to the clipboard"""
    bl_idname = "mul.copy_command"
    bl_label = "Copy Command"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        cmd = build_preview_command(context)
        text = ffmpeg_runner.command_to_pretty_string(cmd)
        context.window_manager.clipboard = text
        self.report({'INFO'}, "FFmpeg command copied to clipboard")
        return {'FINISHED'}


ClassManager.add_class(MUL_OT_CopyCommand)
