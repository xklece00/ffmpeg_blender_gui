# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Subpanel that renders read-only preview of the resolved
#               FFmpeg command line so the user always sees what is going to
#               run or can copy the command.
# ------------------------------------------------------------------------------
"""FFmpeg command preview subpanel."""

import bpy

from ..class_manager import ClassManager
from ..operators.op_copy_command import build_preview_command
from .. import ffmpeg_runner


def _wrap(text, width=64):
    """Wrap a long command into chunks at flag boundaries when possible."""
    out = []
    current = ""
    for token in text.split(" "):
        if not current:
            current = token
            continue
        if len(current) + 1 + len(token) > width:
            out.append(current)
            current = token
        else:
            current += " " + token
    if current:
        out.append(current)
    return out


class MUL_PT_FFmpeg_Preview(bpy.types.Panel):
    bl_label = "Command Preview"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = 'MUL_PT_FFmpeg'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        try:
            cmd = build_preview_command(context)
            pretty = ffmpeg_runner.command_to_pretty_string(cmd)
        except Exception:
            layout.label(text="(no preview)", icon='ERROR')
            return

        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8
        for line in _wrap(pretty, width=64):
            col.label(text=line)

        layout.operator("mul.copy_command", icon='COPYDOWN')


ClassManager.add_class(MUL_PT_FFmpeg_Preview)
