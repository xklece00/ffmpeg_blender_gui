# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Subpanel for advanced user settings, allowing user to add
#               extra command line args, choose whether to keep the intermediate PNG sequence
#               and whether to open the output file in the system player after encoding.
# ------------------------------------------------------------------------------
"""Advanced subpanel."""

import bpy

from ..class_manager import ClassManager


class MUL_PT_FFmpeg_Advanced(bpy.types.Panel):
    bl_label = "Advanced"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = 'MUL_PT_FFmpeg'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.mul_ffmpeg

        col = layout.column(align=True)
        col.label(text="Custom FFmpeg Args (placed before output):")
        col.prop(props, "custom_cli", text="")

        layout.prop(props, "keep_intermediates")
        layout.prop(props, "open_after_encode")


ClassManager.add_class(MUL_PT_FFmpeg_Advanced)
