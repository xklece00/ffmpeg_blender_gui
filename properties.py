# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Scene PropertyGroup that holds all encoding parameters.
#               Saved in the .blend file so encode setup can travel with each project.
# ------------------------------------------------------------------------------
"""Scene encoding properties."""

import bpy

from .class_manager import ClassManager
from . import codecs as _codecs


# Enum callbacks must return the same Python list object as
# long as the enum value is referenced, otherwise the strings get garbage
# collected and Blender crashes.
_video_codec_cache = {}
_audio_codec_cache = {}
_preset_cache = {}
_pix_fmt_cache = {}
_profile_cache = {}
_rate_mode_cache = {}


def _get_available_encoders(context):
    """Return frozenset of encoder ids the users FFmpeg actually supports.

    Returns ``None`` when the cache hasnt been populated yet (user has not
    clicked Auto-Detect / Test in Add-on Preferences). In that case the codec
    dropdowns use full encoder list, avoiding empty UI on first install.
    """
    from .preferences import get_prefs
    prefs = get_prefs(context)
    if not prefs or not prefs.detected_encoders:
        return None
    encoders = frozenset(
        e.strip() for e in prefs.detected_encoders.split(",") if e.strip()
    )
    return encoders or None


def _container_items(self, context):
    return _codecs.container_enum_items()


def _video_codec_items(self, context):
    container = self.container or "MP4"
    encoders = _get_available_encoders(context)
    cache_key = (container, encoders)
    if cache_key not in _video_codec_cache:
        items = _codecs.video_codecs_for_container(container, available_encoders=encoders)
        if not items:
            if encoders is None:
                items = [("NONE", "(no codec)", "")]
            else:
                items = [("NONE", "(no encoder available - check FFmpeg build)", "")]
        _video_codec_cache[cache_key] = items
    return _video_codec_cache[cache_key]


def _audio_codec_items(self, context):
    container = self.container or "MP4"
    encoders = _get_available_encoders(context)
    cache_key = (container, encoders)
    if cache_key not in _audio_codec_cache:
        items = _codecs.audio_codecs_for_container(container, available_encoders=encoders)
        if not items:
            if encoders is None:
                items = [("NONE", "(no codec)", "")]
            else:
                items = [("NONE", "(no encoder available - check FFmpeg build)", "")]
        _audio_codec_cache[cache_key] = items
    return _audio_codec_cache[cache_key]


def _rate_mode_items(self, context):
    codec = self.video_codec or "libx264"
    if codec not in _rate_mode_cache:
        items = _codecs.rate_modes_for_codec(codec)
        if not items:
            items = [("NONE", "(fixed)", "")]
        _rate_mode_cache[codec] = items
    return _rate_mode_cache[codec]


def _preset_items(self, context):
    codec = self.video_codec or "libx264"
    if codec not in _preset_cache:
        items = _codecs.presets_for_codec(codec)
        if not items:
            items = [("NONE", "(none)", "")]
        _preset_cache[codec] = items
    return _preset_cache[codec]


def _pix_fmt_items(self, context):
    codec = self.video_codec or "libx264"
    if codec not in _pix_fmt_cache:
        items = _codecs.pix_fmts_for_codec(codec)
        if not items:
            items = [("yuv420p", "yuv420p", "")]
        _pix_fmt_cache[codec] = items
    return _pix_fmt_cache[codec]


def _profile_items(self, context):
    codec = self.video_codec or "libx264"
    if codec not in _profile_cache:
        items = _codecs.profiles_for_codec(codec)
        if not items:
            items = [("NONE", "(none)", "")]
        _profile_cache[codec] = items
    return _profile_cache[codec]


def _on_container_change(self, context):
    # When container changes we may need to re-pick codecs that no longer fit.
    # Filter by the encoders the user's FFmpeg can actually produce so that we
    # don't silently steer the user into a codec that will fail at encode time.
    encoders = _get_available_encoders(context)
    valid_video = {
        item[0]
        for item in _codecs.video_codecs_for_container(self.container, available_encoders=encoders)
    }
    if self.video_codec not in valid_video and valid_video:
        self.video_codec = next(iter(valid_video))

    valid_audio = {
        item[0]
        for item in _codecs.audio_codecs_for_container(self.container, available_encoders=encoders)
    }
    if self.audio_codec not in valid_audio and valid_audio:
        self.audio_codec = next(iter(valid_audio))


class MUL_FFmpegProps(bpy.types.PropertyGroup):
    """All encoding parameters for one scene."""

    container: bpy.props.EnumProperty(
        name="Container",
        description="Output container format",
        items=_container_items,
        update=_on_container_change,
    )

    output_filepath: bpy.props.StringProperty(
        name="Output File",
        description="Final video file. Leave empty to use the scene render path with the container extension",
        subtype='FILE_PATH',
        default="",
    )

    # ----- Video --------------------------------------------------------------

    video_codec: bpy.props.EnumProperty(
        name="Video Codec",
        description="Video encoder used by FFmpeg",
        items=_video_codec_items,
    )

    rate_mode: bpy.props.EnumProperty(
        name="Rate Mode",
        description="Bitrate strategy",
        items=_rate_mode_items,
    )

    crf: bpy.props.IntProperty(
        name="CRF",
        description="Constant Rate Factor. Lower means higher quality and bigger file",
        default=23,
        min=0,
        max=63,
        soft_min=0,
        soft_max=51,
    )

    bitrate: bpy.props.StringProperty(
        name="Bitrate",
        description="Target bitrate (e.g. 5M, 2500k)",
        default="5M",
    )

    preset: bpy.props.EnumProperty(
        name="Preset",
        description="Speed / efficiency tradeoff",
        items=_preset_items,
    )

    pix_fmt: bpy.props.EnumProperty(
        name="Pixel Format",
        description="Output pixel format (yuv420p is the safest choice for web playback)",
        items=_pix_fmt_items,
    )

    profile: bpy.props.EnumProperty(
        name="Profile",
        description="Codec profile",
        items=_profile_items,
    )

    two_pass: bpy.props.BoolProperty(
        name="Two-Pass",
        description="Encode in two passes for more accurate VBR quality (slower)",
        default=False,
    )

    # ----- Audio --------------------------------------------------------------

    audio_enabled: bpy.props.BoolProperty(
        name="Include Audio",
        description="Take all audio from the Sequencer and mux it into the output",
        default=True,
    )

    audio_codec: bpy.props.EnumProperty(
        name="Audio Codec",
        description="Audio encoder used by FFmpeg",
        items=_audio_codec_items,
    )

    audio_bitrate: bpy.props.StringProperty(
        name="Audio Bitrate",
        description="Target audio bitrate (ignored for lossless codecs)",
        default="192k",
    )

    audio_sample_rate: bpy.props.IntProperty(
        name="Sample Rate",
        description="Audio sample rate in Hz",
        default=48000,
        min=8000,
        max=192000,
    )

    # ----- Advanced -----------------------------------------------------------

    custom_cli: bpy.props.StringProperty(
        name="Custom Args",
        description="Extra arguments inserted before the output filename. Parsed with shlex",
        default="",
    )

    keep_intermediates: bpy.props.BoolProperty(
        name="Keep Intermediate Files",
        description="Do not delete the rendered PNG sequence after a successful encode",
        default=False,
    )

    open_after_encode: bpy.props.BoolProperty(
        name="Open After Encode",
        description="Open the encoded file in the system default player",
        default=False,
    )


ClassManager.add_class(MUL_FFmpegProps)
