# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Subpanel for audio codec parameters. The panel header also has
#               a checkbox so the user can mute audio without expanding the panel.
# ------------------------------------------------------------------------------
"""Audio codec subpanel."""

import bpy

from ..class_manager import ClassManager
from .. import codecs as _codecs


class MUL_PT_FFmpeg_Audio(bpy.types.Panel):
    bl_label = "Audio"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = 'MUL_PT_FFmpeg'

    def draw_header(self, context):
        self.layout.prop(context.scene.mul_ffmpeg, "audio_enabled", text="")

    def draw(self, context):
        layout = self.layout
        props = context.scene.mul_ffmpeg

        layout.enabled = props.audio_enabled
        layout.prop(props, "audio_codec")

        if props.audio_codec == _codecs.CUSTOM_CODEC_ID:
            col = layout.column(align=True)
            col.label(text="All audio params via Custom Args", icon='INFO')
            col.label(text="(see Advanced > Custom FFmpeg Args)")
            return

        info = _codecs.AUDIO_CODECS.get(props.audio_codec, {})
        if not info.get("lossless", False):
            layout.prop(props, "audio_bitrate")
        layout.prop(props, "audio_sample_rate")


ClassManager.add_class(MUL_PT_FFmpeg_Audio)
