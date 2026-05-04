# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Add-on Preferences. Stores machine FFmpeg path and
#               cached probe result (version + available encoders) so other
#               modules can read it without spawning a process every time.
# ------------------------------------------------------------------------------
"""Add-on preferences."""

import bpy

from .class_manager import ClassManager


class MUL_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    ffmpeg_path: bpy.props.StringProperty(
        name="FFmpeg Path",
        description="Path to the ffmpeg executable. Leave as 'ffmpeg' to use the binary on PATH",
        subtype='FILE_PATH',
        default="ffmpeg",
    )

    detected_version: bpy.props.StringProperty(
        name="Detected Version",
        description="Filled by the Test FFmpeg button",
        default="",
    )

    detected_encoders: bpy.props.StringProperty(
        name="Detected Encoders",
        description="Comma separated list of encoder ids reported by ffmpeg -encoders",
        default="",
    )

    open_after_encode_default: bpy.props.BoolProperty(
        name="Open Output After Encode",
        description="Default value for the per-scene 'Open after encode' option",
        default=False,
    )

    log_command: bpy.props.BoolProperty(
        name="Log Generated Command",
        description="Print the resolved FFmpeg argv to the system console before each encode",
        default=False,
    )

    def has_encoder(self, encoder_id):
        if not self.detected_encoders:
            return False
        return encoder_id in {e.strip() for e in self.detected_encoders.split(",")}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="FFmpeg Binary", icon='FILE_MOVIE')
        row = box.row()
        row.prop(self, "ffmpeg_path", text="")
        row = box.row(align=True)
        row.operator("mul.detect_ffmpeg", icon='VIEWZOOM')
        row.operator("mul.test_ffmpeg", icon='CHECKMARK')

        if self.detected_version:
            box.label(text=self.detected_version, icon='INFO')
        else:
            box.label(text="Not yet tested. Click 'Test' to verify.", icon='ERROR')

        if self.detected_encoders:
            count = len([e for e in self.detected_encoders.split(",") if e.strip()])
            box.label(text=f"{count} encoders available", icon='PRESET')

        box = layout.box()
        box.label(text="Behavior", icon='SETTINGS')
        box.prop(self, "open_after_encode_default")
        box.prop(self, "log_command")


def get_prefs(context=None):
    ctx = context or bpy.context
    addon = ctx.preferences.addons.get(__package__)
    return addon.preferences if addon else None


ClassManager.add_class(MUL_AddonPreferences)
