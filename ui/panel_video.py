# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Subpanel of the main panel with video codecvparameters.
#               Properties only appear if the selected codec actually supports them.
# ------------------------------------------------------------------------------
"""Video codec subpanel."""

import bpy

from ..class_manager import ClassManager
from .. import codecs as _codecs


class MUL_PT_FFmpeg_Video(bpy.types.Panel):
    bl_label = "Video"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = 'MUL_PT_FFmpeg'

    def draw(self, context):
        layout = self.layout
        props = context.scene.mul_ffmpeg
        codec = props.video_codec

        layout.prop(props, "video_codec")

        if _codecs.codec_supports_param(codec, "rate_mode"):
            layout.prop(props, "rate_mode")

            mode = props.rate_mode
            if mode == "CRF" and _codecs.codec_supports_param(codec, "crf"):
                low, high = _codecs.VIDEO_CODECS[codec]["crf_range"]
                row = layout.row()
                row.prop(props, "crf", slider=True)
                row.label(text=f"({low}-{high})")
            elif mode in ("CBR", "VBR") and _codecs.codec_supports_param(codec, "bitrate"):
                layout.prop(props, "bitrate")

        if _codecs.codec_supports_param(codec, "preset"):
            layout.prop(props, "preset")

        if _codecs.codec_supports_param(codec, "pix_fmt"):
            layout.prop(props, "pix_fmt")

        if _codecs.codec_supports_param(codec, "profile"):
            layout.prop(props, "profile")

        if _codecs.codec_supports_param(codec, "two_pass"):
            layout.prop(props, "two_pass")


ClassManager.add_class(MUL_PT_FFmpeg_Video)
