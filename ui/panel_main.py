# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Main FFmpeg Encode panel inside Properties > Output.
#               Shows the FFmpeg status, container selection, derived render
#               settings inherited from the scene and action buttons.
# ------------------------------------------------------------------------------
"""Top-level Output Properties panel."""

import bpy

from ..class_manager import ClassManager
from ..preferences import get_prefs
from .. import codecs as _codecs


class MUL_PT_FFmpeg(bpy.types.Panel):
    """FFmpeg encode settings, lives in Properties > Output."""
    bl_label = "FFmpeg Encode"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 100

    def draw_header(self, context):
        prefs = get_prefs(context)
        if prefs and prefs.detected_version:
            self.layout.label(text="", icon='CHECKMARK')
        else:
            self.layout.label(text="", icon='ERROR')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.mul_ffmpeg
        prefs = get_prefs(context)

        # FFmpeg status row
        status_box = layout.box()
        if prefs and prefs.detected_version:
            row = status_box.row()
            row.label(text=prefs.detected_version, icon='FILE_MOVIE')
            if prefs.detected_encoders:
                detected_set = {
                    e.strip() for e in prefs.detected_encoders.split(",") if e.strip()
                }
                vid_avail = sum(1 for c in _codecs.VIDEO_CODECS if c in detected_set)
                aud_avail = sum(1 for c in _codecs.AUDIO_CODECS if c in detected_set)
                vid_total = len(_codecs.VIDEO_CODECS)
                aud_total = len(_codecs.AUDIO_CODECS)
                ffmpeg_total = len(detected_set)

                sub = status_box.column(align=True)
                sub.scale_y = 0.7
                sub.label(
                    text=(
                        f"Curated codecs available on this FFmpeg: "
                        f"{vid_avail}/{vid_total} video, {aud_avail}/{aud_total} audio"
                    ),
                    icon='FILTER',
                )
                sub.label(
                    text=(
                        f"(Dropdowns also filter by container; your FFmpeg lists "
                        f"{ffmpeg_total} encoders in total.)"
                    )
                )
            else:
                warn = status_box.column(align=True)
                warn.scale_y = 0.7
                warn.label(text="Encoder list not probed - showing all known codecs.",
                           icon='QUESTION')
                warn.label(text="Click Test in Preferences to filter the dropdowns.")
        else:
            col = status_box.column(align=True)
            col.label(text="FFmpeg is not configured.", icon='ERROR')
            col.label(text="Open Add-on Preferences to detect or set the path.")
            col.operator("screen.userpref_show", text="Open Preferences", icon='PREFERENCES')

        # Container and output path
        col = layout.column(align=True)
        col.prop(props, "container")
        col.prop(props, "output_filepath", text="Output File")

        # Display render info
        info_box = layout.box()
        info_box.label(text="Inherited from Render:", icon='INFO')
        col = info_box.column(align=True)
        fps = scene.render.fps / max(scene.render.fps_base, 1e-6)
        col.label(text=f"Resolution: {scene.render.resolution_x} x {scene.render.resolution_y}")
        col.label(text=f"FPS: {fps:.3g}")
        col.label(text=f"Frames: {scene.frame_start} - {scene.frame_end}")

        layout.separator()

        # Buttons
        primary = layout.row()
        primary.scale_y = 1.5
        primary.operator("mul.render_and_encode", icon='RENDER_ANIMATION')

        secondary = layout.column(align=True)
        secondary.operator("mul.encode_existing", icon='FILE_MOVIE')
        hint = secondary.row()
        hint.scale_y = 0.7
        hint.label(text="Pick the first frame; the rest is auto-detected", icon='INFO')


ClassManager.add_class(MUL_PT_FFmpeg)
