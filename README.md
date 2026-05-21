# FFmpeg GUI – Blender Add-on

A UI wrapper around the FFmpeg command-line tool implemented as a  
Blender add-on. Lets you encode rendered animations into modern containers  
and codecs without leaving Blender or touching a terminal.

> Brno University of Technology
>
> Author: Tomáš Klecer, xklece00
>
> Supervisor: Ing. Tomáš Chlubna, Ph.D.
>
> Date: 1.5.2026

## License

Released under **GNU General Public License v3.0 or later**. This matches Blender's own GPL-3.0-or-later licensing and satisfies the Blender Extensions licensing requirements for add-ons. See the `LICENSE` file for the full text.

## Requirements

- **Blender 4.5.0 or newer**
- **FFmpeg 6.0 or newer** installed on the system. The add-on does *not*  
provide FFmpeg (you can download it from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html))
  - The add-on automaticaly detects FFmpeg in `PATH` on first run
  - You can also manually set path to specific binary in **Edit →**  
  **Preferences → Add-ons → FFmpeg GUI**

## Installation

1. Build the installable archive: `make zip` produces
  `FFmpeg_Blender_GUI.zip`.
2. In Blender open **Edit → Preferences → Get Extensions → Install from
  Disk…** and select the produced zip.
3. Open **Edit → Preferences → Add-ons**, find *FFmpeg GUI* and enable it.
4. Optional: in the add-on preferences click **Auto-Detect (PATH)** or
  browse to your `ffmpeg` binary, then **Test** to verify.

## Where to find add-on


| Place                                              | What it does                                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Properties → Output Properties → FFmpeg Encode** | Main encoding panel: container, video codec, audio codec, advanced args, command preview, action buttons. |
| **Edit → Preferences → Add-ons → FFmpeg GUI**      | FFmpeg binary path and probe results.                                                                     |
| **Topbar → Render menu**                           | Quick *Render & Encode with FFmpeg*, *Encode Existing Sequence* and *FFmpeg Encode Settings* shortcuts.   |


## Usage

1. Set up your scene resolution, FPS and frame range as usual.
2. In the **FFmpeg Encode** panel pick a container, video codec and any
  parameters (CRF, preset, pixel format, profile).
3. Optionally enable **Audio** if you want the Sequencer audio mixed in.
4. Optionally fill **Advanced → Custom FFmpeg Args** with extra flags
  (parsed with `shlex`).
5. Click **Render & Encode**. Blender renders the animation into a
  temporary PNG sequence; FFmpeg then encodes it. Press **Esc** to cancel
   the encoding step.

To re-encode an existing image sequence, use **Encode Existing**  
**Sequence…** and pick the first frame. The add-on derives the  
pattern automatically. If a sibling `audio.wav` is found next to
the sequence (or one directory above, matching the layout produced by
*Render & Encode* with *Keep Intermediates*), it is muxed into the
output as well.

## Supported codecs

The add-on has the following codec/container combinations  
exposed in the UI (others can be passed via custom arguments):


| Codec              | Container(s)       |
| ------------------ | ------------------ |
| H.264 (libx264)    | MP4, MKV, MOV      |
| H.265 (libx265)    | MP4, MKV           |
| VP9 (libvpx-vp9)   | WebM, MKV          |
| AV1 (libsvtav1)    | MP4, MKV, WebM     |
| ProRes (prores_ks) | MOV, MKV           |
| FFV1 (lossless)    | MKV, AVI           |
| DNxHR/DNxHD (Avid) | MOV, MKV           |
| MPEG-4 Part 2      | MP4, AVI, MKV      |
| Motion JPEG        | MP4, MKV, MOV, AVI |
| GIF (animation)    | GIF                |


Audio: AAC, Opus, MP3, AC-3, FLAC, ALAC, PCM-16.

The dropdowns are **filtered dynamically** based on which encoders your
FFmpeg binary actually exposes (`ffmpeg -encoders`). Click *Test* in the
add-on preferences to populate that filter; until then the full static
list is shown with a hint in the panel.

Anything not in the table can still be reached three ways:

- **Custom (Custom Args only)** is the last entry in both the Video
Codec and Audio Codec dropdowns. Pick it and the add-on will skip
emitting any codec parameters, leaving you free to write the entire
codec specification (`-c:v`, `-crf`, filters, hardware encoder flags…)
in *Advanced > Custom FFmpeg Args* without colliding with the addon's
defaults. Per-stream granularity is supported, e.g. *Custom* video
with standard AAC audio. The Command Preview shows a hint when a
codec is set to *Custom* but no matching `-c:v` / `-c:a` is present
in Custom Args.
- **Custom Args** in the *Advanced* sub-panel - any additional flag
(filters, color metadata, hardware encoders, …) is appended to the
generated command and parsed safely with `shlex`. FFmpeg honours the
last value of duplicated flags, so `-c:v h264_nvenc` typed there will
override the codec picked in the dropdown.
- **Editing `codecs.py`** - adding a dictionary entry to `VIDEO_CODECS`
or `AUDIO_CODECS` makes a new codec appear in the UI without any
other code changes (the rest of the add-on reads the table
dynamically).

