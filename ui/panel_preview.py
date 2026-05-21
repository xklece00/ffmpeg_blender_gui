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

import os
import shlex

import bpy

from ..class_manager import ClassManager
from ..operators.op_copy_command import build_preview_command
from .. import ffmpeg_runner
from .. import codecs as _codecs


# FFmpeg flags people most frequently forget the leading dash on. If we spot
# one of these as a bare token inside Custom Args we surface a hint so the
# user doesn't ship a command where FFmpeg interprets "c:v" as a positional
# input/output filename (which silently breaks with "Invalid argument").
_SUSPICIOUS_NODASH_FLAGS = frozenset({
    "c:v", "c:a", "c:s", "crf", "preset", "pix_fmt", "b:v", "b:a",
    "vf", "af", "filter_complex", "ar", "ac", "movflags", "metadata",
    "tune", "profile:v", "level", "shortest", "map", "r", "framerate",
    "start_number", "i", "y", "n",
})


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

        props = context.scene.mul_ffmpeg

        # Tokenise Custom Args the same way ffmpeg_runner does so detection
        # matches the actual command. shlex can throw on unbalanced quotes -
        # in that case skip the typo check and surface the parse error.
        custom_tokens = []
        custom_parse_error = None
        try:
            custom_tokens = shlex.split(props.custom_cli or "", posix=(os.name != "nt"))
        except ValueError as exc:
            custom_parse_error = str(exc)

        if custom_parse_error:
            layout.label(
                text=f"Custom Args parse error: {custom_parse_error}",
                icon='ERROR',
            )

        # Flag-without-dash typo (e.g. "c:v" instead of "-c:v"). FFmpeg
        # would treat such tokens as positional inputs/outputs and bail.
        bad = [t for t in custom_tokens if t in _SUSPICIOUS_NODASH_FLAGS]
        if bad:
            layout.label(
                text=f"Custom Args: missing dash on {bad[0]!r} (write -{bad[0]})",
                icon='ERROR',
            )

        # When a codec is set to CUSTOM but the user has not supplied a
        # matching -c:v / -c:a in Custom Args, FFmpeg silently falls back
        # to the muxer default (e.g. libx264 for MP4). Surface that. We
        # check the exact "-c:v" / "-c:a" token, not just substring.
        has_cv = "-c:v" in custom_tokens
        has_ca = "-c:a" in custom_tokens
        if props.video_codec == _codecs.CUSTOM_CODEC_ID and not has_cv:
            layout.label(
                text="Tip: video codec is Custom but no -c:v in Custom Args - "
                     "FFmpeg will pick the muxer default.",
                icon='INFO',
            )
        if (props.audio_enabled
                and props.audio_codec == _codecs.CUSTOM_CODEC_ID
                and not has_ca):
            layout.label(
                text="Tip: audio codec is Custom but no -c:a in Custom Args - "
                     "FFmpeg will pick the muxer default.",
                icon='INFO',
            )

        # Output path without a basename - on Windows ".mp4" alone is an
        # invalid filename. _resolve_output_path now patches this by
        # appending "render", but inform the user so they don't end up
        # with a mystery "render.mp4" in their target folder.
        out = (props.output_filepath or "").strip()
        if out:
            ends_sep = out.endswith("/") or out.endswith("\\")
            base = os.path.basename(out.rstrip("/\\"))
            if ends_sep or not base or base.startswith("."):
                layout.label(
                    text="Output File has no filename - will save as 'render'",
                    icon='INFO',
                )

        layout.operator("mul.copy_command", icon='COPYDOWN')


ClassManager.add_class(MUL_PT_FFmpeg_Preview)
