# ------------------------------------------------------------------------------
# MUL Project: FFmpeg GUI Blender Add-on
# Author:       Tomáš Klecer
# Date:         26.4.2026
# University:   Brno University of Technology
# Supervisor:   Ing. Tomáš Chlubna, Ph.D.
# Description:  Lists supported containers, video and
#               audio codecs together with the parameter ranges and defaults
#               used by both UI and the FFmpeg command builder.
# Note:         Codecs and containers listed by Claude Opus 4.7
# ------------------------------------------------------------------------------
"""Codec and container definitions."""

import os


# Sentinel value used in both video and audio codec dropdowns. Selecting it
# tells _video_args / _audio_args to skip emitting any codec parameters at
# all, leaving the user free to write the entire codec specification in the
# Advanced -> Custom FFmpeg Args field. Useful for hardware encoders
# (NVENC, QSV, VideoToolbox) and unstandard parameter combinations that the addon
# table does not cover.
CUSTOM_CODEC_ID = "CUSTOM"
CUSTOM_CODEC_LABEL = "Custom (Custom Args only)"
CUSTOM_CODEC_DESC = ("Skip all codec parameters; write -c:v / -c:a and "
                     "any other flags yourself in Advanced > Custom FFmpeg Args")


CONTAINERS = {
    "MP4":  {"label": "MP4",                "ext": "mp4",  "muxer": "mp4"},
    "MKV":  {"label": "Matroska (MKV)",     "ext": "mkv",  "muxer": "matroska"},
    "WEBM": {"label": "WebM",               "ext": "webm", "muxer": "webm"},
    "MOV":  {"label": "QuickTime (MOV)",    "ext": "mov",  "muxer": "mov"},
    "AVI":  {"label": "AVI",                "ext": "avi",  "muxer": "avi"},
    "GIF":  {"label": "GIF (animation)",    "ext": "gif",  "muxer": "gif"},
}