## Project layout

```
FFmpeg_Blender_GUI/
├── blender_manifest.toml   # Blender 4.2+ extension manifest
├── __init__.py             # bl_info + register / unregister
├── class_manager.py        # central class registry helper
├── log_service.py          # thin logging wrapper
├── codecs.py               # codec / container tables + filters
├── properties.py           # per-scene PropertyGroup
├── ffmpeg_runner.py        # discovery, command builder, FFmpegProcess
├── preferences.py          # AddonPreferences (path, probe cache)
├── operators/              # all UI-triggered actions
│   ├── op_detect_ffmpeg.py
│   ├── op_test_ffmpeg.py
│   ├── op_render_and_encode.py
│   ├── op_encode_existing.py
│   ├── op_copy_command.py
│   └── op_show_settings.py
├── ui/                     # panels + topbar menu
│   ├── panel_main.py
│   ├── panel_video.py
│   ├── panel_audio.py
│   ├── panel_advanced.py
│   ├── panel_preview.py
│   └── topbar_menu.py
├── Makefile                # `make zip` / `make clean` / `make install`
├── build_zip.py            # cross-platform packaging helper
├── README.md               # this file
└── LICENSE                 # GPL-3.0-or-later full text
```

## Assignment

This add-on is school project for the **MUL – Multimedia** course
(academic year 2025/2026, supervisor Ing. Tomáš Chlubna, Ph.D.) at the
Faculty of Information Technology, Brno University of Technology.

Original assignment (translated from Czech):

> *Create a graphical interface for the FFmpeg command-line tool.
> Implement this interface as an add-on for the Blender multimedia
> editor. The interface should include selection of:*
>
> - *output container,*
> - *output codecs and their parameters such as data rate, quality
> parameter, pixel format, etc.*
>
> *Other parameters such as frame rate and resolution are taken from the
> rendering settings in Blender. The implemented codecs and parameters
> should correspond to commonly used modern video formats, and the
> interface should allow inserting custom command-line parameters and a
> custom path to the FFmpeg installation. The aim of the assignment is
> to create a usable tool that will be publicly available to the
> community.*

## Solution description

### Architecture overview

The add-on is split into following layers:

- **Data model** (`codecs.py`, `properties.py`): a single static table  
defines every container, codec and per-codec parameter range. The  
`bpy.types.PropertyGroup` attached to `bpy.types.Scene` stores the
user's choices so they travel inside the `.blend` file.
- **FFmpeg integration** (`ffmpeg_runner.py`): binary discovery (`find_ffmpeg`),
capability probing (`probe_version`, `probe_encoders`), the
`build_command` translator that turns a `PropertyGroup` into a list
of `argv` tokens, and `FFmpegProcess`, a thin wrapper around
`subprocess.Popen` with non blocking stderr reading.
- **Operators** (`operators/`): every interactive action is a  
`bpy.types.Operator`: detect/test FFmpeg, run render+encode, encode
an existing sequence, copy the generated command, jump to settings.
- **UI** (`ui/`): the main panel in *Properties -> Output* with  
four collapsible subpanels (Video, Audio, Advanced, Command Preview)  
and three quick shortcuts in the *Topbar -> Render* menu.
- Helpers (`class_manager.py`, `log_service.py`): handle  
class registration and structured logging.

### Design features

**Two-phase pipeline:** Render and encode are separated.  
*Render & Encode* first triggers `bpy.ops.render.render(animation=True)`  
into a temporary directory created with `tempfile.mkdtemp()`, then  
optionally calls `bpy.ops.sound.mixdown(...)` to extract the  
Sequencer audio strips into a PCM `audio.wav`, and finally spawns  
FFmpeg with both files as `-i` inputs. Therefore the PNG sequence
can be re-encoded with different parameters without rendering again
(via *Encode Existing Sequence*), and potential crash during the encode does not corrupt the rendered frames

**Non-blocking encode:** Blender UI runs on a single thread, and
`subprocess.run` would freeze it for the duration of the encode. The
encode operator therefore implements the *modal operator* pattern:

- `subprocess.Popen` launches FFmpeg with `stderr=subprocess.PIPE`.
- A daemon `threading.Thread` drains FFmpeg stderr intoa `queue.Queue`,
because Blender API calls are not thread-safe and must stay
on the main thread.
- A `bpy.app.timers.event_timer_add(0.25, ...)` callback fires on
Blender main loop, dequeues stderr lines that arrived in the
last moments, parses progress with a regex and updates the
workspace status bar.
- Pressing *Esc* triggers `proc.terminate()` and cleans up the
temporary directory.

