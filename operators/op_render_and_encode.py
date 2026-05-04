# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  The main operator. Renders the active scene animation
#               into a temporary PNG sequence, optionally adds audio
#               from the Sequencer and then runs FFmpeg as non-blocking
#               modal subprocess.
# ------------------------------------------------------------------------------
"""Render & Encode: full pipeline operator."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

import bpy

from ..class_manager import ClassManager
from ..log_service import LogService
from ..preferences import get_prefs
from .. import ffmpeg_runner
from .. import codecs as _codecs

_LOG = LogService.get_logger("operators.render_and_encode")


_DIGITS_AT_END = re.compile(r"(\d+)(?=[^\d]*$)")


def _derive_frame_pattern(scene, frame):
    """Convert Blender frame_path into an ffmpeg printf pattern."""
    path = scene.render.frame_path(frame=frame)
    m = _DIGITS_AT_END.search(path)
    if not m:
        return path
    digits = len(m.group(1))
    return path[:m.start()] + f"%0{digits}d" + path[m.end():]


def _resolve_output_path(scene, props):
    if props.output_filepath:
        return _codecs.ensure_container_ext(
            bpy.path.abspath(props.output_filepath), props.container
        )
    base = bpy.path.abspath(scene.render.filepath) or "render"
    if base.endswith(os.sep) or base.endswith("/"):
        base = base + "render"
    root, _ = os.path.splitext(base)
    return root + "." + _codecs.get_container_ext(props.container)


def _open_file_in_player(path):
    if not path or not os.path.isfile(path):
        return
    try:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError as e:
        _LOG.warning(f"Could not open output file: {e}")


class MUL_OT_RenderAndEncode(bpy.types.Operator):
    """Render the animation and encode it with FFmpeg"""
    bl_idname = "mul.render_and_encode"
    bl_label = "Render & Encode"
    bl_options = {'REGISTER'}

    _process = None
    _timer = None
    _temp_dir = None
    _output_path = None

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        scene = context.scene
        props = scene.mul_ffmpeg
        prefs = get_prefs(context)

        ffmpeg_path = ffmpeg_runner.find_ffmpeg(prefs.ffmpeg_path if prefs else "")
        if not ffmpeg_path:
            self.report({'ERROR'}, "FFmpeg not found. Set the path in Add-on Preferences.")
            return {'CANCELLED'}

        output_path = _resolve_output_path(scene, props)
        if not output_path:
            self.report({'ERROR'}, "Could not resolve an output file path")
            return {'CANCELLED'}

        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        except OSError as e:
            self.report({'ERROR'}, f"Could not create output directory: {e}")
            return {'CANCELLED'}

        self._temp_dir = tempfile.mkdtemp(prefix="mul_ffmpeg_")
        frames_dir = os.path.join(self._temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        # Render PNG sequence into the temp directory
        frame_pattern = self._render_animation(scene, frames_dir)
        if frame_pattern is None:
            self._cleanup_temp()
            self.report({'ERROR'}, "Render did not produce frames (cancelled or failed)")
            return {'CANCELLED'}

        audio_path = self._maybe_mixdown_audio(scene, props)

        fps = scene.render.fps / max(scene.render.fps_base, 1e-6)
        cmd = ffmpeg_runner.build_command(
            props=props,
            ffmpeg_path=ffmpeg_path,
            frame_pattern=frame_pattern,
            fps=fps,
            audio_path=audio_path,
            output_path=output_path,
            frame_start=scene.frame_start,
        )

        if prefs and prefs.log_command:
            print("[FFmpeg GUI] " + ffmpeg_runner.command_to_pretty_string(cmd))

        self._process = ffmpeg_runner.FFmpegProcess(cmd)
        try:
            self._process.start()
        except OSError as e:
            self._cleanup_temp()
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
            self._finish(context, cancelled=True)
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
                self._finish(context, cancelled=False)
                if rc == 0:
                    self.report({'INFO'}, f"Encoded: {self._output_path}")
                    self._maybe_open_output(context)
                    return {'FINISHED'}
                self.report({'ERROR'}, f"FFmpeg exited with code {rc}. Last line: {last}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    # ------------------------------------------------------------------ helpers

    def _render_animation(self, scene, frames_dir):
        """Run a blocking animation render to PNG sequence in frames_dir.

        Returns the printf pattern for ffmpeg, or None on failure.
        """
        original_filepath = scene.render.filepath
        original_format = scene.render.image_settings.file_format
        original_color_mode = scene.render.image_settings.color_mode

        scene.render.filepath = os.path.join(frames_dir, "frame_")
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'

        # frame_path() and frame pattern must both be resolved while the temp
        # filepath is still active; the finally block below restores the user
        # path which would otherwise poison both lookups.
        pattern = _derive_frame_pattern(scene, scene.frame_start)
        first_frame = scene.render.frame_path(frame=scene.frame_start)

        try:
            result = bpy.ops.render.render(animation=True, write_still=False)
        except RuntimeError as e:
            _LOG.error(f"Render failed: {e}")
            result = {'CANCELLED'}
        finally:
            scene.render.filepath = original_filepath
            scene.render.image_settings.file_format = original_format
            scene.render.image_settings.color_mode = original_color_mode

        if 'FINISHED' not in result:
            return None

        if not os.path.isfile(first_frame):
            _LOG.error(f"Expected first frame not found: {first_frame}")
            return None

        return pattern

    def _maybe_mixdown_audio(self, scene, props):
        if not props.audio_enabled:
            return None
        # Skip the mixdown for audio-less containers (e.g. GIF)
        if not _codecs.container_supports_audio(props.container):
            return None
        audio_path = os.path.join(self._temp_dir, "audio.wav")
        try:
            bpy.ops.sound.mixdown(filepath=audio_path, container='WAV', codec='PCM')
        except RuntimeError as e:
            _LOG.warning(f"Audio mixdown failed (no sound strips?): {e}")
            return None
        return audio_path if os.path.isfile(audio_path) else None

    def _finish(self, context, cancelled):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        try:
            context.workspace.status_text_set(None)
        except AttributeError:
            pass
        if not context.scene.mul_ffmpeg.keep_intermediates:
            self._cleanup_temp()
        else:
            _LOG.info(f"Kept intermediates at: {self._temp_dir}")

    def _cleanup_temp(self):
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except OSError as e:
                _LOG.warning(f"Could not remove temp dir: {e}")
        self._temp_dir = None

    def _maybe_open_output(self, context):
        prefs = get_prefs(context)
        wants_open = (context.scene.mul_ffmpeg.open_after_encode
                      or (prefs and prefs.open_after_encode_default))
        if wants_open:
            _open_file_in_player(self._output_path)


ClassManager.add_class(MUL_OT_RenderAndEncode)