VIDEO_CODECS = {
    "libx264": {
        "label": "H.264 (libx264)",
        "containers": {"MP4", "MKV", "MOV"},
        "rate_modes": ["CRF", "CBR", "VBR"],
        "default_rate_mode": "CRF",
        "crf_range": (0, 51),
        "default_crf": 23,
        "default_bitrate": "5M",
        "presets": ["ultrafast", "superfast", "veryfast", "faster", "fast",
                    "medium", "slow", "slower", "veryslow"],
        "default_preset": "medium",
        "pix_fmts": ["yuv420p", "yuv422p", "yuv444p"],
        "default_pix_fmt": "yuv420p",
        "profiles": ["baseline", "main", "high"],
        "default_profile": "high",
        "supports_two_pass": True,
    },
    "libx265": {
        "label": "H.265 / HEVC (libx265)",
        "containers": {"MP4", "MKV"},
        "rate_modes": ["CRF", "CBR", "VBR"],
        "default_rate_mode": "CRF",
        "crf_range": (0, 51),
        "default_crf": 28,
        "default_bitrate": "5M",
        "presets": ["ultrafast", "superfast", "veryfast", "faster", "fast",
                    "medium", "slow", "slower", "veryslow"],
        "default_preset": "medium",
        "pix_fmts": ["yuv420p", "yuv420p10le", "yuv422p10le", "yuv444p10le"],
        "default_pix_fmt": "yuv420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": True,
    },
    "libvpx-vp9": {
        "label": "VP9 (libvpx-vp9)",
        "containers": {"WEBM", "MKV"},
        "rate_modes": ["CRF", "CBR", "VBR"],
        "default_rate_mode": "CRF",
        "crf_range": (0, 63),
        "default_crf": 31,
        "default_bitrate": "2M",
        "presets": [],
        "default_preset": "",
        "pix_fmts": ["yuv420p", "yuv422p", "yuv444p"],
        "default_pix_fmt": "yuv420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": True,
    },
    "libsvtav1": {
        "label": "AV1 (libsvtav1)",
        "containers": {"MP4", "MKV", "WEBM"},
        "rate_modes": ["CRF", "CBR"],
        "default_rate_mode": "CRF",
        "crf_range": (0, 63),
        "default_crf": 35,
        "default_bitrate": "2M",
        "presets": ["0", "2", "4", "6", "8", "10", "12"],
        "default_preset": "8",
        "pix_fmts": ["yuv420p", "yuv420p10le"],
        "default_pix_fmt": "yuv420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": False,
    },
    "prores_ks": {
        "label": "ProRes (prores_ks)",
        "containers": {"MOV", "MKV"},
        "rate_modes": [],
        "default_rate_mode": "",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "",
        "presets": [],
        "default_preset": "",
        "pix_fmts": ["yuv422p10le", "yuv444p10le"],
        "default_pix_fmt": "yuv422p10le",
        "profiles": ["proxy", "lt", "standard", "hq", "4444", "4444xq"],
        "profile_map": {"proxy": "0", "lt": "1", "standard": "2",
                        "hq": "3", "4444": "4", "4444xq": "5"},
        "default_profile": "standard",
        "supports_two_pass": False,
    },
    "ffv1": {
        "label": "FFV1 (lossless)",
        "containers": {"MKV", "AVI"},
        "rate_modes": [],
        "default_rate_mode": "",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "",
        "presets": [],
        "default_preset": "",
        "pix_fmts": ["yuv420p", "yuv422p", "yuv444p", "yuv422p10le"],
        "default_pix_fmt": "yuv420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": False,
    },
    "mpeg4": {
        "label": "MPEG-4 Part 2",
        "containers": {"MP4", "AVI", "MKV"},
        "rate_modes": ["CBR", "VBR"],
        "default_rate_mode": "CBR",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "5M",
        "presets": [],
        "default_preset": "",
        "pix_fmts": ["yuv420p"],
        "default_pix_fmt": "yuv420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": False,
    },
    "mjpeg": {
        "label": "Motion JPEG",
        "containers": {"MP4", "MKV", "MOV", "AVI"},
        "rate_modes": ["CBR"],
        "default_rate_mode": "CBR",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "20M",
        "presets": [],
        "default_preset": "",
        # MJPEG historically uses the JPEG full-range yuvj* family; modern
        # FFmpeg accepts plain yuv420p too and auto-tags color range.
        "pix_fmts": ["yuvj420p", "yuvj422p", "yuv420p"],
        "default_pix_fmt": "yuvj420p",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": False,
    },
    "dnxhd": {
        "label": "DNxHR/DNxHD (Avid)",
        "containers": {"MOV", "MKV"},
        # DNxHR bitrate is derived from the chosen profile, so no rate mode
        # picker - the user just picks a quality tier in Profile.
        "rate_modes": [],
        "default_rate_mode": "",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "",
        "presets": [],
        "default_preset": "",
        # LB/SQ/HQ use yuv422p; HQX/444 require yuv422p10le / yuv444p10le.
        "pix_fmts": ["yuv422p", "yuv422p10le", "yuv444p10le"],
        "default_pix_fmt": "yuv422p",
        "profiles": ["dnxhr_lb", "dnxhr_sq", "dnxhr_hq", "dnxhr_hqx", "dnxhr_444"],
        "default_profile": "dnxhr_hq",
        "supports_two_pass": False,
    },
    "gif": {
        "label": "GIF (animation)",
        "containers": {"GIF"},
        "rate_modes": [],
        "default_rate_mode": "",
        "crf_range": (0, 0),
        "default_crf": 0,
        "default_bitrate": "",
        "presets": [],
        "default_preset": "",
        # 8-bit palette is the only format the GIF muxer understands.
        # FFmpeg auto-converts yuv frames into pal8 internally.
        "pix_fmts": ["pal8"],
        "default_pix_fmt": "pal8",
        "profiles": [],
        "default_profile": "",
        "supports_two_pass": False,
    },
}


AUDIO_CODECS = {
    "aac":         {"label": "AAC",                 "containers": {"MP4", "MKV", "MOV"},        "default_bitrate": "192k", "lossless": False},
    "libopus":     {"label": "Opus",                "containers": {"MKV", "WEBM"},              "default_bitrate": "128k", "lossless": False},
    "libmp3lame":  {"label": "MP3 (LAME)",          "containers": {"MP4", "MKV", "AVI"},        "default_bitrate": "192k", "lossless": False},
    "ac3":         {"label": "AC-3",                "containers": {"MP4", "MKV", "MOV", "AVI"}, "default_bitrate": "384k", "lossless": False},
    "flac":        {"label": "FLAC (lossless)",     "containers": {"MKV", "MOV"},               "default_bitrate": "",     "lossless": True},
    "alac":        {"label": "ALAC (Apple lossless)", "containers": {"MOV", "MKV"},             "default_bitrate": "",     "lossless": True},
    "pcm_s16le":   {"label": "PCM 16-bit",          "containers": {"MOV", "AVI", "MKV"},        "default_bitrate": "",     "lossless": True},
}