**Command builder:** `build_command` is a function that takes the
`PropertyGroup`, the FFmpeg binary path, frame pattern, fps, optional
audio path and output path, and returns a `list[str]` of arguments.
The generated command can be previewed in the *Command Preview* subpanel
before any subprocess is spawned. Custom user arguments are parsed with
`shlex.split(..., posix=(os.name != "nt"))` to handle quotes and
escapes.

**Codec table:** `codecs.py` lists every container, video codec and
audio codec with their valid container intersection,
supported rate modes, parameter ranges, defaults and human-readable label.
The UI dropdowns, parameter visibility, command builder
and runtime validation all read from the same dictionary,
so adding a codec is as simnple as possible.

**Dynamic encoder filtering:** When the user clicks *Test* in the
add-on preferences, `ffmpeg -encoders` is parsed with a regex
(`_ENCODER_LINE`) and the resulting set of encoder ids is cached in
`AddonPreferences.detected_encoders`. The codec dropdowns are then filtered
through `codec_supports_encoder(...)` so the user only sees
options their FFmpeg build can actually produce.

**Frame pattern derivation:** Blender writes PNGs as
`frame_0001.png`, `frame_0002.png`, …; FFmpeg image-sequence input
expects a printf-style pattern `frame_%04d.png`. The helper
`_derive_frame_pattern` extracts the trailing digit block with the
regex `(\d+)(?=[^\d]*$)`, counts its width and substitutes the
appropriate `%0Nd` placeholder. The same regex powers
`_split_pattern_and_start` in *Encode Existing Sequence*, which
additionally returns the first frame number for FFmpeg `-start_number`.

**Output path safety:** `ensure_container_ext` appends the container
extension when the user typed output path lacks one but respects
any extension the user explicitly typed.

**Audio search in *Encode Existing Sequence*:** The helper
`_find_sibling_audio` looks for `audio.wav`, `audio.flac` or
`audio.mp3` next to the picked frame and one directory above. The
one above lookup matches the layout produced by *Render & Encode*
with *Keep Intermediates*, allowing audio from previous render to be
reused automaticaly.

## Results evaluation

### Functional outcome

This add-on only implements the basic requirements from the assignment.
Functionalities of add-on were tested on Windows 11 using Blender 4.5.3
LTS and FFmpeg 2026-04-26 and produced videos were played using
VLC Media Player.

### Comparison with Blender built in FFmpeg export

Blender already uses a *FFmpeg Video* output format under
*Output Properties → Output → File Format*. The add-on brings
improvemetns in following areas:

- **Own codecs:** Blenders bundled libavcodec lags ffmpeg.org
releases by months. The add-on uses the system FFmpeg,
so anything in `ffmpeg -encoders` is reachable.
- **Explicit parameter control:** Blender allows user to set vague
 *Output Quality* presets (Lowest…Lossless) that map to internal CRF values
the user cannot see. The add-on lets the user type CRF, bitrate,
preset, profile and pixel format directly.
- **Two phase pipeline:** Blender encodes during render, so changing a
codec parameter requires re-rendering. The add-on encodes from a
separately rendered PNG sequence, allowing easier iteration.
- **Custom args:** Blender offers no way to pass
`-vf scale=...`, `-tune film`, color metadata or a hardware encoder.
The add-on accepts arbitrary arguments.
- **Encode Existing Sequence:** Image sequences from older render or
another platform can be turned into a video using this operator.

### Limitations

- Hardware encoders (NVENC, QSV, VideoToolbox, AMF) are not in the UI.
They are only reachable through *Custom Args*. A clean integration would  
require codec specific parameter mapping (e.g. `-cq` instead of `-crf`  
etc.).
- The add-on encodes from image sequences only. Transcoding of
an existing video file is not implemented.
- The *Encode Existing Sequence* operator picks up audio only by
filename convention (`audio.wav` next to or above the sequence).

## AI ussage

I used Claude Opus 4.7 via Cursor IDE to help with following:

- Advise on specific bpy and ffmpeg syntax.
- Code reviewing and debugging errors.
- Routine tasks as listing codecs, creatin `__init__.py` files etc.
- Creating `blender_manifest.toml`.
- Creating deploy helpers `Makefile` and `build_zip.py`.
- Adding safety asserts (when some service is not available)

## Sources

[1] BLENDER FOUNDATION. Blender Python API Documentation [online].
    Verze 4.5. Amsterdam: Blender Foundation, 2025
    [cit. 2026-05-03]. Available from:
    [https://docs.blender.org/api/current/index.html](https://docs.blender.org/api/current/index.html)

[2] BLENDER FOUNDATION. Add-on Tutorial. In: Blender Manual
    [online]. Verze 4.5. Amsterdam: Blender Foundation, 2025
    [cit. 2026-05-03]. Available from:
    [https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)

[3] FFMPEG DEVELOPERS. ffmpeg Documentation [online].
    [s.l.]: FFmpeg, 2026 [cit. 2026-05-03]. Available from:
    [https://ffmpeg.org/ffmpeg.html](https://ffmpeg.org/ffmpeg.html)