# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Encodes an already rendered image sequence. The user selects
#               first frame, the operator derives the printf style FFmpeg
#               pattern from it and reuses the same PropertyGroup as the
#               render-and-encode pipeline.
# ------------------------------------------------------------------------------
"""Encode an existing image sequence with FFmpeg."""

import os
import re

import bpy

from ..class_manager import ClassManager
from ..log_service import LogService
from ..preferences import get_prefs
from .. import ffmpeg_runner
from .. import codecs as _codecs

_LOG = LogService.get_logger("operators.encode_existing")


_TRAILING_DIGITS = re.compile(r"(\d+)(?=[^\d]*$)")

# Audio file name produced in Render & Encode
_SIBLING_AUDIO_NAMES = ("audio.wav", "audio.flac", "audio.mp3")


def _split_pattern_and_start(picked_file):
    """Given a file like '.../frame_0001.png', return (pattern, start_frame)."""
    m = _TRAILING_DIGITS.search(picked_file)
    if not m:
        return picked_file, 0
    digits = len(m.group(1))
    start = int(m.group(1))
    pattern = picked_file[:m.start()] + f"%0{digits}d" + picked_file[m.end():]
    return pattern, start


def _find_sibling_audio(picked_file):
    """Look for an audio file produced alongside an image sequence.

    Two locationssearched:
      1. The directory containing the sequence (audio next to the frames).
      2. The parent of that directory (Render & Encode pipeline).
    Returns the absolute path or empty string when nothing found.
    """
    if not picked_file:
        return ""
    seq_dir = os.path.dirname(picked_file)
    parent_dir = os.path.dirname(seq_dir)
    for base in (seq_dir, parent_dir):
        if not base:
            continue
        for name in _SIBLING_AUDIO_NAMES:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate):
                return candidate
    return ""


class MUL_OT_EncodeExisting(bpy.types.Operator):
    """Encode an existing image sequence with FFmpeg.

Opens a file browser - user selects the FIRST frame of the sequence
(e.g. frame_0001.png). The trailing frame number is detected automatically
and the rest of the sequence is consumed in order.

If an ``audio.wav`` (or .flac/.mp3) is found next to the sequence or
one directory above, it is automatically added to the output"""
    bl_idname = "mul.encode_existing"
    bl_label = "Encode Existing Sequence (Pick First Frame)..."
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name="First Frame",
        description="First frame of the image sequence (e.g. frame_0001.png)",
        subtype='FILE_PATH',
    )
    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.exr;*.bmp",
        options={'HIDDEN'},
    )

    _process = None
    _timer = None
    _output_path = None

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        # Rendered in the right side panel of the file browser. Used to
        # tell the user that only the first frame should be picked
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Pick the FIRST frame of the sequence", icon='INFO')
        col.label(text="Example: frame_0001.png")
        col.separator()
        col.label(text="The frame number and its zero-padding")
        col.label(text="are detected automatically from the name.")

        # Live preview of audio auto detection
        audio_box = layout.box()
        col = audio_box.column(align=True)
        detected = _find_sibling_audio(self.filepath) if self.filepath else ""
        if detected:
            col.label(text="Audio detected and will be muxed in:", icon='SOUND')
            col.label(text=os.path.basename(detected))
            col.label(text="(disable in panel: Audio > Include Audio)")
        else:
            col.label(text="No sibling audio file detected", icon='MUTE_IPO_OFF')
            col.label(text="(looks for audio.wav next to or above")
            col.label(text=" the picked frame; output will be silent)")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Encode settings come from", icon='PROPERTIES')
        col.label(text="Properties > Output > FFmpeg Encode")

    def execute(self, context):
        scene = context.scene
        props = scene.mul_ffmpeg
        prefs = get_prefs(context)

        if not self.filepath or not os.path.isfile(self.filepath):
            self.report({'ERROR'}, "Pick a valid first-frame image")
            return {'CANCELLED'}

        ffmpeg_path = ffmpeg_runner.find_ffmpeg(prefs.ffmpeg_path if prefs else "")
        if not ffmpeg_path:
            self.report({'ERROR'}, "FFmpeg not found. Set the path in Add-on Preferences.")
            return {'CANCELLED'}

        pattern, start_frame = _split_pattern_and_start(self.filepath)

        audio_path = ""
        if props.audio_enabled:
            audio_path = _find_sibling_audio(self.filepath)
            if audio_path:
                _LOG.info(f"Found sibling audio file: {audio_path}")
                self.report({'INFO'}, f"Picking up audio: {os.path.basename(audio_path)}")

        if props.output_filepath:
            output_path = _codecs.ensure_container_ext(
                bpy.path.abspath(props.output_filepath), props.container
            )
        else:
            root, _ = os.path.splitext(self.filepath)
            root = re.sub(r"_?\d+$", "", root)
            output_path = root + "." + _codecs.get_container_ext(props.container)

        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        except OSError as e:
            self.report({'ERROR'}, f"Could not create output directory: {e}")
            return {'CANCELLED'}

        fps = scene.render.fps / max(scene.render.fps_base, 1e-6)

        cmd = ffmpeg_runner.build_command(
            props=props,
            ffmpeg_path=ffmpeg_path,
            frame_pattern=pattern,
            fps=fps,
            audio_path=audio_path or None,
            output_path=output_path,
            frame_start=start_frame,
        )

        if prefs and prefs.log_command:
            print("[FFmpeg GUI] " + ffmpeg_runner.command_to_pretty_string(cmd))

        self._process = ffmpeg_runner.FFmpegProcess(cmd)
        try:
            self._process.start()
        except OSError as e:
            self.report({'ERROR'}, f"Failed to spawn FFmpeg: {e}")
            return {'CANCELLED'}

        self._output_path = output_path
        self._timer = context.window_manager.event_timer_add(0.25, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Encoding started. Press Esc to cancel.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._process.cancel()
            self._finish(context)
            self.report({'WARNING'}, "Encoding cancelled by user")
            return {'CANCELLED'}

        if event.type == 'TIMER':
            for line in self._process.drain_lines():
                progress = ffmpeg_runner.parse_progress(line)
                if progress is not None:
                    msg = (f"FFmpeg: frame {progress['frame']}  "
                           f"@ {progress['fps']:.1f} fps  "
                           f"time {progress['time']}")
                    context.workspace.status_text_set(msg)

            if not self._process.is_running():
                rc = self._process.returncode
                last = self._process.last_line
                self._finish(context)
                if rc == 0:
                    self.report({'INFO'}, f"Encoded: {self._output_path}")
                    return {'FINISHED'}
                self.report({'ERROR'}, f"FFmpeg exited with code {rc}. Last line: {last}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        try:
            context.workspace.status_text_set(None)
        except AttributeError:
            pass


ClassManager.add_class(MUL_OT_EncodeExisting)
