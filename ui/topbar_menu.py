# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Adds three entries to the topbar Render menu: Render & Encode,
#               Encode Existing Sequence, and a shortcut to the settings
#               panel.
# ------------------------------------------------------------------------------
"""Topbar Render menu integration."""

import bpy


def _draw_render_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("mul.render_and_encode",
                    text="Render & Encode with FFmpeg",
                    icon='RENDER_ANIMATION')
    layout.operator("mul.encode_existing",
                    text="Encode Existing Sequence (Pick First Frame)...",
                    icon='FILE_MOVIE')
    layout.operator("mul.show_ffmpeg_settings",
                    text="FFmpeg Encode Settings...",
                    icon='SETTINGS')


def register_menu():
    bpy.types.TOPBAR_MT_render.append(_draw_render_menu)


def unregister_menu():
    try:
        bpy.types.TOPBAR_MT_render.remove(_draw_render_menu)
    except ValueError:
        pass
