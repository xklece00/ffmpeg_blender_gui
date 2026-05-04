# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  FFmpeg discovery (which / -version / -encoders), command
#               builder that translates PropertyGroup into argv
#               and a wrapper around subprocess.
# ------------------------------------------------------------------------------
"""FFmpeg discovery, command builder and subprocess wrapper."""

import os
import re
import shlex
import shutil
import subprocess
import threading
import queue

from .log_service import LogService
from . import codecs as _codecs

_LOG = LogService.get_logger("ffmpeg_runner")

# Hide console window on Windows when launching ffmpeg from a Blender process
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_ffmpeg(custom_path=""):
    """Find usable FFmpeg binary.

    custom_path is used first if provided, otherwise PATH is searched.
    Returns absolute path string, or empty string when nothing is usable.
    """
    if custom_path:
        custom_path = os.path.expanduser(custom_path)
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return os.path.realpath(custom_path)
        # On Windows the user may have typed without .exe
        if os.name == "nt" and os.path.isfile(custom_path + ".exe"):
            return os.path.realpath(custom_path + ".exe")

    found = shutil.which("ffmpeg")
    if found:
        return os.path.realpath(found)

    return ""


def probe_version(ffmpeg_path):
    """Run `ffmpeg -version` and return the first line, or empty string."""
    if not ffmpeg_path:
        return ""
    try:
        res = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-version"],
            capture_output=True, text=True, timeout=5, check=False,
            creationflags=_CREATE_NO_WINDOW,
        )
        first = (res.stdout or "").strip().splitlines()
        return first[0] if first else ""
    except (OSError, subprocess.SubprocessError) as e:
        _LOG.warning(f"FFmpeg probe failed: {e}")
        return ""


_ENCODER_LINE = re.compile(r"^\s*[VAS][.A-Z]{5}\s+(\S+)\s")


def probe_encoders(ffmpeg_path):
    """Run `ffmpeg -encoders` and return the set of encoder ids."""
    if not ffmpeg_path:
        return set()
    try:
        res = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=10, check=False,
            creationflags=_CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        _LOG.warning(f"FFmpeg encoders probe failed: {e}")
        return set()

    encoders = set()
    for line in (res.stdout or "").splitlines():
        m = _ENCODER_LINE.match(line)
        if m:
            encoders.add(m.group(1))
    return encoders


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------

def _video_args(props):
    codec = props.video_codec
    info = _codecs.VIDEO_CODECS.get(codec, {})
    args = ["-c:v", codec]

    rate_mode = props.rate_mode if _codecs.codec_supports_param(codec, "rate_mode") else ""

    if rate_mode == "CRF":
        args += ["-crf", str(props.crf)]
        if codec == "libvpx-vp9":
            # VP9 needs -b:v 0
            args += ["-b:v", "0"]
    elif rate_mode == "CBR":
        br = props.bitrate.strip() or info.get("default_bitrate", "5M")
        args += ["-b:v", br, "-maxrate", br, "-bufsize", br]
    elif rate_mode == "VBR":
        br = props.bitrate.strip() or info.get("default_bitrate", "5M")
        args += ["-b:v", br]

    if _codecs.codec_supports_param(codec, "preset") and props.preset and props.preset != "NONE":
        args += ["-preset", props.preset]

    if _codecs.codec_supports_param(codec, "pix_fmt") and props.pix_fmt:
        args += ["-pix_fmt", props.pix_fmt]

    if _codecs.codec_supports_param(codec, "profile") and props.profile and props.profile != "NONE":
        value = _codecs.resolve_profile_value(codec, props.profile)
        args += ["-profile:v", value]

    if codec == "ffv1":
        args += ["-level", "3", "-coder", "1", "-context", "1", "-g", "1"]

    return args


def _audio_args(props, audio_input_added):
    if not audio_input_added:
        return []
    codec = props.audio_codec
    # No valid audio codec for this container (e.g. GIF) — emit nothing
    if not codec or codec == "NONE":
        return []
    args = ["-c:a", codec]
    info = _codecs.AUDIO_CODECS.get(codec, {})
    if not info.get("lossless", False):
        br = props.audio_bitrate.strip() or info.get("default_bitrate", "192k")
        if br:
            args += ["-b:a", br]
    if props.audio_sample_rate:
        args += ["-ar", str(int(props.audio_sample_rate))]
    args += ["-shortest"]
    return args


