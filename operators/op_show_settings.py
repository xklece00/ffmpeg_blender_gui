# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Shortcut in the topbar Render menu that
#               opens the FFmpeg Encode panel in the Properties editor.
# ------------------------------------------------------------------------------
"""Show the FFmpeg encode settings panel."""

import bpy

from ..class_manager import ClassManager
from ..log_service import LogService

_LOG = LogService.get_logger("operators.show_settings")


class MUL_OT_ShowSettings(bpy.types.Operator):
    """Switch the Properties editor to the FFmpeg Encode panel"""
    bl_idname = "mul.show_ffmpeg_settings"
    bl_label = "FFmpeg Encode Settings..."
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        # Find any opened Properties editor and switch its context to OUTPUT
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PROPERTIES':
                    for space in area.spaces:
                        if space.type == 'PROPERTIES':
                            try:
                                space.context = 'OUTPUT'
                            except TypeError:
                                pass
                    area.tag_redraw()
                    self.report({'INFO'}, "Opened Output Properties")
                    return {'FINISHED'}

        self.report({'WARNING'}, "No Properties editor visible. Open one and look at Output Properties.")
        return {'CANCELLED'}


ClassManager.add_class(MUL_OT_ShowSettings)