def container_enum_items():
    return [(key, info["label"], info["label"]) for key, info in CONTAINERS.items()]


def get_container_ext(container_key):
    info = CONTAINERS.get(container_key)
    return info["ext"] if info else "mp4"


def ensure_container_ext(path, container_key):
    """Append the container extension when the path is missing one.

    Respects an existing extension written by user (user may legitimately
    want ``.m4v`` instead of ``.mp4`` etc.) but if only a bare filename is
    is given (which would make muxer detection fail), the container extension is appended.
    """
    if not path:
        return path
    _, ext = os.path.splitext(path)
    if ext:
        return path
    return path + "." + get_container_ext(container_key)


def video_codecs_for_container(container_key, available_encoders=None):
    """Return video codecs valid in the given container for UI filtering.

    The ``CUSTOM`` sentinel is appended as the last option.

    When ``available_encoders`` is provided (a set of encoder ids
    that the user's FFmpeg actually supports), codecs not present in the set
    are skipped. ``None`` disables the filter and returns all known codecs
    (used as a fall-back when the encoder cache has not been populated yet).
    """
    out = []
    for codec_id, info in VIDEO_CODECS.items():
        if container_key not in info["containers"]:
            continue
        if available_encoders is not None and codec_id not in available_encoders:
            continue
        out.append((codec_id, info["label"], info["label"]))
    out.append((CUSTOM_CODEC_ID, CUSTOM_CODEC_LABEL, CUSTOM_CODEC_DESC))
    return out


def audio_codecs_for_container(container_key, available_encoders=None):
    """Like ``video_codecs_for_container`` but for audio codecs.

    The ``CUSTOM`` sentinel is appended last (but only for containers that
    actually support audio)
    """
    if not container_supports_audio(container_key):
        return []
    out = []
    for codec_id, info in AUDIO_CODECS.items():
        if container_key not in info["containers"]:
            continue
        if available_encoders is not None and codec_id not in available_encoders:
            continue
        out.append((codec_id, info["label"], info["label"]))
    out.append((CUSTOM_CODEC_ID, CUSTOM_CODEC_LABEL, CUSTOM_CODEC_DESC))
    return out


def container_supports_audio(container_key):
    """Returns True if at least one audio codec in the table maps to this container.

    Used by the encode pipeline to skip audio mixdown / FFmpeg ``-i`` for
    audio-less containers like GIF, where adding an audio stream would make
    the mux fail outright.
    """
    return any(container_key in info["containers"] for info in AUDIO_CODECS.values())


def presets_for_codec(codec_id):
    info = VIDEO_CODECS.get(codec_id)
    if not info or not info["presets"]:
        return []
    return [(p, p, p) for p in info["presets"]]


def pix_fmts_for_codec(codec_id):
    info = VIDEO_CODECS.get(codec_id)
    if not info or not info["pix_fmts"]:
        return []
    return [(p, p, p) for p in info["pix_fmts"]]


def profiles_for_codec(codec_id):
    info = VIDEO_CODECS.get(codec_id)
    if not info or not info["profiles"]:
        return []
    return [(p, p, p) for p in info["profiles"]]


def rate_modes_for_codec(codec_id):
    info = VIDEO_CODECS.get(codec_id)
    if not info or not info["rate_modes"]:
        return []
    labels = {"CRF": "Constant Quality (CRF)", "CBR": "Constant Bitrate", "VBR": "Variable Bitrate"}
    return [(m, labels.get(m, m), m) for m in info["rate_modes"]]


def codec_supports_param(codec_id, param):
    """Return True if a codec exposes the given UI parameter."""
    info = VIDEO_CODECS.get(codec_id)
    if not info:
        return False
    if param == "crf":
        return "CRF" in info["rate_modes"]
    if param == "bitrate":
        return "CBR" in info["rate_modes"] or "VBR" in info["rate_modes"]
    if param == "rate_mode":
        return bool(info["rate_modes"])
    if param == "preset":
        return bool(info["presets"])
    if param == "pix_fmt":
        return bool(info["pix_fmts"])
    if param == "profile":
        return bool(info["profiles"])
    if param == "two_pass":
        return info.get("supports_two_pass", False)
    return False


def resolve_profile_value(codec_id, profile_label):
    """Some codecs (ProRes) need numeric profile id, some take the label as it is."""
    info = VIDEO_CODECS.get(codec_id)
    if not info:
        return profile_label
    return info.get("profile_map", {}).get(profile_label, profile_label)