def build_command(props, ffmpeg_path, frame_pattern, fps,
                  audio_path, output_path, frame_start=None, force_audio=False):
    """Build the full ffmpeg argv for the encode step.

    frame_pattern is a printf-style path like ``/tmp/render/####.png`` rendered by
    Blender, already converted to ``%04d`` form. When ``force_audio`` is True, the
    ``audio_path`` is included even if it does not point at a real file. This is
    used by the command preview to render audio flags without the mixdown WAV
    actually existing on disk.
    """
    cmd = [ffmpeg_path or "ffmpeg", "-y", "-hide_banner"]

    cmd += ["-framerate", str(fps)]
    if frame_start is not None:
        cmd += ["-start_number", str(int(frame_start))]
    cmd += ["-i", frame_pattern]

    audio_input_added = False
    if audio_path and (force_audio or os.path.isfile(audio_path)):
        # Skip audio input entirely for audio-less containers (GIF) so the
        # mux step won't refuse to embed audio stream.
        if _codecs.container_supports_audio(props.container):
            cmd += ["-i", audio_path]
            audio_input_added = True

    cmd += _video_args(props)
    cmd += _audio_args(props, audio_input_added)

    if props.custom_cli.strip():
        try:
            cmd += shlex.split(props.custom_cli, posix=(os.name != "nt"))
        except ValueError as e:
            _LOG.warning(f"Could not parse custom CLI args: {e}")

    cmd.append(output_path)
    return cmd


def command_to_pretty_string(cmd):
    """Return a human readable, copy-pasteable representation of an argv."""
    parts = []
    for token in cmd:
        if any(c in token for c in (" ", "\t", '"', "'")):
            parts.append('"' + token.replace('"', '\\"') + '"')
        else:
            parts.append(token)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Process wrapper
# ---------------------------------------------------------------------------

# FFmpeg writes progress lines in following way:
#   frame=  123 fps= 25 q=20.0 size=    1024kB time=00:00:05.04 bitrate=...
_PROGRESS_RE = re.compile(
    r"frame=\s*(?P<frame>\d+).*?"
    r"fps=\s*(?P<fps>[\d.]+).*?"
    r"time=\s*(?P<time>[\d:.]+)"
)


def parse_progress(line):
    """Return dict {frame, fps, time} parsed from an FFmpeg stderr line, or None."""
    m = _PROGRESS_RE.search(line)
    if not m:
        return None
    return {
        "frame": int(m.group("frame")),
        "fps": float(m.group("fps")),
        "time": m.group("time"),
    }


class FFmpegProcess:
    """Non-blocking wrapper around subprocess.Popen.

    The encoder operator polls poll_progress() on a Blender timer. The stderr
    is drained on a daemon thread so we never block the Blender main thread.
    """

    def __init__(self, cmd):
        self._cmd = cmd
        self._proc = None
        self._stderr_q = queue.Queue()
        self._reader = None
        self._last_line = ""

    def start(self):
        _LOG.info("Spawning FFmpeg: " + command_to_pretty_string(self._cmd))
        self._proc = subprocess.Popen(
            self._cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            creationflags=_CREATE_NO_WINDOW,
        )
        self._reader = threading.Thread(
            target=self._drain_stderr,
            args=(self._proc.stderr, self._stderr_q),
            daemon=True,
        )
        self._reader.start()

    @staticmethod
    def _drain_stderr(stream, q):
        # FFmpeg uses \r to update the same progress line, split on both \r\n
        buffer = ""
        try:
            while True:
                ch = stream.read(1)
                if ch == "":
                    break
                if ch in ("\n", "\r"):
                    if buffer:
                        q.put(buffer)
                        buffer = ""
                else:
                    buffer += ch
            if buffer:
                q.put(buffer)
        except Exception:
            pass
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def drain_lines(self):
        """Pull all currently buffered stderr lines."""
        out = []
        while True:
            try:
                out.append(self._stderr_q.get_nowait())
            except queue.Empty:
                break
        if out:
            self._last_line = out[-1]
        return out

    @property
    def last_line(self):
        return self._last_line

    def is_running(self):
        return self._proc is not None and self._proc.poll() is None

    @property
    def returncode(self):
        return None if self._proc is None else self._proc.returncode

    def cancel(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def wait(self, timeout=None):
        if self._proc:
            try:
                return self._proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                return None
        return None
